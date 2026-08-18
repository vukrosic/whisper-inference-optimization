# WSP-004 — stock multi-request workers

Status: promoted concurrent-serving incumbent on WSP-005 int8.

Mechanism: faster-whisper's documented `WhisperModel(num_workers=N)` plus concurrent `transcribe` calls from Python threads. This is a supported integrated-runtime scheduling mechanism, not a novel kernel. The initial screen compares int8 workers=1/concurrency=4 control to workers=2 and 4 at concurrency=4 on identical request submission order, then separately checks concurrency=1 latency for a survivor.

All frozen model, decode, VAD, data, normalization, and quality rules apply. Results are reordered to the immutable utterance order before evaluation. Queue delay is included in per-request end-to-end latency; primary throughput includes the complete concurrent block wall time.

Attempt-v1 screen submitted all 200 requests at time zero. Its throughput and output evidence are valid, but latency describes a queued backlog and is not used as request-latency evidence. Confirmation uses harness schema 2: bounded closed-loop concurrency with at most four in-flight requests, immediate replacement on completion, and immutable output reordering.

Kill on OOM/failure, any development edit-distance increase, less than 5% throughput gain in a valid screen, or batch-one guardrail breach. A survivor requires three paired interleaved blocks and full `test-clean` confirmation before promotion.

Schema-2 AB/BA/AB confirmation for workers=2 versus workers=1 at concurrency 4 yields throughput ratios 1.1446, 1.1383, and 1.1310 (median +13.8333%). Median p50 improves 13.14%; median p95 regresses 1.31%, within guardrail. All outputs exactly match WSP-005 quality.

The workers=2 batch-one check preserves the development output and records p50/p95 of 144.76/211.99 ms, respectively -0.06%/+1.30% versus WSP-005. Full test-clean reaches 67.3148 audio-seconds/wall-second with zero failures and exactly the WSP-005 transcript and normalized-output hashes: 1,368 edits, 2.5753% WER. See `PROMOTION.md` for immutable receipt hashes and claim boundaries.
