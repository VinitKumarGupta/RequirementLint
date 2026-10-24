"""A small supervised text classifier for requirement vagueness."""

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .parser import Requirement
from .preprocessing import tokenize_requirement


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "requirement_classifier.joblib"
LABEL_NAMES = {"vague": "Potentially vague", "clear": "Relatively clear"}


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


def create_pipeline() -> Pipeline:
    """Learn TF-IDF features and classifier weights from training data only."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            tokenizer=feature_tokens,
            token_pattern=None,
            lowercase=False,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def load_model() -> Pipeline:
    """Load the local model produced by train_model.py in this environment."""
    return joblib.load(MODEL_PATH)
