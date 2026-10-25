"""A small supervised text classifier for requirement vagueness."""

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from .parser import Requirement
from .preprocessing import tokenize_requirement


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "requirement_classifier.joblib"
LABEL_NAMES = {"vague": "Potentially vague", "clear": "Relatively clear"}


@dataclass(frozen=True)
class FeatureContribution:
    """One present feature's contribution; positive favors vague."""

    feature: str
    score: float

    @property
    def supports(self) -> str:
        return "vague" if self.score > 0 else "clear"


@dataclass(frozen=True)
class PredictionExplanation:
    """The prediction and a breakdown of its linear decision score."""

    label: str
    contributions: list[FeatureContribution]
    intercept: float
    remaining_contribution: float
    decision_score: float
    known_feature_count: int


def feature_tokens(text: str) -> list[str]:
    """Reuse spaCy tokenization, keeping words, numbers, and negation.

    Standalone punctuation is excluded from features. Source text and the
    tokens used for highlighting are not modified.
    """
    return [
        token.text.lower()
        for token in tokenize_requirement(Requirement(text=text, line_number=1))
        if any(character.isalnum() for character in token.text)
    ]


class NumericSignalExtractor(BaseEstimator, TransformerMixin):
    """Count numeric and comparison cues that often indicate measurable requirements."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for text in X:
            rows.append([
                sum(character.isdigit() for character in text),
                text.count("%"),
                sum(character in "<>=" for character in text),
            ])
        return sparse.csr_matrix(np.asarray(rows, dtype=float))

    def get_feature_names_out(self, input_features=None):
        return np.asarray(
            ["numeric__digits", "numeric__percentages", "numeric__operators"],
            dtype=object,
        )


def create_pipeline() -> Pipeline:
    """Learn TF-IDF features and numeric cues before the classifier step."""
    return Pipeline([
        ("features", FeatureUnion([
            ("tfidf", TfidfVectorizer(
                tokenizer=feature_tokens,
                token_pattern=None,
                lowercase=False,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )),
            ("numeric", NumericSignalExtractor()),
        ])),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def load_model() -> Pipeline:
    """Load the local model produced by train_model.py in this environment."""
    return joblib.load(MODEL_PATH)


def explain_predictions(
    model: Pipeline, texts: list[str], top_n: int = 5
) -> list[PredictionExplanation]:
    """Explain binary Logistic Regression using TF-IDF value times weight.

    Only features present in each input are ranked, by absolute contribution.
    Scores are oriented toward vague regardless of the stored class order.
    Intercept plus all contributions equals the oriented decision score.
    These are model influences, not probability percentages or rule findings.
    """
    if top_n < 1:
        raise ValueError("top_n must be at least 1.")
    if not texts:
        return []

    if "features" in model.named_steps:
        feature_union = model.named_steps["features"]
        features = feature_union.transform(texts).tocsr()
        names = feature_union.get_feature_names_out()
    elif "tfidf" in model.named_steps:
        vectorizer = model.named_steps["tfidf"]
        features = vectorizer.transform(texts).tocsr()
        names = vectorizer.get_feature_names_out()
    else:
        raise ValueError("Explanations require a fitted TF-IDF feature extractor.")

    classifier = model.named_steps["classifier"]
    classes = list(classifier.classes_)
    if set(classes) != {"clear", "vague"} or classifier.coef_.shape[0] != 1:
        raise ValueError("Explanations require a binary clear/vague Logistic Regression model.")

    direction = 1.0 if classes[1] == "vague" else -1.0
    weights = classifier.coef_[0] * direction
    intercept = float(classifier.intercept_[0]) * direction
    labels = classifier.predict(features)
    scores = classifier.decision_function(features) * direction

    explanations = []
    for row_index, (label, score) in enumerate(zip(labels, scores)):
        row = features.getrow(row_index)
        contributions = [
            FeatureContribution(str(names[index]), float(value * weights[index]))
            for index, value in zip(row.indices, row.data)
            if value * weights[index] != 0
        ]
        contributions.sort(key=lambda item: (-abs(item.score), item.feature))
        shown = contributions[:top_n]
        remaining = sum(item.score for item in contributions[top_n:])
        explanations.append(PredictionExplanation(
            label=str(label),
            contributions=shown,
            intercept=intercept,
            remaining_contribution=remaining,
            decision_score=float(score),
            known_feature_count=row.nnz,
        ))
    return explanations
