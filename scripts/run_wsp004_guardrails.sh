#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PY:-$PROJECT/.venv/bin/python}"
MANIFEST="$PROJECT/evidence/data/librispeech-test-clean-v1.json"
OUT="$PROJECT/evidence/candidates/WSP-004/guardrails"
mkdir -p "$OUT"

ONE="$OUT/WSP-004-w2-c1-batch-one.json"
"$PY" "$PROJECT/candidates/WSP-004/run_concurrent.py" \
  --manifest "$MANIFEST" --data-root "$PROJECT/data" \
  --download-root "$PROJECT/models/hf-cache" --compute-type int8_float16 \
  --workers 2 --concurrency 1 --split development \
  --run-id WSP-004-w2-c1-batch-one --output "$ONE" \
  > "$OUT/WSP-004-w2-c1-batch-one.log" 2>&1
"$PY" "$PROJECT/benchmarks/evaluate.py" --manifest "$MANIFEST" --split development \
  --hypotheses "$ONE" --output "$OUT/WSP-004-w2-c1-batch-one.quality.json" \
  > "$OUT/WSP-004-w2-c1-batch-one.quality.log" 2>&1

FULL="$OUT/WSP-004-w2-c4-full-test-clean.json"
"$PY" "$PROJECT/candidates/WSP-004/run_concurrent.py" \
  --manifest "$MANIFEST" --data-root "$PROJECT/data" \
  --download-root "$PROJECT/models/hf-cache" --compute-type int8_float16 \
  --workers 2 --concurrency 4 --split full \
  --run-id WSP-004-w2-c4-full-test-clean --output "$FULL" \
  > "$OUT/WSP-004-w2-c4-full-test-clean.log" 2>&1
"$PY" "$PROJECT/benchmarks/evaluate.py" --manifest "$MANIFEST" --split full \
  --hypotheses "$FULL" --output "$OUT/WSP-004-w2-c4-full-test-clean.quality.json" \
  > "$OUT/WSP-004-w2-c4-full-test-clean.quality.log" 2>&1
