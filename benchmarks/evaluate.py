#!/usr/bin/env python3
"""Candidate-independent LibriSpeech reference evaluator."""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import jiwer


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).upper()
    text = "".join(" " if unicodedata.category(ch)[0] in {"P", "S"} else ch for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def score_pair(reference: str, hypothesis: str) -> dict:
    ref = normalize(reference)
    hyp = normalize(hypothesis)
    result = jiwer.process_words(ref, hyp)
    return {
        "normalized_reference": ref,
        "normalized_hypothesis": hyp,
        "substitutions": result.substitutions,
        "deletions": result.deletions,
        "insertions": result.insertions,
        "edit_distance": result.substitutions + result.deletions + result.insertions,
        "reference_words": len(ref.split()),
        "exact_match": ref == hyp,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--split", choices=["development", "full"], required=True)
    parser.add_argument("--hypotheses", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    hypotheses_doc = json.loads(Path(args.hypotheses).read_text())
    expected = manifest[args.split]
    hypotheses = hypotheses_doc["utterances"]
    if [x["utterance_id"] for x in hypotheses] != [x["utterance_id"] for x in expected]:
        raise RuntimeError("hypothesis IDs/order do not exactly match frozen manifest")

    per_utterance = []
    for reference_item, hypothesis_item in zip(expected, hypotheses):
        scored = score_pair(reference_item["reference"], hypothesis_item.get("hypothesis", ""))
        per_utterance.append({
            "utterance_id": reference_item["utterance_id"],
            **scored,
            "failure": hypothesis_item.get("failure"),
        })
    substitutions = sum(item["substitutions"] for item in per_utterance)
    deletions = sum(item["deletions"] for item in per_utterance)
    insertions = sum(item["insertions"] for item in per_utterance)
    reference_words = sum(item["reference_words"] for item in per_utterance)
    edit_distance = substitutions + deletions + insertions
    canonical = "".join(
        f'{item["utterance_id"]}\t{item["normalized_hypothesis"]}\n' for item in per_utterance
    )
    report = {
        "schema": 1,
        "manifest": str(Path(args.manifest).resolve()),
        "split": args.split,
        "hypotheses": str(Path(args.hypotheses).resolve()),
        "utterance_count": len(per_utterance),
        "failure_count": sum(bool(item["failure"]) for item in per_utterance),
        "reference_words": reference_words,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "total_edit_distance": edit_distance,
        "wer": edit_distance / reference_words,
        "exact_transcript_matches": sum(item["exact_match"] for item in per_utterance),
        "normalized_output_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "per_utterance": per_utterance,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "utterance_count", "failure_count", "reference_words", "substitutions",
        "deletions", "insertions", "total_edit_distance", "wer",
        "exact_transcript_matches", "normalized_output_sha256")}, indent=2))


if __name__ == "__main__":
    main()

