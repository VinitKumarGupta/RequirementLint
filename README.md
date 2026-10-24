# RequirementLint

RequirementLint will help people review software requirements written in English. It will flag wording that may be vague or difficult to test, explain the issue, and suggest what information to add.

For example, "The application should load quickly" does not tell a tester how long loading may take. The tool will ask for a time limit and test conditions. The stakeholder decides the actual target.

## Project status

Early development: line-based input parsing, English tokenization with spaCy, and an initial vague-wording rule are implemented. The tokenizer is available as a preprocessing component; the current warning rule still operates directly on text. Token-aware rules, part-of-speech tagging, classification, and the interface are planned.

See [example requirements](docs/examples.md) for the proposed warnings and expected behavior.

## Setup

Requires Python 3.10 or newer; tested with standard CPython 3.12 on Windows. On Windows, use a standard Windows Python installation rather than MSYS2 Python for compatibility with spaCy's prebuilt packages. Run commands from the repository root.

Create an isolated environment and install dependencies:

```sh
python -m venv .venv
```

On Windows:

```sh
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or Linux:

```sh
.venv/bin/python -m pip install -r requirements.txt
```

The examples below use `python`. Replace it with `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux unless the environment is already activated. No trained spaCy model download is needed for tokenization. After installation, tokenization runs locally without network access.

## Run the parser

```sh
python -c "from requirementlint import parse_requirements; print(parse_requirements('The application should load quickly.'))"
```

Expected output:

```text
[Requirement(text='The application should load quickly.', line_number=1)]
```

The parser accepts one requirement per line. Blank lines are skipped, while original line numbers and wording (including surrounding spaces) are preserved. Multiple sentences on the same line remain one requirement. This step organizes the input; it does not yet identify vague wording.

For use in Python:

```python
from requirementlint import parse_requirements

text = "The application should load quickly.\n\nThe system must save changes."
for requirement in parse_requirements(text):
    print(f"{requirement.line_number}: {requirement.text}")
```

Output:

```text
1: The application should load quickly.
3: The system must save changes.
```

## Tokenize requirements

Tokenization splits each requirement into language-aware units such as words and punctuation. spaCy's English tokenizer handles contractions and decimal numbers: `Don't` becomes `Do` and `n't`, while `2.5` stays together. Hyphenated phrases can span multiple tokens; `user-friendly` becomes `user`, `-`, and `friendly`.

Try it from the terminal:

```sh
python -c "from requirementlint import Requirement; from requirementlint.preprocessing import tokenize_requirement; print([t.text for t in tokenize_requirement(Requirement('Load quickly.', 1))])"
```

Output:

```text
['Load', 'quickly', '.']
```

For use with the parser:

```python
from requirementlint import parse_requirements
from requirementlint.preprocessing import tokenize_requirement

for requirement in parse_requirements("Load quickly."):
    for token in tokenize_requirement(requirement):
        print(f"{token.text!r}: line {token.line_number}, characters [{token.start}, {token.end})")
```

Output:

```text
'Load': line 1, characters [0, 4)
'quickly': line 1, characters [5, 12)
'.': line 1, characters [12, 13)
```

Character ranges are zero-based and exclude the end position. Each token preserves the original spelling and source line number. Whitespace-only tokens are omitted, but positions still refer to the unchanged input. Punctuation, numbers, quotes, and negation are retained for later checks.

This component uses spaCy's English tokenization rules. It does not assign grammatical tags, produce lemmas, classify requirements, or infer meaning. The existing `RL001` rule remains an independent baseline and does not yet consume these tokens. See [spaCy's tokenization documentation](https://spacy.io/usage/linguistic-features#tokenization).

## Check vague wording

Rule `RL001` detects `quickly`, `user-friendly`, and `efficiently`, ignoring letter case. Each finding contains the original phrase, source line number, character range, explanation, and an improvement suggestion.

```python
from requirementlint import check_vague_wording, parse_requirements

text = "The application should load quickly."
for requirement in parse_requirements(text):
    for finding in check_vague_wording(requirement):
        print(f"Line {finding.line_number} [{finding.rule_id}]: {finding.phrase}")
        print(finding.explanation)
        print(finding.suggestion)
```

Output:

```text
Line 1 [RL001]: quickly
The required speed is not measurable from 'quickly' alone.
Specify a time limit and the conditions under which it will be tested.
```

Finding offsets are zero-based positions within the original line. The end position is exclusive: `requirement.text[finding.start:finding.end]` returns the matched phrase. These positions support future highlighting.

### Current rule limitations

- This is a small phrase-based rule, not a semantic assessment. It does not detect every form of ambiguity or infer whether nearby text already defines a measurable target.
- Paired straight or curly double quotes mark literal text to skip, avoiding warnings on labels such as `"Quickly"`. This heuristic also skips whole requirements enclosed in those quotes. Single quotes, escaped quotes, and nested quotations are not handled specially.
- Only the three listed spellings are supported. Quantity and missing-performance-criteria checks are not implemented yet.
- Suggestions ask for stakeholder-defined criteria; they do not invent thresholds or rewrite requirements.

## Tests

```sh
python -m unittest discover -s tests -v
```

The tests cover input parsing, token boundaries and source positions, contractions, decimal numbers, warning explanations and locations, case handling, repeated matches, word boundaries, quoted labels, clear requirements, and the parser-to-rule workflow.

## Planned features

- Accept pasted English requirements, initially one requirement per line.
- Highlight potentially vague wording and imprecise quantities.
- Flag selected performance statements that lack measurable criteria.
- Explain each warning and prompt the user to make the requirement testable.
- Keep the original wording unchanged for human review.

A warning is a reason to review a requirement, not proof that it is wrong. Finding no warning does not prove that a requirement is complete or correct. Not every requirement needs a number.

## How it will work

1. **Read input:** keep each requirement's text and line number.
2. **Process text:** identify words and phrases while keeping their original positions for highlighting.
3. **Apply rules:** look for a small set of warning patterns.
4. **Collect findings:** record the phrase, warning category, explanation, and improvement prompt.
5. **Display results:** show findings beside the original requirement in a simple interface.

Later, a classical machine-learning classifier will be evaluated alongside the rule baseline. Its requirement-level prediction will be separate from the rule-based phrase explanations.

## Planned tools

Python and spaCy are used for text processing and English tokenization. scikit-learn is planned for TF-IDF and classification, and Streamlit for the interface.

## Development roadmap

1. **Scope and examples:** define warning categories and expected results.
2. **Input processing:** read one requirement per line, tokenize English text, and preserve source locations.
3. **Vague wording detection:** identify selected vague terms, explain findings, and test false-positive cases.
4. **Rule baseline:** add quantity and performance checks with documented limitations.
5. **Classifier evaluation:** prepare labelled data, reserve unseen test examples, and compare rules with TF-IDF plus Logistic Regression or Naive Bayes using precision, recall, and F1.
6. **Interface and usage:** provide text input, highlighted findings, usage documentation, and end-to-end validation.

## Outside the first version

Accounts, a database, document uploads, languages other than English, automatic rewriting, and generative-AI services are outside the initial scope.
