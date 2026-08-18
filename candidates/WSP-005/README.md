# WSP-005 — serial int8_float16 isolation

Status: promoted serial incumbent.

Mechanism: immutable serial `WhisperModel.transcribe` baseline path with only CTranslate2 `compute_type` changed from `float16` to `int8_float16`. This removes WSP-001/WSP-002 `BatchedInferencePipeline` semantic differences and isolates quantization.

The model revision, data, request order, decode options, VAD=false, normalization, evaluator, startup exclusion, and all gates remain frozen. Kill on any development edit-distance increase, less than 5% throughput gain, failure, or latency guardrail breach. Any survivor still requires balanced paired repetitions and full `test-clean`.

Initial screen: 49.7899× real-time (+5.98% vs B0 median), 116 edits / 2.8600% WER (B0 124 / 3.0572%), p50 142.75 ms, p95 210.91 ms, zero failures, and 2.06 GB peak.

Three fresh AB/BA/AB pairs yield throughput ratios 1.0431, 1.0623, and 1.0573 (median +5.7283%). Median p50/p95 ratios are 0.9434/0.9935. Quality hashes are deterministic and the candidate has 116 edits versus 124 in every control.

Promoted serial incumbent. On all 2,620 `test-clean` utterances, WSP-005 reaches 48.5461× versus 46.0244× (+5.4790%), improves p50/p95 5.94%/2.77%, reduces peak memory 33.56%, and improves the frozen oracle from 1,391 edits / 2.6186% WER to 1,368 edits / 2.5753% WER, with zero failures. This finite-suite result supports “no degradation on frozen test-clean,” not universal quality equivalence.
