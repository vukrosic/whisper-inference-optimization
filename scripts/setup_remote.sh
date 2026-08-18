#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ENV_DIR="$PROJECT/.venv"
MODEL_DIR="$PROJECT/models/hf-cache"
DATA_DIR="$PROJECT/data"
LOG_DIR="$PROJECT/logs"
EVIDENCE_DIR="$PROJECT/evidence"
REVISION=0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf

mkdir -p "$MODEL_DIR" "$DATA_DIR" "$LOG_DIR" "$EVIDENCE_DIR/model" "$EVIDENCE_DIR/data" "$EVIDENCE_DIR/environment"
date -u +%FT%TZ > "$EVIDENCE_DIR/setup-started-utc.txt"

uv venv --python "${PYTHON:-python3}" "$ENV_DIR"
uv pip install --python "$ENV_DIR/bin/python" \
  faster-whisper==1.2.1 \
  ctranslate2==4.8.1 \
  jiwer==4.0.0 \
  soundfile==0.14.0 \
  nvidia-ml-py==13.580.82 \
  psutil==7.0.0
uv pip freeze --python "$ENV_DIR/bin/python" | LC_ALL=C sort > "$EVIDENCE_DIR/environment/uv-pip-freeze.txt"

"$ENV_DIR/bin/python" "$PROJECT/benchmarks/download_model.py" \
  --output-dir "$MODEL_DIR" \
  --revision "$REVISION" \
  --receipt "$EVIDENCE_DIR/model/download-receipt.json" \
  > "$LOG_DIR/model-download.log" 2>&1 &
MODEL_PID=$!

curl --fail --location --retry 3 --retry-delay 2 \
  --output "$DATA_DIR/test-clean.tar.gz" \
  https://www.openslr.org/resources/12/test-clean.tar.gz \
  > "$LOG_DIR/test-clean-download.log" 2>&1 &
DATA_PID=$!

printf '%s\n' "$MODEL_PID" > "$EVIDENCE_DIR/model/download.pid"
printf '%s\n' "$DATA_PID" > "$EVIDENCE_DIR/data/download.pid"
wait "$MODEL_PID"
wait "$DATA_PID"

md5sum "$DATA_DIR/test-clean.tar.gz" > "$EVIDENCE_DIR/data/test-clean.md5"
sha256sum "$DATA_DIR/test-clean.tar.gz" > "$EVIDENCE_DIR/data/test-clean.sha256"
test "$(cut -d' ' -f1 "$EVIDENCE_DIR/data/test-clean.md5")" = "32fa31d27d2e1cad72775fee3f4849a9"
tar -xzf "$DATA_DIR/test-clean.tar.gz" -C "$DATA_DIR"

ARCHIVE_SHA256=$(cut -d' ' -f1 "$EVIDENCE_DIR/data/test-clean.sha256")
"$ENV_DIR/bin/python" "$PROJECT/benchmarks/build_manifest.py" \
  --root "$DATA_DIR" \
  --output "$EVIDENCE_DIR/data/librispeech-test-clean-v1.json" \
  --archive-sha256 "$ARCHIVE_SHA256" \
  > "$LOG_DIR/manifest-build.log" 2>&1

"$ENV_DIR/bin/python" - <<'PY' > "$EVIDENCE_DIR/environment/runtime.json"
import json
import ctranslate2
import faster_whisper
import huggingface_hub
import jiwer
import soundfile
print(json.dumps({
    "faster_whisper": faster_whisper.__version__,
    "ctranslate2": ctranslate2.__version__,
    "huggingface_hub": huggingface_hub.__version__,
    "jiwer": getattr(jiwer, "__version__", "4.0.0"),
    "soundfile": soundfile.__version__,
    "cuda_device_count": ctranslate2.get_cuda_device_count(),
    "supported_compute_types_cuda0": sorted(ctranslate2.get_supported_compute_types("cuda", 0)),
}, indent=2))
PY

date -u +%FT%TZ > "$EVIDENCE_DIR/setup-completed-utc.txt"
