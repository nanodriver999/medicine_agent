"""Provider-reported LLM usage ledger, without assumed prices or token counts."""
from __future__ import annotations
from dataclasses import dataclass, field
import math

@dataclass(frozen=True)
class Pricing:
    input_units_per_million: float
    output_units_per_million: float
    def __post_init__(self):
        if any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or v < 0
               for v in (self.input_units_per_million, self.output_units_per_million)):
            raise ValueError("invalid pricing")

@dataclass
class LLMUsageLedger:
    pricing: Pricing
    model_revision: str
    entries: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.model_revision, str) or not self.model_revision.strip():
            raise ValueError("model revision required")

    def add(self, *, input_tokens: int, output_tokens: int, source: str) -> dict:
        if any(isinstance(n, bool) or not isinstance(n,int) or n < 0
               for n in (input_tokens, output_tokens)):
            raise ValueError("token counts must be nonnegative integers")
        if source != "provider_usage":
            raise ValueError("only provider-reported usage is accepted")
        cost = (input_tokens * self.pricing.input_units_per_million +
                output_tokens * self.pricing.output_units_per_million) / 1_000_000
        entry = {"input_tokens": input_tokens, "output_tokens": output_tokens,
                 "cost_units": cost, "source": source,
                 "model_revision": self.model_revision}
        self.entries.append(entry)
        return entry

    def summary(self) -> dict:
        return {"llm_cost_units": sum(e["cost_units"] for e in self.entries),
                "input_tokens": sum(e["input_tokens"] for e in self.entries),
                "output_tokens": sum(e["output_tokens"] for e in self.entries),
                "usage_status": "verified" if self.entries else "missing_provider_usage",
                "model_revision": self.model_revision}
