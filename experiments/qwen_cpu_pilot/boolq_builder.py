"""Create a frozen, balanced BoolQ sample from the public human-labelled development set."""
from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

SOURCE_SHA = "ebc29ea3808c5c611672384b3de56e83349fe38fc1fe876fd29b674d81d0a80a"
QUESTIONS_SHA = "3fa33a0e7e968c99056ffe17a430a555a9678f717d6fdcc78e1c352dfa4eb462"
SEED = 20261113


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python boolq_builder.py /path/to/original/dev.jsonl")
    source = Path(sys.argv[1])
    assert sha(source) == SOURCE_SHA, "The source is not the original BoolQ dev.jsonl"
    data = [json.loads(line) for line in source.read_text(encoding="utf8").splitlines()]
    assert len(data) == 3270
    eligible = [(i, row) for i, row in enumerate(data) if 80 <= len(row["passage"]) <= 1700]
    positives = [i for i, row in eligible if row["answer"] is True]
    negatives = [i for i, row in eligible if row["answer"] is False]
    rng = random.Random(SEED)
    chosen = sorted(rng.sample(positives, 24) + rng.sample(negatives, 24))
    root = Path(__file__).resolve().parent
    out = root / "boolq"
    out.mkdir(exist_ok=True)
    shutil.copyfile(root / "local_models.py", out / "local_models.py")
    shutil.copyfile(root / "ridi-check.json", out / "ridi-check.json")
    with (out / "questions.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "question", "expected"])
        for index in chosen:
            row = data[index]
            passage = " ".join(row["passage"].split())
            question = " ".join(row["question"].split())
            prompt = (f"POLICY [p{index:04d}]: {passage}\n"
                      f"QUESTION: {question}\nGive exactly YES or NO, no other words.")
            writer.writerow([f"p{index:04d}", prompt, "YES" if row["answer"] else "NO"])
    assert sha(out / "questions.csv") == QUESTIONS_SHA, "Sample does not match the Windows freeze"
    assert sha(out / "local_models.py") == "716ef2147ed703ce1952778bac9e41698194a0c6b2da495e853dfacd75bb333d"
    info = {
        "dataset": "BoolQ dev (Google Research), Clark et al. 2019; CC BY-SA 3.0",
        "source_sha256": SOURCE_SHA,
        "questions_sha256": QUESTIONS_SHA,
        "seed": SEED,
        "selected_original_zero_based_indices": chosen,
        "n": 48, "n_yes": 24, "n_no": 24,
        "sampling": "Balanced without replacement after filtering source passages 80-1700 characters; not representative",
        "limitations": "Public dev labels; potential training contamination; no new blind adjudicators; model size swap not a same-weights update",
    }
    (out / "PRE_RUN_FREEZE.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf8")
    print("BOOLQ_FROZEN", json.dumps(info))


if __name__ == "__main__":
    main()
