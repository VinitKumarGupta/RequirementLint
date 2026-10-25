"""Streamlit interface for reviewing English software requirements."""

from html import escape

import streamlit as st

from requirementlint import (
    Finding, check_imprecise_quantity, check_performance_criteria,
    check_vague_wording, parse_requirements,
)
from requirementlint.preprocessing import tokenize_requirement
from requirementlint.classifier import MODEL_PATH, explain_predictions, load_model


SAMPLE_REQUIREMENTS = (
    "The page should load fast.\n"
    "Latency should be very low.\n"
    "The page must load within 2 seconds for 100 concurrent users.\n"
    "When the user selects Cancel, close the dialog without saving changes."
)


@st.cache_resource
def cached_model(modified_at: int):
    """Reload the model when training changes its modification timestamp."""
    return load_model()


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
    st.write("Find unclear requirements and see what to improve.")
    st.caption("English requirements · One requirement per line")

    model = None
    if MODEL_PATH.exists():
        try:
            model = cached_model(MODEL_PATH.stat().st_mtime_ns)
        except (OSError, ValueError, EOFError, ImportError, AttributeError):
            pass
    if model is None:
        st.info("Language classification is unavailable. Basic wording checks are still available.")

    with st.form("requirements_form"):
        text = st.text_area("Requirements", value=SAMPLE_REQUIREMENTS, height=200)
        submitted = st.form_submit_button("Analyze", type="primary")

    if not submitted:
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
            findings.extend(check_imprecise_quantity(requirement, tokens))
            findings.extend(check_performance_criteria(requirement))
            findings.sort(key=lambda finding: finding.start)
            results.append((requirement, findings))

        explanations = (
            explain_predictions(model, [requirement.text for requirement in requirements])
            if model is not None else None
        )

    # A review flag is the union of rule findings, model flags, and inputs the
    # model cannot assess. It does not relabel either independent prediction.
    needs_review = [
        bool(findings) or (
            explanations is not None
            and (explanations[index].label == "vague" or explanations[index].known_feature_count == 0)
        )
        for index, (_, findings) in enumerate(results)
    ]
    summary = st.columns(2)
    summary[0].metric("Requirements", len(results))
    summary[1].metric("Need review", sum(needs_review))

    for index, (requirement, findings) in enumerate(results):
        explanation = explanations[index] if explanations is not None else None
        with st.container(border=True):
            st.markdown(f"**Line {requirement.line_number}**")
            st.markdown(highlight_findings(requirement.text, findings), unsafe_allow_html=True)
            if needs_review[index]:
                st.warning("Needs review")
            else:
                st.success("No issues detected")

            for finding in findings:
                st.write(f"**Why:** {finding.explanation}")
                st.write(f"**Improve:** {finding.suggestion}")
            if not findings and explanation is not None and explanation.known_feature_count == 0:
                st.info(
                    "There is not enough familiar wording to assess this requirement. "
                    "Review its expected behavior and acceptance criteria manually."
                )
            elif not findings and explanation is not None and explanation.label == "vague":
                st.write("**Why:** The wording may be open to interpretation; a specific issue could not be identified.")
                st.write(
                    "**Improve:** Check that the expected behavior and acceptance criteria are explicit. "
                    "Add measurable limits where relevant."
                )

    st.caption("Suggestions support human review. No issues detected does not guarantee a complete requirement.")


if __name__ == "__main__":
    main()
