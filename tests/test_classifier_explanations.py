"""Check that feature explanations account for the fitted classifier score."""

from copy import deepcopy
import unittest

from requirementlint.classifier import create_pipeline, explain_predictions


class ClassifierExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A small in-memory fixture; never reads or modifies the saved model.
        cls.model = create_pipeline()
        cls.model.fit(
            [
                "vague uncertain", "uncertain ambiguous", "vague subjective",
                "clear exact", "exact defined", "clear measurable",
            ],
            ["vague", "vague", "vague", "clear", "clear", "clear"],
        )

    def test_labels_match_pipeline_and_all_score_parts_add_up(self):
        texts = ["vague uncertain", "clear exact", "vague exact"]
        explanations = explain_predictions(self.model, texts, top_n=1)
        expected_labels = self.model.predict(texts).tolist()
        expected_scores = self.model.decision_function(texts)
        self.assertEqual([item.label for item in explanations], expected_labels)
        for explanation, expected_score in zip(explanations, expected_scores):
            total = (
                explanation.intercept
                + sum(item.score for item in explanation.contributions)
                + explanation.remaining_contribution
            )
            self.assertAlmostEqual(total, float(expected_score), places=10)
            self.assertAlmostEqual(explanation.decision_score, float(expected_score), places=10)
            self.assertLessEqual(len(explanation.contributions), 1)

    def test_features_come_from_input_and_include_both_directions(self):
        explanation = explain_predictions(self.model, ["vague exact"], top_n=10)[0]
        self.assertEqual({item.feature for item in explanation.contributions}, {"vague", "exact"})
        self.assertEqual({item.supports for item in explanation.contributions}, {"clear", "vague"})
        magnitudes = [abs(item.score) for item in explanation.contributions]
        self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))

    def test_unknown_vocabulary_has_no_invented_feature_explanation(self):
        explanation = explain_predictions(self.model, ["zzzxxyy"])[0]
        self.assertEqual(explanation.known_feature_count, 0)
        self.assertEqual(explanation.contributions, [])
        self.assertEqual(explanation.remaining_contribution, 0)
        self.assertAlmostEqual(explanation.decision_score, explanation.intercept)

    def test_class_order_does_not_reverse_displayed_meaning(self):
        reversed_model = deepcopy(self.model)
        classifier = reversed_model.named_steps["classifier"]
        classifier.classes_ = classifier.classes_[::-1]
        classifier.coef_ *= -1
        classifier.intercept_ *= -1
        text = ["vague uncertain"]
        original = explain_predictions(self.model, text)[0]
        reversed_explanation = explain_predictions(reversed_model, text)[0]
        self.assertEqual(original.label, reversed_explanation.label)
        self.assertEqual(original.contributions, reversed_explanation.contributions)
        self.assertAlmostEqual(original.decision_score, reversed_explanation.decision_score)

    def test_empty_batch_returns_no_explanations(self):
        self.assertEqual(explain_predictions(self.model, []), [])

    def test_nonpositive_feature_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            explain_predictions(self.model, ["vague"], top_n=0)


if __name__ == "__main__":
    unittest.main()
