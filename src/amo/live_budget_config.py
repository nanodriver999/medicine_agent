"""Fail-closed configuration for live LLM currency reservations."""
from __future__ import annotations
from .currency_budget import CurrencyBudget
from .llm_usage import Pricing


def parse_live_llm_budget(env):
    required=("LLM_INPUT_UNITS_PER_MILLION","LLM_OUTPUT_UNITS_PER_MILLION",
              "LLM_PRICING_CURRENCY","LLM_MAX_ROUND_CURRENCY_COST",
              "LLM_CURRENCY_BUDGET")
    if any(not env.get(key) for key in required):
        raise ValueError("missing verified LLM pricing or reservation configuration")
    pricing=Pricing(float(env[required[0]]),float(env[required[1]]))
    budget=CurrencyBudget(float(env[required[4]]),env[required[2]])
    ceiling=float(env[required[3]])
    # A zero reservation is not a meaningful upper bound for a billable call.
    if not (0 < ceiling <= budget.limit):
        raise ValueError("invalid round currency ceiling")
    return pricing,budget,ceiling
