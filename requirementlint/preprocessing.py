"""English tokenization with positions in the original requirement text."""

from dataclasses import dataclass
from functools import lru_cache
import re

from spacy.lang.en import English

from .parser import Requirement


_QUOTED_STRING = re.compile(r'"[^"\r\n]*"|“[^”\r\n]*”')


@dataclass(frozen=True)
class Token:
    """A word or punctuation token with zero-based, end-exclusive offsets.

    Offsets refer to the original requirement line, not the entire document.
    """

    text: str
    line_number: int
    start: int
    end: int


@lru_cache(maxsize=1)
def _english_tokenizer() -> English:
    # Reuse the tokenizer across requirements instead of rebuilding it per line.
    return English()


def mask_quoted_strings(text: str) -> str:
    """Replace straight- or curly-double-quoted text with a literal placeholder."""
    return _QUOTED_STRING.sub("LITERAL_STRING", text)


def tokenize_requirement(requirement: Requirement) -> list[Token]:
    """Tokenize English text without changing its spelling or source positions.

    Whitespace-only tokens are omitted; punctuation, numbers, and negation are
    retained. No trained model, POS tagging, or lemmatization is used here.
    """
    document = _english_tokenizer().make_doc(requirement.text)
    return [
        Token(
            text=token.text,
            line_number=requirement.line_number,
            start=token.idx,
            end=token.idx + len(token.text),
        )
        for token in document
        if not token.is_space
    ]
