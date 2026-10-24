# Synthetic starter dataset

These 52 English requirements were authored with AI assistance specifically for this project. They are synthetic examples, not collected user requirements, an externally validated corpus, or a research benchmark. Labels are provisional and need human review.

- `train.json`: 40 examples, 20 per class, used to learn the vocabulary, TF-IDF weights, and classifier parameters.
- `test.json`: 12 different examples, 6 per class, reserved for evaluation and never passed to `fit`.

## Label definitions

- `vague`: contains an undefined subjective quality, quantity, or acceptance criterion that calls for clarification.
- `clear`: relatively explicit for the purpose of this wording demonstration. This does not establish completeness, feasibility, or correctness. Referenced workloads such as W1 are assumed to be specified elsewhere.

Labels were assigned from these definitions, not generated from the implemented rules. Some examples deliberately contain numbers but remain vague, while others describe testable behavior without numbers. Literal UI text can contain a vague word without making the behavior vague.

## Evaluation limits

The files were separated manually. The training script checks for exact duplicates after normalizing case and whitespace, but this does not eliminate shared writing style, related concepts, or semantic overlap. Both files come from the same synthetic authoring process. Results on 12 examples will be unstable and do not establish real-world accuracy.

Keep test examples out of training and vocabulary fitting. Repeatedly changing the model based on these test results turns this set into development data; obtain a fresh independent test set before reporting final performance.

Further evaluation requires requirements from appropriately licensed sources or consenting contributors, documented provenance, independently reviewed labels, and splits grouped by source or template. Starter results are demonstration results, not a validated accuracy claim.
