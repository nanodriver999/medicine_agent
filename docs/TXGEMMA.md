# Optional TxGemma-2B-Predict adapter

Reference: https://huggingface.co/google/txgemma-2b-predict

Use the **official** `tdc_prompts.json` template for a supported TDC task.
For `BBB_Martins` the model card shows multiple-choice labels
`(A) does not cross the BBB` and `(B) crosses the BBB`.
For inference, use a model generation function that returns **only the newly
generated continuation**, not the original prompt or a natural-language
explanation. `amo.txgemma.predict` then validates the continuation.

Classification output accepts only exactly `A`, `B`, `(A)`, `(B)`
(case-insensitive, with surrounding whitespace). Ambiguous output is
`parse_error`. These labels are **not calibrated probabilities**.
Regression output accepts only a finite standalone number with no surrounding
explanatory text. Do not mix classifications with ADMET regression outputs
on an interchangeable numerical scale.

This PR implements task schema, prompt formatting and strict parsers.
It does **not** load/download TxGemma weights, run Hugging Face inference,
or claim prediction accuracy. That requires an opt-in GPU / Colab evaluation,
verified supported task, pinned model revision and 10–30 molecule smoke test.
