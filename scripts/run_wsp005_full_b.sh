#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PY:-$PROJECT/.venv/bin/python}"
MANIFEST="$PROJECT/evidence/data/librispeech-test-clean-v1.json"
OUT="$PROJECT/evidence/candidates/WSP-005/full-test-clean"
mkdir -p "$OUT"

B="$OUT/WSP-005-full-B-serial-int8f16.json"
"$PY" "$PROJECT/candidates/WSP-005/run_serial_int8.py" \
  --manifest "$MANIFEST" --data-root "$PROJECT/data" \
  --download-root "$PROJECT/models/hf-cache" --split full \
  --variant serial --run-id WSP-005-full-B-serial-int8f16 --output "$B" \
  > "$OUT/WSP-005-full-B-serial-int8f16.log" 2>&1
"$PY" "$PROJECT/benchmarks/evaluate.py" --manifest "$MANIFEST" --split full \
  --hypotheses "$B" --output "$OUT/WSP-005-full-B-serial-int8f16.quality.json" \
  > "$OUT/WSP-005-full-B-serial-int8f16.quality.log" 2>&1
