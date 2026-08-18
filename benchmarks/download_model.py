#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from faster_whisper.utils import download_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    resolved = download_model("turbo", cache_dir=str(output), revision=args.revision)
    receipt = {
        "logical_model_name": "turbo",
        "official_alias_repo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
        "requested_revision": args.revision,
        "resolved_local_path": str(Path(resolved).resolve()),
    }
    Path(args.receipt).write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
