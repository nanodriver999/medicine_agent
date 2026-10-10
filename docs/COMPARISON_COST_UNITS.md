# Cost units in policy comparisons

`verify_comparison` must not add symbolic ADMET evaluation budget units to provider monetary LLM charges. Each run now needs explicitly matching `evaluation_cost_basis`, `llm_cost_basis`, and `budget_cost_basis` to obtain a comparable status. These labels express the experimenter's externally validated conversion protocol; equal labels do not independently verify the conversion rate or provider invoice. Missing or mismatched labels produce `incompatible_cost_units`.
