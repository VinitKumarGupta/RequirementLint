"""Check warning locations, explanations, and common false-positive cases."""

import unittest

from requirementlint import (
    Requirement, check_imprecise_quantity_phrases, check_vague_wording, parse_requirements,
)


class VagueWordingTests(unittest.TestCase):
    def test_supported_phrases_have_actionable_guidance(self):
        cases = (
            ("The application should load quickly.", "quickly", "time limit"),
            ("The interface must be user-friendly.", "user-friendly", "user task"),
            ("The service should run efficiently.", "efficiently", "metric"),
        )
        for text, phrase, suggestion_detail in cases:
            with self.subTest(phrase=phrase):
                findings = check_vague_wording(Requirement(text, 1))
                self.assertEqual(len(findings), 1)
                finding = findings[0]
                self.assertEqual(finding.phrase, phrase)
                self.assertEqual(finding.rule_id, "RL001")
                self.assertEqual(finding.category, "vague-wording")
                self.assertTrue(finding.explanation)
                self.assertIn(suggestion_detail, finding.suggestion)

    def test_case_insensitive_match_preserves_original_text_and_offsets(self):
        requirement = Requirement("  Café: load QUICKLY!  ", 4)
        finding = check_vague_wording(requirement)[0]
        self.assertEqual((finding.start, finding.end), (13, 20))
        self.assertEqual(finding.line_number, 4)
        self.assertEqual(finding.phrase, "QUICKLY")
        self.assertEqual(requirement.text[finding.start:finding.end], "QUICKLY")
        self.assertEqual(requirement.text, "  Café: load QUICKLY!  ")

    def test_repeated_and_different_phrases_remain_in_text_order(self):
        requirement = Requirement("Quickly load efficiently, then quickly save.", 1)
        findings = check_vague_wording(requirement)
        self.assertEqual([finding.phrase for finding in findings], ["Quickly", "efficiently", "quickly"])
        self.assertEqual([finding.start for finding in findings], [0, 13, 31])

    def test_does_not_match_inside_larger_words(self):
        self.assertEqual(
            check_vague_wording(Requirement("quicklyish inefficiently user-friendlyness", 1)),
            [],
        )

    def test_clear_requirements_have_no_findings(self):
        cases = (
            "Under workload W1, at least 95% of dashboard loads must finish within 2 seconds.",
            "When the user selects Cancel, close the dialog without saving changes.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(check_vague_wording(Requirement(text, 1)), [])

    def test_quoted_labels_are_skipped(self):
        for label in ('"Quickly"', '“Quickly”'):
            with self.subTest(label=label):
                text = f"The system must display the label {label} on the shortcut button."
                self.assertEqual(check_vague_wording(Requirement(text, 1)), [])

    def test_quoted_label_does_not_hide_unquoted_warning(self):
        requirement = Requirement('Display "Quickly" and "efficiently" quickly.', 1)
        findings = check_vague_wording(requirement)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].start, requirement.text.rindex("quickly"))

    def test_unclosed_quote_does_not_hide_warning(self):
        findings = check_vague_wording(Requirement('Load "quickly.', 1))
        self.assertEqual([finding.phrase for finding in findings], ["quickly"])

    def test_parser_and_rule_preserve_line_numbers_across_blank_lines(self):
        text = "Save changes.\r\n\r\nLoad quickly."
        findings = [
            finding
            for requirement in parse_requirements(text)
            for finding in check_vague_wording(requirement)
        ]
        self.assertEqual(len(findings), 1)
        self.assertEqual((findings[0].line_number, findings[0].start, findings[0].end), (3, 5, 12))


class ImpreciseQuantityPhraseTests(unittest.TestCase):
    def test_supported_phrases_have_findings_with_original_spans(self):
        cases = (
            ("The system must process a large volume of records.", "large volume"),
            ("The service should support high capacity.", "high capacity"),
            ("The report contains a significant amount of data.", "significant amount"),
        )
        for text, phrase in cases:
            with self.subTest(phrase=phrase):
                finding = check_imprecise_quantity_phrases(Requirement(text, 3))[0]
                self.assertEqual(finding.rule_id, "RL004")
                self.assertEqual(finding.category, "imprecise-quantity-phrase")
                self.assertEqual(finding.phrase, phrase)
                self.assertEqual(finding.line_number, 3)
                self.assertEqual(text[finding.start:finding.end], phrase)
                self.assertTrue(finding.explanation)
                self.assertTrue(finding.suggestion)

    def test_quoted_phrase_is_skipped(self):
        text = 'Display the label "large volume" in the report.'
        self.assertEqual(
            check_imprecise_quantity_phrases(Requirement(text, 1)),
            [],
        )


if __name__ == "__main__":
    unittest.main()
