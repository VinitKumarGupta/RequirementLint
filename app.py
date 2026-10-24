"""Streamlit interface for reviewing English software requirements."""

from html import escape

import streamlit as st

from requirementlint import Finding, check_imprecise_quantity, check_vague_wording, parse_requirements
from requirementlint.preprocessing import tokenize_requirement
from requirementlint.classifier import LABEL_NAMES, MODEL_PATH, load_model


SAMPLE_REQUIREMENTS = (
    "The application should load quickly.\n"
    "The interface must be user-friendly.\n"
    "The service should process requests efficiently.\n"
    "The system must support many users.\n"
    "The system must support 100 concurrent users.\n"
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
    st.write("Find potentially vague wording and make software requirements easier to test.")
    st.caption("English requirements · One requirement per line")

    model = None
    if MODEL_PATH.exists():
        try:
            model = cached_model(MODEL_PATH.stat().st_mtime_ns)
        except (OSError, ValueError, EOFError, ImportError, AttributeError):
            st.warning("The local classifier could not be loaded. Retrain it using the README instructions.")
    if model is None:
        st.info("Rule analysis is available. Train the starter model using the README instructions to enable ML predictions.")
    else:
        st.caption("ML demo: trained on a small synthetic dataset. Predictions may disagree with the rules.")

    with st.form("requirements_form"):
        text = st.text_area("Requirements", value=SAMPLE_REQUIREMENTS, height=200)
        submitted = st.form_submit_button("Analyze", type="primary")

    st.caption(
        "Current checks cover vague wording (quickly, user-friendly, efficiently) "
        "and imprecise quantities (many, several, few). "
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
            findings.extend(check_imprecise_quantity(requirement, tokens))
            findings.sort(key=lambda finding: finding.start)
            results.append((requirement, findings))

        predictions = model.predict([requirement.text for requirement in requirements]) if model is not None else None

    requirement_count, warning_count = st.columns(2)
    requirement_count.metric("Requirements", len(results))
    warning_count.metric("Warnings", sum(len(findings) for _, findings in results))

    for index, (requirement, findings) in enumerate(results):
        st.subheader(f"Line {requirement.line_number}")
        st.markdown(highlight_findings(requirement.text, findings), unsafe_allow_html=True)

        if predictions is not None:
            st.write(f"**ML prediction:** {LABEL_NAMES[predictions[index]]}")
            st.caption("Whole-requirement classification. Highlighted spans and suggestions below come from rules.")

        for finding in findings:
            st.caption(finding.category.replace("-", " ").capitalize())
            st.warning(f"{finding.phrase}: {finding.explanation}")
            st.write(f"Suggestion: {finding.suggestion}")
        if not findings:
            st.info("No warnings from the current checks.")

if __name__ == "__main__":
    main()
