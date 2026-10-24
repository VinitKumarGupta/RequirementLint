"""Behavior checks for line-separated requirement input."""

import unittest

from requirementlint import Requirement, parse_requirements


class ParseRequirementsTests(unittest.TestCase):
    def test_empty_or_whitespace_only_input_has_no_requirements(self):
        for text in ("", "   ", "\n\t\n", "\r\n"):
            with self.subTest(text=text):
                self.assertEqual(parse_requirements(text), [])

    def test_reads_multiple_requirements_in_order(self):
        text = "The application should load quickly.\nThe system must save changes."
        self.assertEqual(
            parse_requirements(text),
            [
                Requirement("The application should load quickly.", 1),
                Requirement("The system must save changes.", 2),
            ],
        )

    def test_blank_lines_do_not_change_original_line_numbers(self):
        text = "\nFirst requirement.\n \t\nSecond requirement.\n"
        self.assertEqual(
            parse_requirements(text),
            [Requirement("First requirement.", 2), Requirement("Second requirement.", 4)],
        )

    def test_preserves_whitespace_punctuation_and_unicode(self):
        text = '  Show the label "Café".\t '
        self.assertEqual(parse_requirements(text), [Requirement(text, 1)])

    def test_supports_common_line_endings(self):
        for separator in ("\n", "\r\n", "\r"):
            with self.subTest(separator=separator):
                text = separator.join(("First requirement.", "Second requirement.", ""))
                self.assertEqual(
                    parse_requirements(text),
                    [Requirement("First requirement.", 1), Requirement("Second requirement.", 2)],
                )

    def test_multiple_sentences_on_one_line_remain_one_requirement(self):
        text = "Save the report. Display a confirmation."
        self.assertEqual(parse_requirements(text), [Requirement(text, 1)])


if __name__ == "__main__":
    unittest.main()
