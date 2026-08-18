#!/usr/bin/env python3
"""Build a frozen LibriSpeech test-other confirmation manifest without model outputs."""
import argparse
import hashlib
import json
from pathlib import Path

import soundfile as sf

from build_manifest import evenly_spaced, sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Directory containing LibriSpeech/test-other")
    parser.add_argument("--output", required=True)
    parser.add_argument("--archive-sha256", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    split_root = root / "LibriSpeech" / "test-other"
    references: dict[str, str] = {}
    for transcript_path in sorted(split_root.rglob("*.trans.txt")):
        for line in transcript_path.read_text().splitlines():
            utterance_id, text = line.split(" ", 1)
            if utterance_id in references:
                raise RuntimeError(f"duplicate transcript {utterance_id}")
            references[utterance_id] = text

    entries = []
    for audio_path in sorted(split_root.rglob("*.flac")):
        utterance_id = audio_path.stem
        if utterance_id not in references:
            raise RuntimeError(f"missing transcript for {utterance_id}")
        info = sf.info(str(audio_path))
        entries.append({
            "utterance_id": utterance_id,
            "relative_path": str(audio_path.relative_to(root)),
            "reference": references[utterance_id],
            "duration_seconds": info.frames / info.samplerate,
            "frames": info.frames,
            "samplerate": info.samplerate,
            "channels": info.channels,
            "bytes": audio_path.stat().st_size,
            "sha256": sha256(audio_path),
        })
    entries.sort(key=lambda item: item["utterance_id"])
    if not entries or set(references) != {item["utterance_id"] for item in entries}:
        raise RuntimeError("audio/transcript ID sets differ or are empty")

    duration_sorted = sorted(entries, key=lambda item: (item["duration_seconds"], item["utterance_id"]))
    strata: list[list[dict]] = [[] for _ in range(5)]
    for index, entry in enumerate(duration_sorted):
        strata[min(4, index * 5 // len(duration_sorted))].append(entry)
    development = []
    for stratum_index, stratum_items in enumerate(strata):
        for entry in evenly_spaced(stratum_items, 40):
            development.append({**entry, "duration_stratum": stratum_index})
    development.sort(key=lambda item: item["utterance_id"])
    selected = {item["utterance_id"] for item in development}
    warmup = [item for item in entries if item["utterance_id"] not in selected][:5]

    manifest = {
        "schema": 1,
        "confirmation_only": True,
        "source": "OpenSLR SLR12 LibriSpeech test-other",
        "license": "CC BY 4.0",
        "published_archive_md5": "fb5a50374b501bb3bac4815ee91d3135",
        "archive_sha256": args.archive_sha256,
        "selection_rule": "full confirmation is all utterances in lexicographic ID order; development screen is frozen but may not be used for retuning",
        "full_count": len(entries),
        "development_count": len(development),
        "warmup_count": len(warmup),
        "total_audio_seconds_full": sum(item["duration_seconds"] for item in entries),
        "total_audio_seconds_development": sum(item["duration_seconds"] for item in development),
        "warmup": warmup,
        "development": development,
        "full": entries,
    }
    encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    Path(args.output).write_text(encoded)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "full_count": len(entries),
        "full_audio_seconds": manifest["total_audio_seconds_full"],
        "development_count": len(development),
    }, indent=2))


if __name__ == "__main__":
    main()
