# RequirementLint

RequirementLint will help people review software requirements written in English. It will flag wording that may be vague or difficult to test, explain the issue, and suggest what information to add.

For example, "The application should load quickly" does not tell a tester how long loading may take. The tool will ask for a time limit and test conditions. The stakeholder decides the actual target.

## Project status

Early development: line-based input parsing is implemented and tested. Warning detection, classification, and the interface are planned.

See [example requirements](docs/examples.md) for the proposed warnings and expected behavior.

## Run the parser

Requires Python 3.10 or newer. The current implementation uses only the Python standard library; no additional packages are required. Run commands from the repository root.

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

## Tests

```sh
python -m unittest discover -s tests -v
```

The tests cover blank input, ordering, source line numbers, unchanged text, common line endings, and multiple sentences on a single line.

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

Python for the analysis, NLTK or spaCy for basic NLP, scikit-learn for TF-IDF and classification, and Streamlit for the interface. These technology choices are provisional.

## Development roadmap

1. **Scope and examples:** define warning categories and expected results.
2. **Input processing:** read one requirement per line and preserve its location.
3. **Vague wording detection:** identify selected vague terms, explain findings, and test false-positive cases.
4. **Rule baseline:** add quantity and performance checks with documented limitations.
5. **Classifier evaluation:** prepare labelled data, reserve unseen test examples, and compare rules with TF-IDF plus Logistic Regression or Naive Bayes using precision, recall, and F1.
6. **Interface and usage:** provide text input, highlighted findings, usage documentation, and end-to-end validation.

## Outside the first version

Accounts, a database, document uploads, languages other than English, automatic rewriting, and generative-AI services are outside the initial scope.
