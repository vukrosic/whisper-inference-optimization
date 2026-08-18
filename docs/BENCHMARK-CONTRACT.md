# Frozen speech-inference benchmark contract

Status: **FROZEN v1 — 2026-08-18 — preserved historical contract for the completed experiment**

The exact model snapshot, LibriSpeech archive and per-file manifest, dependency lock, evaluator, runner, normalization, baseline configuration, metrics, and promotion rules are frozen. No WSP candidate may run until B0 produces three valid deterministic development receipts.

## Product question

Can stock faster-whisper serving mechanisms improve warm English ASR throughput on the reference CUDA GPU while preserving the immutable FP16 baseline's full LibriSpeech WER and total edit distance, without materially harming batch-one latency?

## Frozen identities

- Logical model name: `turbo`.
- Official faster-whisper mapping at tag `v1.2.1`: `turbo` and `large-v3-turbo` resolve to `mobiuslabsgmbh/faster-whisper-large-v3-turbo`.
- faster-whisper source: tag `v1.2.1`, commit `65882eee9f5cdbeeb2d877f1131d48cf241b327d`.
- CTranslate2: `4.8.1`, tag commit `0d8bcd362ac75ef860ef161d6f0efad0ae439ff0`.
- Resolved model Hub snapshot: canonical `dropbox-dash/faster-whisper-large-v3-turbo`, revision `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf`, ungated, MIT. The official alias above remains the requested identity. Selected file SHA-256 hashes are in `evidence/model/files.sha256`; `model.bin` is `e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da`.
- Dataset: official OpenSLR SLR12 LibriSpeech `test-clean`, archive `test-clean.tar.gz`, published/verified MD5 `32fa31d27d2e1cad72775fee3f4849a9`, archive SHA-256 `39fde525e59672dc6d1551919b1478f724438a95aa55f874b576be21967e6c23`, CC BY 4.0. `test-other` is prohibited until a speed winner survives full `test-clean`.
- Hardware: NVIDIA CUDA GPU with 24,576 MiB; driver 595.84; CUDA toolkit 12.8.93; Ryzen 7 2700X 8c/16t; 31 GiB RAM. The implementation is not restricted to this reference device; other compatible GPUs require fresh timing and configuration selection.
- Experiment root: an isolated project directory on a non-persistent GPU container. The provider endpoint is intentionally omitted from this public copy.

## Workload

- Development screen: exactly 200 `test-clean` utterances selected before inference from duration quintiles, 40 per quintile, deterministically spread through each duration-sorted stratum. It contains 1,492.5350625 audio seconds. Manifest stores exact order, IDs, references, durations, byte sizes, and SHA-256 audio hashes.
- Full confirmation: all official `test-clean` utterances in lexicographic utterance-ID order with the same per-file metadata and hashes.
- Batch-one latency distribution: the same 200-item development screen, one request completed before the next begins.
- Audio is decoded in full. VAD is explicitly false. No transcript/result cache, skipped audio, reordered report, changed references, or candidate-specific preprocessing is allowed.
- Frozen manifest: `evidence/data/librispeech-test-clean-v1.json`, SHA-256 `4b02039657f80c16ac419099678c5fd3a413684f65fa8230e2ed38d03aa4b317`; full set is 2,620 utterances and 19,452.480625 audio seconds.

## Immutable baseline B0

- Stock `WhisperModel("turbo", device="cuda", compute_type="float16", revision=<pinned>)`, one warm resident model.
- Serial one-utterance-at-a-time `WhisperModel.transcribe`.
- Decode: `language="en"`, `task="transcribe"`, `beam_size=5`, `best_of=5`, `patience=1`, `length_penalty=1`, `temperature=0.0`, `condition_on_previous_text=False`, `without_timestamps=True`, `word_timestamps=False`, `vad_filter=False`, `initial_prompt=None`, `prefix=None`, `hotwords=None`, `suppress_blank=True`, `suppress_tokens=[-1]`, `repetition_penalty=1`, `no_repeat_ngram_size=0`.
- The generator is fully consumed before timing completes. Startup/model load and warmup are reported separately and excluded from steady-state wall time.
- Exact command is frozen in `baselines/B0-serial-fp16/manifest.json`.

## Candidate order

1. `WSP-001`: stock `BatchedInferencePipeline`, FP16, batch sizes 4/8/16 with identical decode semantics and VAD disabled. The public API batches chunks within one audio input; this limitation is part of the integrated-runtime result. Kill a size on OOM, failure, quality-gate breach, or throughput loss.
2. `WSP-002`: `int8_float16` at best surviving batch size. Kill as no-degradation candidate on any final edit-distance increase; also kill as product winner below 5% throughput gain versus immutable FP16 B0. A bounded quality tradeoff may remain only in a separate frontier.
3. `WSP-003`: duration-aware bounded microbatching/scheduling only if measured padding/profile evidence justifies it. Compare to stock batched incumbent, preserve request mapping/order, and declare maximum queue delay before implementation.

## Metrics and timing

- Primary: `audio_seconds / wall_seconds`, paired median candidate/baseline ratio.
- Also mandatory: real-time factor `wall/audio`, utterances/s, per-utterance e2e timing, p50/p95 batch-one latency, external GPU peak memory, failures, and startup/model-load time.
- Warm runs only. Every timed result contains raw per-utterance rows. CTranslate2 generator completion is the operation-completion boundary; no asynchronous work is left outstanding after full generator consumption.
- Confirmation uses at least three valid balanced interleaved AB/BA or ABBA blocks. Invalid runs remain preserved but do not count.
- Cost proxy: `audio_hours_per_gpu_hour = audio_seconds_per_wall_second`; optional `audio_hours_per_dollar(r) = audio_seconds_per_wall_second / r` for an explicitly labeled hourly-rate sensitivity only. No current rental-price claim is allowed without an authorized receipt.

## Quality oracle and gate

- Oracle: official LibriSpeech reference transcripts from the frozen archive.
- Shared normalization: Unicode NFKC, uppercase, punctuation replaced by spaces, whitespace collapsed, then word tokenization. The same implementation is applied to references and hypotheses.
- Report corpus WER, total substitutions/deletions/insertions, per-utterance edit counts and churn, exact normalized transcript matches, and SHA-256 of canonical `utterance_id<TAB>normalized_hypothesis` lines.
- Full no-degradation gate: candidate total edit distance may not exceed B0 and candidate corpus WER may not exceed B0. Zero failures is required.
- A candidate with at most +0.10 absolute percentage-point WER increase may be retained only as a separately labeled quality-budget frontier; it is never called no-degradation.

## Promotion and stopping

Promotion requires all of: at least +5% median paired primary-throughput gain, batch-one p50 regression no worse than 3%, p95 no worse than 5%, zero failures, and full no-increase WER/edit-distance gate on full `test-clean`. Narrower wins are reported without promotion.

Stop a candidate family on its declared kill rule, infrastructure failure after bounded diagnosis, or missing authority. A failed candidate is evidence, not project completion. Re-profile before WSP-003 and after any incumbent promotion.

## Claim boundaries

- Operator claim: isolated model/runtime operation only.
- Integrated claim: stock faster-whisper pipeline under this harness.
- Quality-evaluated claim: integrated result that passed the stated finite LibriSpeech gate.
- Whole-system claim: end-to-end decoded-audio throughput/latency including file decoding and host orchestration, excluding startup.

## Frozen code and environment receipts

- Manifest builder SHA-256: `aec871294420ff952dbc9b12d5d081db829b61ddb4e659163f88704d0fd332dc`.
- Evaluator SHA-256: `7408c02547a6be40e4550ba5ae7dbe22f29310b2bc8c61cba81be049f494051e`.
- Benchmark runner SHA-256: `dd05b77f23758fd12303d51455cfa2c79bd7c87654a28679e0c9ca1f1f95ee9f`.
- Dependency freeze SHA-256: `a94a0a0ac7c0afc4868d2b0df25d8edd7bda297b657573e24bc32c9773b7ed95`.
- Resolved runtime confirms one CUDA device and support for `float16` and `int8_float16`; exact package and host receipts live under `evidence/environment/`.
