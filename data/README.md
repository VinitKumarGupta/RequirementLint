# Synthetic requirement dataset

Version 2 contains 252 English requirements authored with AI assistance specifically for this project. They are synthetic examples, not collected user requirements, an externally validated corpus, or a research benchmark. No third-party dataset was imported. Labels were assigned during authoring and remain provisional pending independent human review.

| File | Examples | Clear | Vague | Purpose |
| --- | ---: | ---: | ---: | --- |
| `train.json` | 200 | 100 | 100 | Fit the vocabulary, TF-IDF weights, and classifier parameters |
| `dev.json` | 12 | 6 | 6 | Inspect errors and guide development |
| `test.json` | 40 | 20 | 20 | Reserved evaluation after development decisions are settled |

The original 40 training examples are retained. The additional 160 examples cover eight areas: performance, usability, security, reliability, data handling, integrations, accessibility, and functional behavior. Each added area contains 10 clear and 10 vague examples.

The original 12-example `test.json` is preserved as `dev.json`, with its text and labels unchanged. Its results had already been inspected to guide development, so it is no longer treated as a final test set. The new 40-example `test.json` contains different scenarios. Related clear/vague scenario pairs in the new test set are kept together in that set.

## Label definitions

- `vague`: contains an undefined subjective quality, quantity, condition, or acceptance criterion that calls for clarification. For example, an undefined "appropriate duration" cannot be tested consistently.
- `clear`: provides an observable behavior or an explicit criterion for this wording demonstration. This does not establish completeness, feasibility, correctness, or compliance. Referenced workloads, devices, and protocols such as W1, P1, and U1 are assumed to be specified elsewhere.

Labels were assigned from these definitions, not generated from the implemented rules or classifier. Examples deliberately include:

- Numbers inside vague statements, such as a specified number of icons described only as "self-explanatory".
- Clear functional behavior without numerical thresholds.
- Literal UI text containing words that can otherwise be vague.
- Explicit definitions of terms such as "stale".
- Both clear and vague statements using "should", so the modal verb alone does not determine the label.

Quantities and technical criteria are illustrative scenario targets, not recommendations for real systems. During label review, assess whether the wording supplies an observable outcome; do not relabel an example merely because the current classifier disagrees. Record disputed interpretations before changing labels.

## Evaluation limits

The files were separated manually. The training script checks example structure, labels, empty text, within-file duplicates, and overlap across all three files after normalizing case and whitespace. It prints actual counts at runtime. These checks do not detect paraphrases or eliminate shared writing style, related concepts, or semantic overlap. All three splits come from the same synthetic authoring process; the new test set is not independently authored or externally validated.

Normal training fits only `train.json` and reports metrics on `dev.json`. The test file is read for duplicate and label validation, but its metrics are computed only with `--evaluate-test`. Neither development nor test text is used to fit the vocabulary or classifier.

The 12 development examples are small and already familiar. Improvements there may reflect adaptation to those examples. Do not copy the missed development sentence into training. Evaluate the reserved set after settling model/data choices; repeated tuning against its results makes it development data as well. A fresh, independently labelled test set is preferable before making broader performance claims.

Further evaluation requires requirements from appropriately licensed sources or consenting contributors, documented provenance, independently reviewed labels, and splits grouped by source or template. Starter results are demonstration results, not a validated accuracy claim.
