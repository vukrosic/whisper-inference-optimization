#!/usr/bin/env python3
"""Run stock serial or stock batched faster-whisper on a frozen manifest."""
import argparse
import hashlib
import json
import statistics
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pynvml
from faster_whisper import BatchedInferencePipeline, WhisperModel


REVISION = "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
DECODE = {
    "language": "en",
    "task": "transcribe",
    "beam_size": 5,
    "best_of": 5,
    "patience": 1.0,
    "length_penalty": 1.0,
    "temperature": 0.0,
    "condition_on_previous_text": False,
    "without_timestamps": True,
    "word_timestamps": False,
    "vad_filter": False,
    "initial_prompt": None,
    "prefix": None,
    "hotwords": None,
    "suppress_blank": True,
    "suppress_tokens": [-1],
    "repetition_penalty": 1.0,
    "no_repeat_ngram_size": 0,
}


class MemorySampler:
    def __init__(self) -> None:
        pynvml.nvmlInit()
        self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        self.samples: list[dict] = []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            self.samples.append({"monotonic": time.monotonic(), "used_bytes": info.used})
            self.stop_event.wait(0.02)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop_event.set()
        self.thread.join()


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def decode_one(engine, item: dict, variant: str, batch_size: int | None, data_root: Path) -> dict:
    path = data_root / item["relative_path"]
    start = time.monotonic()
    failure = None
    text = ""
    segment_count = 0
    try:
        if variant == "serial":
            segments, _ = engine.transcribe(str(path), **DECODE)
        else:
            # Explicit full-audio clip timestamps disable VAD and handle rare >=30 s files.
            segments, _ = engine.transcribe(
                str(path), batch_size=batch_size,
                clip_timestamps=[{"start": 0.0, "end": item["duration_seconds"]}],
                **DECODE,
            )
        materialized = list(segments)
        text = "".join(segment.text for segment in materialized).strip()
        segment_count = len(materialized)
    except Exception as exc:  # preserved in the result and rejected by the quality gate
        failure = f"{type(exc).__name__}: {exc}"
    elapsed = time.monotonic() - start
    return {
        "utterance_id": item["utterance_id"],
        "duration_seconds": item["duration_seconds"],
        "elapsed_seconds": elapsed,
        "hypothesis": text,
        "segment_count": segment_count,
        "failure": failure,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--download-root", required=True)
    parser.add_argument("--split", choices=["development", "full"], default="development")
    parser.add_argument("--variant", choices=["serial", "batched"], required=True)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.variant == "batched" and args.batch_size not in {4, 8, 16}:
        parser.error("batched requires --batch-size 4, 8, or 16")

    manifest_path = Path(args.manifest)
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    data_root = Path(args.data_root)

    load_start = time.monotonic()
    model = WhisperModel(
        "turbo", device="cuda", device_index=0, compute_type="float16",
        num_workers=1, download_root=args.download_root, revision=REVISION,
    )
    model_load_seconds = time.monotonic() - load_start
    engine = model if args.variant == "serial" else BatchedInferencePipeline(model)

    warmup_rows = [decode_one(engine, item, args.variant, args.batch_size, data_root) for item in manifest["warmup"]]
    if any(row["failure"] for row in warmup_rows):
        raise RuntimeError(f"warmup failure: {warmup_rows}")

    items = manifest[args.split]
    start_utc = datetime.now(timezone.utc).isoformat()
    run_start = time.monotonic()
    with MemorySampler() as memory:
        rows = [decode_one(engine, item, args.variant, args.batch_size, data_root) for item in items]
    run_wall = time.monotonic() - run_start
    end_utc = datetime.now(timezone.utc).isoformat()
    audio_seconds = sum(item["duration_seconds"] for item in items)
    latencies = [row["elapsed_seconds"] for row in rows]
    output_canonical = "".join(f'{row["utterance_id"]}\t{row["hypothesis"]}\n' for row in rows)
    receipt = {
        "schema": 1,
        "run_id": args.run_id,
        "variant": args.variant,
        "batch_size": args.batch_size,
        "split": args.split,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "logical_model_name": "turbo",
        "official_alias_repo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
        "model_revision": REVISION,
        "compute_type": "float16",
        "decode": DECODE,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "startup_model_load_seconds": model_load_seconds,
        "warmup": warmup_rows,
        "utterance_count": len(rows),
        "failure_count": sum(bool(row["failure"]) for row in rows),
        "total_audio_seconds": audio_seconds,
        "run_wall_seconds": run_wall,
        "audio_seconds_per_wall_second": audio_seconds / run_wall,
        "real_time_factor": run_wall / audio_seconds,
        "utterances_per_second": len(rows) / run_wall,
        "latency_p50_seconds": statistics.median(latencies),
        "latency_p95_seconds": percentile(latencies, 0.95),
        "latency_mean_seconds": statistics.mean(latencies),
        "gpu_peak_used_bytes": max(sample["used_bytes"] for sample in memory.samples),
        "gpu_memory_samples": memory.samples,
        "raw_output_sha256": hashlib.sha256(output_canonical.encode()).hexdigest(),
        "utterances": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: receipt[k] for k in (
        "run_id", "variant", "batch_size", "failure_count", "total_audio_seconds",
        "run_wall_seconds", "audio_seconds_per_wall_second", "real_time_factor",
        "utterances_per_second", "latency_p50_seconds", "latency_p95_seconds",
        "gpu_peak_used_bytes", "raw_output_sha256")}, indent=2))


if __name__ == "__main__":
    main()

