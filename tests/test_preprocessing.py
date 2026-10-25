"""Verify meaningful token boundaries and source locations for NLP input."""

import unittest

from requirementlint import Requirement, parse_requirements
from requirementlint.preprocessing import mask_quoted_strings, tokenize_requirement


class TokenizeRequirementTests(unittest.TestCase):
    def test_masks_straight_and_curly_quoted_strings(self):
        text = 'Show "Save 50% <now>" and “Retry > 3 times”.'
        self.assertEqual(
            mask_quoted_strings(text),
            "Show LITERAL_STRING and LITERAL_STRING.",
        )

    def test_leaves_unquoted_and_unmatched_text_unchanged(self):
        text = 'Set limit to 50%; label is "not closed.'
        self.assertEqual(mask_quoted_strings(text), text)

    def test_separates_punctuation_from_words(self):
        tokens = tokenize_requirement(Requirement("Load quickly.", 1))
        self.assertEqual([token.text for token in tokens], ["Load", "quickly", "."])
        self.assertEqual([(token.start, token.end) for token in tokens], [(0, 4), (5, 12), (12, 13)])

    def test_splits_contraction_without_discarding_negation(self):
        tokens = tokenize_requirement(Requirement("Don't save changes.", 1))
        self.assertEqual([token.text for token in tokens], ["Do", "n't", "save", "changes", "."])

    def test_preserves_decimal_and_units(self):
        tokens = tokenize_requirement(Requirement("Respond within 2.5 seconds.", 1))
        self.assertEqual([token.text for token in tokens], ["Respond", "within", "2.5", "seconds", "."])

    def test_preserves_case_unicode_and_offsets_despite_extra_whitespace(self):
        requirement = Requirement("  Café\tloads  QUICKLY.  ", 7)
        tokens = tokenize_requirement(requirement)
        self.assertEqual([token.text for token in tokens], ["Café", "loads", "QUICKLY", "."])
        self.assertEqual(tokens[0].start, 2)
        self.assertEqual(tokens[2].start, 14)
        for token in tokens:
            self.assertEqual(token.line_number, 7)
            self.assertEqual(requirement.text[token.start:token.end], token.text)
        self.assertEqual(requirement.text, "  Café\tloads  QUICKLY.  ")

    def test_preserves_quotes_and_hyphenated_phrase_parts(self):
        tokens = tokenize_requirement(Requirement('Display "user-friendly".', 1))
        self.assertEqual(
            [token.text for token in tokens],
            ["Display", '"', "user", "-", "friendly", '"', "."],
        )

    def test_empty_or_whitespace_input_has_no_tokens(self):
        for text in ("", "  ", "\t  "):
            with self.subTest(text=text):
                self.assertEqual(tokenize_requirement(Requirement(text, 1)), [])

    def test_parser_to_tokenizer_keeps_source_line_numbers(self):
        requirements = parse_requirements("Save changes.\r\n\r\nLoad quickly.")
        tokens = tokenize_requirement(requirements[1])
        self.assertEqual([token.text for token in tokens], ["Load", "quickly", "."])
        self.assertTrue(all(token.line_number == 3 for token in tokens))
        self.assertEqual(tokens[0].start, 0)


if __name__ == "__main__":
    unittest.main()
