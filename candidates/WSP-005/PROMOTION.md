# WSP-005 promotion receipt

Promoted role: serial throughput/latency incumbent.

- Mechanism: stock CTranslate2 `int8_float16`; stock serial faster-whisper decoder unchanged.
- Full FP16 receipt: `evidence/candidates/WSP-002/full-test-clean/WSP-002-full-A-fp16.json`, SHA-256 `a696f72238fbfef2e7398119eeb00fba6ac165b87ad56d9e20b2f69c35f2c44d`.
- Full FP16 quality: SHA-256 `81b7d435f453843ef14c2f57dc46345662dee00c8cc85d17f26f0f9b620804b9`.
- Full WSP-005 receipt: `evidence/candidates/WSP-005/full-test-clean/WSP-005-full-B-serial-int8f16.json`, SHA-256 `58a4e8af12f21741e09ad0d6f8c854c569759152176beec721e058bd4b15ad01`.
- Full WSP-005 quality: SHA-256 `6aa5d7abb48ae785d8319166adb4fb6433e0cc91e5314a83731e206f9cd2e28e`.
- Throughput: 46.0244× → 48.5461× (+5.4790%).
- p50/p95: 153.98/215.22 ms → 144.84/209.27 ms.
- Peak device allocation: 3,099,721,728 → 2,059,534,336 bytes.
- Quality: 1,391 → 1,368 edits; WER 2.6186% → 2.5753%; zero failures.

Claim boundary: quality-evaluated whole-system result for pinned faster-whisper/CTranslate2, pinned turbo snapshot, RTX 3090, and frozen LibriSpeech test-clean. It is not a novel-kernel claim and does not establish universal ASR quality.

