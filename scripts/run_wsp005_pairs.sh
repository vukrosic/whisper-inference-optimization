#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PY:-$PROJECT/.venv/bin/python}"
MANIFEST="$PROJECT/evidence/data/librispeech-test-clean-v1.json"
OUT="$PROJECT/evidence/candidates/WSP-005/paired"
mkdir -p "$OUT"

run_a() {
  local label=$1 result="$OUT/${1}.json"
  "$PY" "$PROJECT/benchmarks/run_benchmark.py" --manifest "$MANIFEST" \
    --data-root "$PROJECT/data" --download-root "$PROJECT/models/hf-cache" \
    --split development --variant serial --run-id "$label" --output "$result" \
    > "$OUT/${label}.log" 2>&1
  "$PY" "$PROJECT/benchmarks/evaluate.py" --manifest "$MANIFEST" --split development \
    --hypotheses "$result" --output "$OUT/${label}.quality.json" \
    > "$OUT/${label}.quality.log" 2>&1
}

run_b() {
  local label=$1 result="$OUT/${1}.json"
  "$PY" "$PROJECT/candidates/WSP-005/run_serial_int8.py" --manifest "$MANIFEST" \
    --data-root "$PROJECT/data" --download-root "$PROJECT/models/hf-cache" \
    --split development --variant serial --run-id "$label" --output "$result" \
    > "$OUT/${label}.log" 2>&1
  "$PY" "$PROJECT/benchmarks/evaluate.py" --manifest "$MANIFEST" --split development \
    --hypotheses "$result" --output "$OUT/${label}.quality.json" \
    > "$OUT/${label}.quality.log" 2>&1
}

run_a WSP-005-pair1-A-fp16
run_b WSP-005-pair1-B-int8f16
run_b WSP-005-pair2-B-int8f16
run_a WSP-005-pair2-A-fp16
run_a WSP-005-pair3-A-fp16
run_b WSP-005-pair3-B-int8f16
