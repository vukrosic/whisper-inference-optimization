# WSP-004 promotion receipt

Promoted role: concurrent-serving incumbent at bounded closed-loop concurrency 4.

- Mechanism: official faster-whisper `WhisperModel(num_workers=2)` with concurrent stock `transcribe` calls; WSP-005 `int8_float16` compute and every frozen decode/data/quality setting are unchanged.
- Harness: schema 2 bounded closed loop, at most four requests in flight, immediate replacement on completion, queue delay included, results restored to immutable manifest order.
- Paired development confirmation: workers=2 versus matched workers=1 at concurrency 4 in AB/BA/AB blocks; throughput ratios `1.1445586850`, `1.1383332580`, `1.1310251228`; median gain `+13.8333%`.
- Paired latency: median p50 ratio `0.8686022218` (13.14% better); median p95 ratio `1.0131246796` (+1.31%, within the 5% guardrail).
- Batch-one guardrail: 144.76 ms p50, 211.99 ms p95, zero failures, 2,135,031,808-byte peak; p50/p95 changes versus WSP-005 are -0.06%/+1.30%.
- Full test-clean: 67.3148312934 audio-seconds/wall-second, RTF 0.0148555672, 9.06645 utterances/s, 288.9776 s wall, and 2,437,021,696-byte peak.
- Full quality: 988 substitutions, 281 deletions, 99 insertions, 1,368 edits, 2.575301% WER, 1,890 exact matches, zero failures. Raw and normalized output hashes exactly match WSP-005.
- Combined full-set result versus immutable FP16 B0: +46.2590% throughput, 31.6281% less wall time, and 21.3793% lower measured peak allocation.
- Mechanism-only full-set result versus serial WSP-005: +38.6618% throughput. The paired mechanism claim remains the more defensible +13.8333% because it uses matched concurrent controls.
- Full performance receipt: `evidence/candidates/WSP-004/guardrails/WSP-004-w2-c4-full-test-clean.json`, SHA-256 `7d87bbac8ac28fb2d3d369a18d8c3bd3d68c2e60738686387677cda4bb2d8185`.
- Full quality receipt: SHA-256 `647a6bfb4c0a6a8e5cf851461949d427e2211e4a7740dab45ff26ffc5e5383aa`.
- Batch-one performance receipt: SHA-256 `310143f58fe8e504e997fe1948acb8c5f838a07fbe356b22305a0e34635a278e`.
- Batch-one quality receipt: SHA-256 `c515de85f0a56c82b2fffb06394508e96eb3ae5be8a9127c64be0fde683f320a`.
- Candidate harness SHA-256: `25c09d932e366da3f3ed23408e25f5c8b037257e0af3318c95f91bcaed434b4a`.

Claim boundary: quality-evaluated whole-system concurrent result for the pinned faster-whisper/CTranslate2 stack, pinned turbo snapshot, one RTX 3090, bounded concurrency 4, and frozen LibriSpeech test-clean. It is a supported integrated-runtime configuration result, not a novel kernel or universal ASR-quality claim.
