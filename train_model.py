"""Train on synthetic requirements; evaluate development data by default."""

import argparse
from collections import Counter
from itertools import combinations
import json

import joblib
import sklearn
from sklearn.metrics import classification_report

from requirementlint import (
    Requirement, check_imprecise_quantity, check_performance_criteria, check_vague_wording,
)
from requirementlint.classifier import MODEL_PATH, PROJECT_ROOT, create_pipeline
from requirementlint.preprocessing import tokenize_requirement


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def read_examples(filename: str) -> list[dict]:
    examples = json.loads((PROJECT_ROOT / "data" / filename).read_text(encoding="utf-8"))
    if not isinstance(examples, list) or not examples:
        raise ValueError(f"{filename} must contain a nonempty list of examples.")
    for index, item in enumerate(examples, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise ValueError(f"{filename}: example {index} needs a text string.")
        if item.get("label") not in ("clear", "vague"):
            raise ValueError(f"{filename}: example {index} needs a clear or vague label.")
    if {item["label"] for item in examples} != {"clear", "vague"}:
        raise ValueError(f"{filename} must contain both clear and vague labelled examples.")
    normalized = [normalize(item["text"]) for item in examples]
    if any(not text for text in normalized) or len(normalized) != len(set(normalized)):
        raise ValueError(f"{filename} contains empty or duplicate examples.")
    return examples


def rule_prediction(text: str) -> str:
    requirement = Requirement(text=text, line_number=1)
    findings = check_vague_wording(requirement)
    findings.extend(check_imprecise_quantity(requirement, tokenize_requirement(requirement)))
    findings.extend(check_performance_criteria(requirement))
    return "vague" if findings else "clear"


def evaluate(model, examples: list[dict], split: str, training_count: int) -> dict:
    texts = [item["text"] for item in examples]
    expected = [item["label"] for item in examples]
    predictions = model.predict(texts).tolist()
    baseline = [rule_prediction(text) for text in texts]

    report = {
        "dataset": "Synthetic requirements v2; demonstration only, not a benchmark",
        "evaluation_split": split,
        "training_examples": training_count,
        "evaluation_examples": len(examples),
        "sklearn_version": sklearn.__version__,
    }
    for name, predicted in (("rules", baseline), ("classifier", predictions)):
        print(f"\n{name.upper()} on the synthetic {split} split")
        print(classification_report(expected, predicted, labels=["clear", "vague"], zero_division=0))
        report[name] = classification_report(
            expected, predicted, labels=["clear", "vague"], output_dict=True, zero_division=0
        )
    report["examples"] = [
        {"text": text, "expected": label, "rules": rule, "classifier": predicted}
        for text, label, rule, predicted in zip(texts, expected, baseline, predictions)
    ]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluate-test", action="store_true",
        help="Also evaluate the reserved test set after model and data decisions are settled.",
    )
    args = parser.parse_args()

    datasets = {split: read_examples(f"{split}.json") for split in ("train", "dev", "test")}
    for split, examples in datasets.items():
        print(f"{split}: {len(examples)} examples; labels: {dict(Counter(item['label'] for item in examples))}")
    for left, right in combinations(datasets, 2):
        left_texts = {normalize(item["text"]) for item in datasets[left]}
        right_texts = {normalize(item["text"]) for item in datasets[right]}
        if left_texts & right_texts:
            raise ValueError(f"Duplicate requirements found across {left} and {right} splits.")

    training = datasets["train"]
    model = create_pipeline()
    model.fit([item["text"] for item in training], [item["label"] for item in training])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nSaved model: {MODEL_PATH}")
    splits_to_evaluate = ["dev", "test"] if args.evaluate_test else ["dev"]
    for split in splits_to_evaluate:
        report = evaluate(model, datasets[split], split, len(training))
        filename = "evaluation.json" if split == "dev" else "test_evaluation.json"
        report_path = MODEL_PATH.parent / filename
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved {split} evaluation: {report_path}")
    if not args.evaluate_test:
        print("\nReserved test metrics were not computed. Use --evaluate-test for final evaluation.")
    print("These scores describe synthetic examples, not real-world accuracy.")


if __name__ == "__main__":
    main()
