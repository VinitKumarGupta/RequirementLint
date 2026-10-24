"""Streamlit interface for reviewing English software requirements."""

from dataclasses import asdict
from html import escape

import streamlit as st

from requirementlint import Finding, check_vague_wording, parse_requirements
from requirementlint.preprocessing import tokenize_requirement


SAMPLE_REQUIREMENTS = (
    "The application should load quickly.\n"
    "The interface must be user-friendly.\n"
    "The service should process requests efficiently.\n"
    "When the user selects Cancel, close the dialog without saving changes."
)


def highlight_findings(text: str, findings: list[Finding]) -> str:
    """Highlight matched spans while displaying input as literal text."""
    parts = []
    cursor = 0
    for finding in sorted(findings, key=lambda item: item.start):
        parts.append(escape(text[cursor:finding.start]))
        parts.append(
            '<mark style="background-color: #ffe08a; color: #222;">'
            + escape(text[finding.start:finding.end])
            + "</mark>"
        )
        cursor = finding.end
    parts.append(escape(text[cursor:]))
    return '<div style="white-space: pre-wrap; overflow-wrap: anywhere;">' + "".join(parts) + "</div>"


def main() -> None:
    st.set_page_config(page_title="RequirementLint", page_icon="📝", layout="centered")
    st.title("RequirementLint")
    st.write("Find potentially vague wording and make software requirements easier to test.")
    st.caption("English requirements · One requirement per line")

    with st.form("requirements_form"):
        text = st.text_area("Requirements", value=SAMPLE_REQUIREMENTS, height=200)
        submitted = st.form_submit_button("Analyze", type="primary")

    st.caption(
        "Current checks cover quickly, user-friendly, and efficiently. "
        "Warnings support human review; no warning does not guarantee a clear requirement."
    )

    if not submitted:
        st.info("Edit the sample or paste your requirements, then select Analyze.")
        return

    requirements = parse_requirements(text)
    if not requirements:
        st.warning("Enter at least one requirement before analyzing.")
        return

    results = []
    with st.spinner("Analyzing requirements..."):
        for requirement in requirements:
            tokens = tokenize_requirement(requirement)
            findings = check_vague_wording(requirement)
            results.append((requirement, tokens, findings))

    requirement_count, warning_count, token_count = st.columns(3)
    requirement_count.metric("Requirements", len(results))
    warning_count.metric("Warnings", sum(len(findings) for _, _, findings in results))
    token_count.metric("Tokens", sum(len(tokens) for _, tokens, _ in results))

    for requirement, tokens, findings in results:
        st.subheader(f"Line {requirement.line_number}")
        st.markdown(highlight_findings(requirement.text, findings), unsafe_allow_html=True)

        for finding in findings:
            st.warning(f"{finding.phrase}: {finding.explanation}")
            st.write(f"Suggestion: {finding.suggestion}")
        if not findings:
            st.info("No warnings from the current checks.")

        with st.expander(f"Explore NLP tokens for line {requirement.line_number}"):
            st.caption(
                "spaCy splits the text into words and punctuation. Start and end are "
                "character positions in the original line, starting at zero; end is excluded. "
                "The current warnings come from phrase rules, not a trained classifier."
            )
            st.dataframe([asdict(token) for token in tokens], hide_index=True)


if __name__ == "__main__":
    main()
