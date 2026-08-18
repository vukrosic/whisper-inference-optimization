#!/usr/bin/env python3
"""Run frozen serial harness with only compute_type changed to int8_float16."""
import importlib.util
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT / "benchmarks" / "run_benchmark.py"
spec = importlib.util.spec_from_file_location("frozen_whisper_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)

original_model = runner.WhisperModel


def int8_model(*args, **kwargs):
    kwargs["compute_type"] = "int8_float16"
    return original_model(*args, **kwargs)


runner.WhisperModel = int8_model
runner.main()

output = Path(sys.argv[sys.argv.index("--output") + 1])
receipt = json.loads(output.read_text())
receipt["compute_type"] = "int8_float16"
receipt["variant"] = "serial_int8_float16"
receipt["candidate_id"] = "WSP-005"
receipt["frozen_runner_sha256"] = "dd05b77f23758fd12303d51455cfa2c79bd7c87654a28679e0c9ca1f1f95ee9f"
output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

