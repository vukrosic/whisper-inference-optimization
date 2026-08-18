#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PY:-$PROJECT/.venv/bin/python}"
MANIFEST="$PROJECT/evidence/data/librispeech-test-clean-v1.json"
OUT="$PROJECT/evidence/candidates/WSP-004/paired-v2"
mkdir -p "$OUT"

run_cfg() {
  local workers=$1 label=$2 result="$OUT/${2}.json"
  "$PY" "$PROJECT/candidates/WSP-004/run_concurrent.py" \
    --manifest "$MANIFEST" --data-root "$PROJECT/data" \
    --download-root "$PROJECT/models/hf-cache" --compute-type int8_float16 \
    --workers "$workers" --concurrency 4 --run-id "$label" --output "$result" \
    > "$OUT/${label}.log" 2>&1
  "$PY" "$PROJECT/benchmarks/evaluate.py" --manifest "$MANIFEST" --split development \
    --hypotheses "$result" --output "$OUT/${label}.quality.json" \
    > "$OUT/${label}.quality.log" 2>&1
}

run_cfg 1 WSP-004-v2-pair1-A-w1c4
run_cfg 2 WSP-004-v2-pair1-B-w2c4
run_cfg 2 WSP-004-v2-pair2-B-w2c4
run_cfg 1 WSP-004-v2-pair2-A-w1c4
run_cfg 1 WSP-004-v2-pair3-A-w1c4
run_cfg 2 WSP-004-v2-pair3-B-w2c4
