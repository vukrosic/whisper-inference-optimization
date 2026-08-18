# RTX 3090 Whisper serving portfolio case

## Outcome

On one RTX 3090, a pinned faster-whisper 1.2.1 / CTranslate2 4.8.1 deployment of the pinned `turbo` model snapshot was improved from 46.0244x to 67.3148x real time on all 2,620 LibriSpeech test-clean utterances. The promoted configuration uses supported `int8_float16` compute and two stock model workers under bounded closed-loop concurrency four.

The combined result is +46.2590% throughput and 31.6281% less wall time versus immutable serial FP16 B0. It has zero failed requests, 21.38% lower measured GPU peak allocation, and better finite-oracle quality on test-clean: 1,368 edits / 2.5753% WER versus 1,391 / 2.6186%. This strict result is limited to the frozen primary workload, not a universal quality or novel-kernel claim.

The predeclared harder test-other set confirms +42.6700% throughput, zero failures, and 21.38% lower peak memory, but adds 21 edits and +0.039607 absolute percentage points WER. That result is reported only as a bounded speed-quality frontier, never no-degradation. No retuning was performed after seeing it.

## Product metrics

| Configuration | Product lane | Audio / wall | RTF | Utterances/s | p50 / p95 | GPU peak | Edits / WER | Failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 FP16, workers=1 | Serial full set | 46.0244x | 0.021728 | 6.199 | 153.98 / 215.22 ms | 3.100 GB | 1,391 / 2.6186% | 0 |
| WSP-005 int8_float16 | Serial full set | 48.5461x | 0.020599 | 6.539 | 144.84 / 209.27 ms | 2.060 GB | 1,368 / 2.5753% | 0 |
| WSP-004 int8, workers=2, c=4 | Concurrent full set | 67.3148x | 0.014856 | 9.066 | 423.26 / 621.32 ms concurrent e2e | 2.437 GB | 1,368 / 2.5753% | 0 |
| WSP-004 workers=2, c=1 | Batch-one development guardrail | 49.0830x | 0.020374 | 6.611 | 144.76 / 211.99 ms | 2.135 GB | 116 / 2.8600% | 0 |

Concurrent latency includes service plus queue delay for the bounded four-request window. It is not presented as batch-one latency. The separate concurrency-one row is the frozen batch-one guardrail.

## Fairness and quality contract

- Model: logical faster-whisper `turbo`; resolved snapshot `dropbox-dash/faster-whisper-large-v3-turbo@0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf`; `model.bin` SHA-256 `e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da`.
- Runtime: faster-whisper 1.2.1 commit `65882eee9f5cdbeeb2d877f1131d48cf241b327d`; CTranslate2 4.8.1 commit `0d8bcd362ac75ef860ef161d6f0efad0ae439ff0`.
- Workload: official OpenSLR SLR12 test-clean, archive MD5 `32fa31d27d2e1cad72775fee3f4849a9`; frozen manifest SHA-256 `4b02039657f80c16ac419099678c5fd3a413684f65fa8230e2ed38d03aa4b317`.
- Decode stays beam 5, English, temperature 0, `condition_on_previous_text=False`, timestamps off, VAD explicitly off. Every generator is fully consumed.
- The evaluator is candidate-independent. Full promotion requires no increase in corpus WER or edit distance, zero failures, at least 5% paired primary-throughput gain, and batch-one p50/p95 regressions no worse than 3%/5%.
- WSP-004 used three bounded AB/BA/AB blocks against a matched workers=1/concurrency=4 control. Its mechanism-only throughput ratios were 1.1446, 1.1383, and 1.1310; median +13.8333%.

The complete frozen contract is `docs/BENCHMARK-CONTRACT.md`; immutable receipt hashes are in `candidates/WSP-005/PROMOTION.md` and `candidates/WSP-004/PROMOTION.md`.

## Cost-capacity proxy

At an hourly GPU price `r`:

- B0 capacity is `46.0244` audio-hours/GPU-hour and cost is `r / 46.0244` per processed audio hour.
- Promoted concurrent capacity is `67.3148` audio-hours/GPU-hour and cost is `r / 67.3148` per processed audio hour.
- The price-independent reduction in GPU cost per processed audio hour is 31.6281%.

No rental price was authorized or captured, so this case intentionally makes no absolute dollar claim.

## Harder-set generalization

| Configuration | Audio / wall | Wall | Peak | Edits / WER | Failures | Disposition |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Fresh FP16 B0, test-other | 41.9647x | 458.23 s | 3.100 GB | 2,558 / 4.8245% | 0 | Oracle |
| int8 workers=2 c=4, test-other | 59.8710x | 321.18 s | 2.437 GB | 2,579 / 4.8641% | 0 | <=0.10 pp quality-budget frontier only |

The performance gain is +42.67% and the implied fixed-rate GPU cost per audio hour falls 29.91%. The +21 edits / +0.03961 pp WER fails the full no-increase gate, so the client-facing deployment choice is explicit: strict evidence on test-clean, or a measured harder-set speed-quality tradeoff.

## Negative evidence

- WSP-001 stock `BatchedInferencePipeline` FP16 at batch 4/8/16 was slower than B0 and changed output from 124 to 130 development edits; the entire family was rejected.
- WSP-002 batched `int8_float16` was +5.6487% on full test-clean but added four edits. It is retained only as a +0.00753 percentage-point WER quality-budget frontier, never a no-degradation win.
- WSP-003 duration scheduling was killed before implementation because the measured/public one-input chunking path did not establish the required padding opportunity.
- WSP-006 FlashAttention failed every warmup request with `RuntimeError: Flash attention 2 is not supported` in the pinned CTranslate2 build. The stock control remained exact; no candidate timing claim is made.
- WSP-007 `int8_bfloat16` was slower in both lanes and increased development edits from 116 to 122.
- WSP-008 native `int8` preserved exact quality but was 0.30% slower at batch one and 0.90% slower concurrently.
- Nsight Compute counters were provider-blocked by `ERR_NVGPUCTRPERM`; no counter-derived claim is made. External GPU sampling and whole-system timing remain valid.

These failures are preserved in `state/inference-traces.jsonl` and `docs/FAILURE-INDEX.md`.

## Reproduction map

Run only on the project-owned GPU after confirming it is process-idle:

```bash
PROJECT=/workspace/whisper-large-v3-turbo-rtx3090-serving
sha256sum "$PROJECT/evidence/data/librispeech-test-clean-v1.json" \
  "$PROJECT/candidates/WSP-004/run_concurrent.py"

bash "$PROJECT/scripts/run_wsp005_pairs.sh"
bash "$PROJECT/scripts/run_wsp005_full_b.sh"
bash "$PROJECT/scripts/run_wsp004_pairs_v2.sh"
bash "$PROJECT/scripts/run_wsp004_guardrails.sh"
```

The setup/download script originates model and dataset downloads on the GPU. Model/audio artifacts remain remote; only source and receipts are synchronized to the Mac. Raw per-utterance outputs, timings, memory samples, evaluator outputs, hashes, logs, and sequence order are under `evidence/`.

## Claim separation

- Operator: CTranslate2 stock compute/worker options only.
- Integrated runtime: faster-whisper decode plus host file decode, feature extraction, scheduling, and result materialization.
- Quality evaluated: official references through the frozen independent evaluator.
- Whole system: all 19,452.480625 audio seconds, excluding separately reported model startup but including request orchestration and complete generator consumption.
