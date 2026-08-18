#!/usr/bin/env python3
"""Candidate-owned matched concurrent request harness for stock faster-whisper."""
import argparse
import hashlib
import json
import statistics
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

import pynvml
from faster_whisper import WhisperModel


REVISION = "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
DECODE = {
    "language": "en", "task": "transcribe", "beam_size": 5, "best_of": 5,
    "patience": 1.0, "length_penalty": 1.0, "temperature": 0.0,
    "condition_on_previous_text": False, "without_timestamps": True,
    "word_timestamps": False, "vad_filter": False, "initial_prompt": None,
    "prefix": None, "hotwords": None, "suppress_blank": True,
    "suppress_tokens": [-1], "repetition_penalty": 1.0, "no_repeat_ngram_size": 0,
}


class MemorySampler:
    def __init__(self):
        pynvml.nvmlInit()
        self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        self.samples = []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self):
        while not self.stop.is_set():
            self.samples.append({
                "monotonic": time.monotonic(),
                "used_bytes": pynvml.nvmlDeviceGetMemoryInfo(self.handle).used,
            })
            self.stop.wait(0.02)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set(); self.thread.join()


def percentile(values, p):
    values = sorted(values); pos = (len(values) - 1) * p
    lo = int(pos); hi = min(lo + 1, len(values) - 1); frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--data-root", required=True)
    ap.add_argument("--download-root", required=True); ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--concurrency", type=int, required=True); ap.add_argument("--run-id", required=True)
    ap.add_argument("--compute-type", choices=["float16", "int8_float16"], default="int8_float16")
    ap.add_argument("--split", choices=["development", "full"], default="development")
    ap.add_argument("--output", required=True); args = ap.parse_args()
    if args.workers < 1 or args.concurrency < 1: ap.error("workers/concurrency must be positive")

    manifest_path = Path(args.manifest); manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes); data_root = Path(args.data_root)
    load_start = time.monotonic()
    model = WhisperModel("turbo", device="cuda", device_index=0, compute_type=args.compute_type,
                         num_workers=args.workers, download_root=args.download_root, revision=REVISION)
    load_seconds = time.monotonic() - load_start

    def infer(item, submitted):
        started = time.monotonic(); failure = None; text = ""; count = 0
        try:
            segments, _ = model.transcribe(str(data_root / item["relative_path"]), **DECODE)
            materialized = list(segments); text = "".join(s.text for s in materialized).strip(); count = len(materialized)
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
        ended = time.monotonic()
        return {"utterance_id": item["utterance_id"], "duration_seconds": item["duration_seconds"],
                "queue_delay_seconds": started - submitted, "service_seconds": ended - started,
                "elapsed_seconds": ended - submitted, "hypothesis": text, "segment_count": count,
                "failure": failure}

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        warm = list(pool.map(lambda item: infer(item, time.monotonic()), manifest["warmup"]))
    if any(x["failure"] for x in warm): raise RuntimeError(f"warmup failure: {warm}")

    items = manifest[args.split]; start_utc = datetime.now(timezone.utc).isoformat()
    run_start = time.monotonic()
    with MemorySampler() as memory, ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        rows_by_index = [None] * len(items)
        futures = {}
        next_index = 0

        def submit_one(index):
            submitted = time.monotonic()
            futures[pool.submit(infer, items[index], submitted)] = index

        while next_index < min(args.concurrency, len(items)):
            submit_one(next_index); next_index += 1
        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                index = futures.pop(future)
                rows_by_index[index] = future.result()
                if next_index < len(items):
                    submit_one(next_index); next_index += 1
        rows = list(rows_by_index)
    wall = time.monotonic() - run_start; end_utc = datetime.now(timezone.utc).isoformat()
    audio = sum(x["duration_seconds"] for x in items); latencies = [x["elapsed_seconds"] for x in rows]
    canonical = "".join(f'{x["utterance_id"]}\t{x["hypothesis"]}\n' for x in rows)
    out = {"schema": 2, "run_id": args.run_id, "variant": "concurrent_stock_transcribe",
           "harness_mode": "bounded_closed_loop",
           "workers": args.workers, "concurrency": args.concurrency, "split": args.split,
           "start_utc": start_utc, "end_utc": end_utc, "logical_model_name": "turbo",
           "official_alias_repo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
           "model_revision": REVISION, "compute_type": args.compute_type, "decode": DECODE,
           "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
           "startup_model_load_seconds": load_seconds, "warmup": warm, "utterance_count": len(rows),
           "failure_count": sum(bool(x["failure"]) for x in rows), "total_audio_seconds": audio,
           "run_wall_seconds": wall, "audio_seconds_per_wall_second": audio / wall,
           "real_time_factor": wall / audio, "utterances_per_second": len(rows) / wall,
           "latency_p50_seconds": statistics.median(latencies), "latency_p95_seconds": percentile(latencies, .95),
           "service_p50_seconds": statistics.median([x["service_seconds"] for x in rows]),
           "queue_p95_seconds": percentile([x["queue_delay_seconds"] for x in rows], .95),
           "gpu_peak_used_bytes": max(x["used_bytes"] for x in memory.samples),
           "gpu_memory_samples": memory.samples, "raw_output_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
           "utterances": rows}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("run_id","workers","concurrency","failure_count","run_wall_seconds",
          "audio_seconds_per_wall_second","latency_p50_seconds","latency_p95_seconds","queue_p95_seconds",
          "gpu_peak_used_bytes","raw_output_sha256")}, indent=2))


if __name__ == "__main__": main()
