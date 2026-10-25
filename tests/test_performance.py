"""Check targeted performance guidance without loading or training a model."""

import unittest

from requirementlint.parser import Requirement
from requirementlint.performance import check_performance_criteria


class PerformanceCriteriaTests(unittest.TestCase):
    def test_low_latency_word_forms_have_consistent_findings(self):
        for adjective in ("low", "lower", "lowest"):
            for metric in ("latency", "latencies", "response time", "response times"):
                phrase = f"{adjective} {metric}"
                text = f"The app must perform under {phrase}"
                with self.subTest(text=text):
                    findings = check_performance_criteria(Requirement(text, 2))
                    self.assertEqual(len(findings), 1)
                    finding = findings[0]
                    self.assertEqual(finding.phrase, phrase)
                    self.assertEqual(text[finding.start:finding.end], phrase)
                    self.assertEqual(finding.line_number, 2)
                    expected_metric = "latency" if metric.startswith("latenc") else "response time"
                    self.assertIn(f"maximum {expected_metric}", finding.suggestion)

    def test_plural_predicates_and_comparatives_keep_original_spans(self):
        for text, phrase in (
            ("Latencies should be lower.", "lower"),
            ("Response times must remain lowest.", "lowest"),
            ("  Latencies must be LOWER than before.", "LOWER"),
        ):
            with self.subTest(text=text):
                findings = check_performance_criteria(Requirement(text, 1))
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].phrase, phrase)
                self.assertEqual(text[findings[0].start:findings[0].end], phrase)

    def test_morphological_variants_respect_quotes_bounds_and_word_boundaries(self):
        for text in (
            'Display "lower latencies" on the settings screen.',
            'Display “lowest response times” on the settings screen.',
            "The app must maintain lower latencies under 100 ms.",
            "Latencies must be lower than 100 milliseconds.",
            "The app must provide lower latency than 0.5 seconds.",
            "Response times must be lowest (at most 100 ms).",
            "Record the lowercase latency field.",
            "Show low latencyish labels.",
        ):
            with self.subTest(text=text):
                self.assertEqual(check_performance_criteria(Requirement(text, 1)), [])

    def test_unquantified_comparisons_still_need_review(self):
        for text in (
            "The app must have lower latencies than before.",
            "The app must have lower latency than the previous version.",
            "Latencies must be lower for 100 users.",
            "Latencies must be lower than 100 requests per second.",
        ):
            with self.subTest(text=text):
                self.assertEqual(len(check_performance_criteria(Requirement(text, 1))), 1)

    def test_vague_speed_and_latency_get_actionable_guidance(self):
        for text, phrase in (
            ("The page should load fast.", "fast"),
            ("Latency should be very low.", "very low"),
        ):
            with self.subTest(text=text):
                findings = check_performance_criteria(Requirement(text, 1))
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].phrase, phrase)
                self.assertEqual(findings[0].rule_id, "RL003")
                self.assertEqual(findings[0].category, "missing-performance-criteria")
                self.assertIn("test conditions", findings[0].suggestion)

    def test_supported_actions_and_common_intervening_objects(self):
        cases = (
            "The API should respond fast.",
            "The service must process all requests fast.",
            "Save the document fast.",
            "The application must start fast.",
            "The browser should render the page fast.",
            "The viewer loads images very fast.",
            "The service must have low latency.",
            "The system should process requests with low latency.",
            "The response time must be low.",
            "Response times should remain very low.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(len(check_performance_criteria(Requirement(text, 1))), 1)

    def test_attached_upper_time_limits_suppress_the_warning(self):
        for bound in (
            "within 2 seconds", "under 200 ms", "at most 100 milliseconds",
            "no more than 1 s", "<= 50 ms", "≤ 50 ms", "within 0.5 seconds",
        ):
            for text in (
                f"The page must load fast {bound}.",
                f"Latency should be very low ({bound}).",
                f"The service must have low latency, {bound}.",
            ):
                with self.subTest(text=text):
                    self.assertEqual(check_performance_criteria(Requirement(text, 1)), [])

    def test_precise_counterparts_do_not_need_subjective_words(self):
        for text in (
            "The page must load within 2 seconds under workload W1.",
            "Latency must be at most 100 milliseconds under workload W2.",
            "The service must respond in under 200 ms.",
        ):
            with self.subTest(text=text):
                self.assertEqual(check_performance_criteria(Requirement(text, 1)), [])

    def test_quoted_labels_and_unrelated_adjectives_are_skipped(self):
        for text in (
            'Display "low latency" on the settings screen.',
            'Display “Latency should be very low” on the settings screen.',
            'The label must read "Load fast".',
            "Load the Fast preset.",
            "Selecting the Fast preset must change the preview resolution.",
            "Show a warning when stock is low.",
            "The queue should have high throughput.",
            "The page must load quickly.",
        ):
            with self.subTest(text=text):
                self.assertEqual(check_performance_criteria(Requirement(text, 1)), [])

    def test_unrelated_counts_deadlines_and_lower_limits_do_not_hide_warning(self):
        for text in (
            "The page should load fast for 200 users.",
            "Latency should be low for 100 requests per second.",
            "The page should load fast; logs must be saved within 2 seconds.",
            "The page should load fast and backups must finish within 2 seconds.",
            "The page should load fast, with cache expiry under 2 seconds.",
            "Latency should be low. The retry timeout must be under 2 seconds.",
            "Latency should be low with startup time under 2 seconds.",
            "The page should load fast within 200 users.",
            "The page should load fast after 2 seconds.",
            "Latency should be low, at least 100 ms.",
        ):
            with self.subTest(text=text):
                self.assertEqual(len(check_performance_criteria(Requirement(text, 1))), 1)

    def test_offsets_line_number_and_original_case_are_preserved(self):
        text = "  Café: the page should load FAST. Latency should be Very Low."
        findings = check_performance_criteria(Requirement(text, 7))
        self.assertEqual([finding.phrase for finding in findings], ["FAST", "Very Low"])
        for finding in findings:
            self.assertEqual(finding.line_number, 7)
            self.assertEqual(text[finding.start:finding.end], finding.phrase)
            self.assertEqual(finding.start, text.index(finding.phrase))

    def test_quoted_phrase_does_not_hide_unquoted_finding(self):
        text = 'Display "low latency"; the page should load fast.'
        findings = check_performance_criteria(Requirement(text, 1))
        self.assertEqual([finding.phrase for finding in findings], ["fast"])

    def test_bound_for_one_action_does_not_suppress_another(self):
        text = "Load fast within 2 seconds; save the file fast."
        findings = check_performance_criteria(Requirement(text, 1))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].start, text.rindex("fast"))

    def test_action_and_latency_phrases_have_separate_nonoverlapping_spans(self):
        text = "The service should process fast with low latency."
        findings = check_performance_criteria(Requirement(text, 1))
        self.assertEqual([finding.phrase for finding in findings], ["fast", "low latency"])
        self.assertLessEqual(findings[0].end, findings[1].start)


if __name__ == "__main__":
    unittest.main()
