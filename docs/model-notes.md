# Model method and limitations

RequirementLint combines lexical checks with a supervised text classifier. The Streamlit interface presents one review status per requirement; training diagnostics and model internals are kept out of the normal review flow.

## Classifier

spaCy tokenizes the input. TF-IDF represents individual words and adjacent word pairs, and Logistic Regression predicts `clear` or `vague`. This baseline learns word associations. It does not explicitly model grammatical relationships, interpret units and thresholds, or verify that a requirement is complete.

The training set contains 200 AI-assisted synthetic examples. Many vague examples are short statements using `should`, while clear examples often contain conditional clauses or numeric limits. Such patterns can become shortcuts: words such as `should` or `be` may influence a prediction without identifying the actual wording issue. A correct label on one sentence does not establish sound reasoning or general accuracy.

Improvement should prioritize matched clear/vague examples with similar subjects, modal verbs, and sentence structures. Include short clear requirements, longer vague requirements, literal UI labels, and measurable versus unmeasurable versions of the same scenario. Keep related variants in the same data split. Add independently reviewed examples for evaluation rather than tuning to the already inspected test results.

See [dataset provenance](../data/README.md) for labelling and split limitations. Synthetic evaluation scores do not establish real-world accuracy.

## Feature contributions

The `explain_predictions` helper uses the saved model's coefficients and the input's TF-IDF values:

```text
feature contribution = TF-IDF value for this input * learned coefficient
final decision score = intercept + sum of all feature contributions
```

Scores are oriented so positive values favor `vague` and negative values favor `clear`, using the stored class order. An exact zero follows scikit-learn's tie handling, selecting the first stored class (`clear` in the standard pipeline). These scores are not probabilities or percentages.

The helper returns up to five present features with the largest absolute contributions, including features opposing the label. It retains the intercept and the combined contribution of omitted features so the full decision score can be reconstructed. Normalized word pairs need not be contiguous literal phrases in the source text.

Contributions explain a model calculation, not why a requirement is objectively vague. They must not be used as phrase-level defects or rewrite recommendations. The helper uses the existing model without retraining; the label still comes from scikit-learn's `predict` method. See [Logistic Regression coefficients and decision scores](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.LogisticRegression.html).

## Review status

- A rule finding or a `vague` model prediction produces **Needs review**.
- If no input features are recognized by the model, the requirement also needs review; an intercept-only decision is not useful evidence of clarity.
- Otherwise the app displays **No issues detected**, without asserting that the requirement is complete or correct.
- With no model available, only the rule checks contribute, and the interface indicates that reduced coverage.

Highlights and specific improvement guidance come from matched checks. Model-only flags receive general guidance because the baseline cannot reliably diagnose an exact defect. The combined review status has not been evaluated as a separate classifier. Presentation changes and additional checks do not establish improved model accuracy.
