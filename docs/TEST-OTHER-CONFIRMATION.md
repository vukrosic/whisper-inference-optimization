# LibriSpeech test-other confirmation

Status: **COMPLETE - strict quality gate failed; retained only as a quality-budget frontier; no retuning**

The frozen v1 contract prohibited test-other until a strict speed winner survived full test-clean. WSP-005 and WSP-004 now satisfy that prerequisite. This supplemental confirmation is therefore activated as a harder-distribution generalization check, not a new optimization search or a replacement for the frozen primary benchmark.

## Frozen identity and workload

- Dataset: official OpenSLR SLR12 LibriSpeech `test-other`, CC BY 4.0.
- Source URL: `https://www.openslr.org/resources/12/test-other.tar.gz`.
- Published MD5: `fb5a50374b501bb3bac4815ee91d3135`.
- Verified archive SHA-256: `d09c181bba5cf717b3dee7d4d592af11a3ee3a09e08ae025c5506f6ebe961c29`.
- Workload: every utterance in lexicographic utterance-ID order, full audio, exact official references, per-file byte size and SHA-256, no VAD/skipping/cache/reordering.
- Manifest builder: independent `benchmarks/build_test_other_manifest.py`; its source hash and the archive/manifest hashes must be recorded before inference.
- Frozen builder SHA-256: `62c0e3549bc7560a1d3203a5de3305584570ad70c39d64f87524fa28ec4ed073`.
- Frozen acquisition script SHA-256: `8f1c63b2637c7ba7d784dff5b12b9b40590871105cc2d8f2ce34dee59fc4c6df`.
- Frozen confirmation sequence SHA-256: `77c4717ff6f2f017b4b9ae2d7142a5b69459aeb54fe7c5aa924a2216ac177e92`.
- Frozen manifest: `evidence/data/librispeech-test-other-v1.json`, SHA-256 `ff5d02bf0da19af23e88be54690aeb3ffccf8f98b7a399627b2a35be70d65eb3`.
- Full set: 2,939 utterances, 19,229.570125 audio seconds. The unused no-retuning development partition is 200 utterances / 1,315.9950625 seconds.
- Decode/model/runtime/hardware/evaluator: exactly frozen v1. No option may be changed in response to test-other output.

## Confirmation sequence

1. Download and verify the official archive on the GPU only; model/audio remain remote.
2. Freeze archive SHA-256, per-file manifest, count, duration, and manifest SHA-256; sync receipts/manifest to the Mac.
3. Run one full serial FP16 B0 receipt and evaluate it.
4. Run promoted WSP-004 (`int8_float16`, workers=2, bounded concurrency=4) and evaluate it.

This sequence is for out-of-sample quality/generalization and a supplemental whole-system throughput cross-check. The existing three-pair test-clean result remains the promotion statistic. On test-other, no-degradation means candidate total edit distance and corpus WER must not exceed its fresh FP16 B0, with zero failures. If it fails, preserve the result and narrow the portfolio claim to test-clean; do not retune on test-other.

## Result

| Metric | Fresh FP16 B0 | Promoted int8 workers=2, c=4 | Delta |
| --- | ---: | ---: | ---: |
| Audio / wall | 41.9647x | 59.8710x | +42.6700% |
| Wall time | 458.233 s | 321.184 s | -29.9082% |
| RTF | 0.023830 | 0.016703 | better |
| Utterances/s | 6.414 | 9.151 | +42.6700% |
| GPU peak | 3,099,721,728 B | 2,437,021,696 B | -21.3793% |
| Failures | 0 | 0 | pass |
| Substitutions / deletions / insertions | 1,878 / 454 / 226 | 1,894 / 459 / 226 | +16 / +5 / 0 |
| Total edits | 2,558 | 2,579 | **+21 - strict fail** |
| Corpus WER | 4.824503% | 4.864110% | **+0.039607 pp - strict fail** |
| Exact transcript matches | 1,702 | 1,695 | -7 |

Disposition: the harder set independently confirms a large throughput/memory/cost-capacity benefit and zero failures, but not no-degradation quality. It is retained only as the contract's separate <=0.10 absolute percentage-point WER quality-budget frontier. The strict portfolio claim remains limited to frozen test-clean, and no WSP candidate is tuned from test-other.

Immutable receipts:

- FP16 performance SHA-256: `cc077647e4937ab63903c6b36a3721b606bd05a7eac2a74d6193c5687c60b20a`.
- FP16 quality SHA-256: `4290a064a1d39c4b772a03243188e8965a17fc00c7ec04daba0e9a5430019c7a`.
- Candidate performance SHA-256: `38d9538952b8f284af13f2c605be47c4e3ab15e417fc141734f3c22f8caf627f`.
- Candidate quality SHA-256: `dfc4aa60c13e52c17f87001fe01ede14a4f59935d819ac8879580239853626ba`.
