# Failure index

Append failures; do not overwrite or erase them.

| UTC | ID | Stage | Classification | Evidence | Disposition |
| --- | --- | --- | --- | --- | --- |
| 2026-08-18 | SETUP-001 | Remote launcher | Invalid setup attempt | Shell could not open `logs/setup-remote.log` because redirection preceded script-created directory; reported PID 2772 exited immediately | Preserve; create `logs/` before launch and retry unchanged setup |
| 2026-08-18 | PROFILE-001 | B0 Nsight Compute basic profile | Infrastructure-blocked diagnostic | `ERR_NVGPUCTRPERM`: provider disallows NVIDIA hardware performance counters. Instrumented run remained exact but timing was distorted 10x and is invalid for speed | Preserve raw CSV/run; use external utilization/power/clock sampling; do not change driver permissions |
| 2026-08-18 | WSP-006-001 | FlashAttention warmup | Candidate/runtime incompatibility | Pinned CTranslate2 4.8.1 accepted `flash_attention=True` at construction but all five warmup transcriptions returned `RuntimeError: Flash attention 2 is not supported`; stock control passed exactly | Preserve control and failure log; terminally reject WSP-006; do not infer timing or quality from failed warmup |
