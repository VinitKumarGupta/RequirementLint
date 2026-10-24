"""Train a demo classifier and compare it with rules on held-out examples."""

import json

import joblib
import sklearn
from sklearn.metrics import classification_report

from requirementlint import Requirement, check_imprecise_quantity, check_vague_wording
from requirementlint.classifier import MODEL_PATH, PROJECT_ROOT, create_pipeline
from requirementlint.preprocessing import tokenize_requirement


def read_examples(filename: str) -> list[dict]:
    examples = json.loads((PROJECT_ROOT / "data" / filename).read_text(encoding="utf-8"))
    if not examples or {item["label"] for item in examples} != {"clear", "vague"}:
        raise ValueError(f"{filename} must contain both clear and vague labelled examples.")
    normalized = [" ".join(item["text"].lower().split()) for item in examples]
    if any(not text for text in normalized) or len(normalized) != len(set(normalized)):
        raise ValueError(f"{filename} contains empty or duplicate examples.")
    return examples


def rule_prediction(text: str) -> str:
    requirement = Requirement(text=text, line_number=1)
    findings = check_vague_wording(requirement)
    findings.extend(check_imprecise_quantity(requirement, tokenize_requirement(requirement)))
    return "vague" if findings else "clear"


def main() -> None:
    training = read_examples("train.json")
    testing = read_examples("test.json")
    train_texts = [item["text"] for item in training]
    test_texts = [item["text"] for item in testing]
    normalize = lambda text: " ".join(text.lower().split())
    if set(map(normalize, train_texts)) & set(map(normalize, test_texts)):
        raise ValueError("Training and test examples must not overlap.")

    model = create_pipeline()
    model.fit(train_texts, [item["label"] for item in training])
    expected = [item["label"] for item in testing]
    predictions = model.predict(test_texts).tolist()
    baseline = [rule_prediction(text) for text in test_texts]

    report = {
        "dataset": "Synthetic starter examples; demonstration only, not a benchmark",
        "training_examples": len(training),
        "test_examples": len(testing),
        "sklearn_version": sklearn.__version__,
    }
    for name, predicted in (("rules", baseline), ("classifier", predictions)):
        print(f"\n{name.upper()} on the held-out synthetic examples")
        print(classification_report(expected, predicted, labels=["clear", "vague"], zero_division=0))
        report[name] = classification_report(
            expected, predicted, labels=["clear", "vague"], output_dict=True, zero_division=0
        )
    report["examples"] = [
        {"text": text, "expected": label, "rules": rule, "classifier": predicted}
        for text, label, rule, predicted in zip(test_texts, expected, baseline, predictions)
    ]

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    report_path = MODEL_PATH.parent / "evaluation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved model: {MODEL_PATH}")
    print(f"Saved evaluation: {report_path}")
    print("These scores describe a tiny synthetic test set, not real-world accuracy.")


if __name__ == "__main__":
    main()
