"""Opt-in real Strands agent + ADMET-AI orchestration.

Default CI does not have an LLM endpoint or ADMET model weights. A fake driver
can verify tool contracts, but cannot establish real agent effectiveness.
"""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
from typing import Callable

from .admet import ADMETAdapter, Endpoint
from .agent_policy import EvaluationSession, run_strands_round
from .core import Budget, descriptors, pareto_front, prepare
from .objectives import check_constraints
from .llm_usage import LLMUsageLedger, Pricing
from .total_cost import reconcile_costs
from .currency_budget import CurrencyBudget
from .live_budget_config import parse_live_llm_budget


def live_agent_run(rows: list[dict], endpoint: Endpoint, *, budget_units: int = 10,
                   adapter: ADMETAdapter | None = None,
                   driver: Callable[[EvaluationSession], dict] | None = None) -> dict:
    if budget_units < 0:
        raise ValueError("negative budget")
    prepared = prepare(rows)
    scored = [{"molecule_id": r["molecule_id"], **descriptors(r["smiles"])}
              for r in prepared]
    eligible = [r for r in scored if check_constraints(r)["passes"]]
    if len({r["molecule_id"] for r in eligible}) != len(eligible):
        raise ValueError("duplicate molecule_id is unsafe for tool selection")
    if adapter is None:
        adapter = ADMETAdapter(endpoint)

    def evaluate(smi: str, tool: str, task: str):
        if tool != "admet_ai" or task != endpoint.name:
            raise ValueError("unregistered endpoint")
        return adapter.evaluate(smi)

    session = EvaluationSession(
        {r["molecule_id"]: r["smiles"] for r in eligible},
        evaluate, {"admet_ai": {endpoint.name}},
        {"admet_ai": endpoint.cost_units * adapter.max_attempts},
        Budget(endpoint.cost_units * budget_units, budget_units))
    if driver is None:
        model_id = os.getenv("LLM_MODEL")
        api_key = os.getenv("LLM_API_KEY")
        if not model_id or not api_key:
            raise ValueError("LLM_MODEL and LLM_API_KEY must be configured")
        # Validate budget assumptions *before* initializing a remote model SDK.
        pricing, currency_budget, max_round = parse_live_llm_budget(os.environ)
        from strands.models.openai import OpenAIModel
        client_args = {"api_key": api_key, "timeout": 30.0}
        if os.getenv("LLM_BASE_URL"):
            client_args["base_url"] = os.environ["LLM_BASE_URL"]
        model = OpenAIModel(model_id=model_id, client_args=client_args,
                            params={"temperature": 0, "max_tokens": 2048})
        ledger = LLMUsageLedger(pricing, model_id)
        driver = lambda current: run_strands_round(
            current, model, usage_ledger=ledger, currency_budget=currency_budget,
            maximum_llm_currency_cost=max_round)
    driver_result = driver(session)
    by_id = {r["molecule_id"]: r for r in eligible}
    evaluated = []
    for event in session.events:
        if event["kind"] != "evaluated":
            continue
        row = by_id[event["molecule_id"]]
        evaluated.append({**row, endpoint.name: event["result"]["value"],
                          "admet_status": "ok", "admet_source": "admet_ai"})
    frontier = pareto_front(evaluated, {"qed": "max", endpoint.name: endpoint.direction})
    llm_cost = driver_result.get("llm_cost", {"usage_status": "missing_pricing_configuration"})
    currency = os.getenv("LLM_PRICING_CURRENCY")
    unit_rate = os.getenv("EVALUATION_CURRENCY_PER_COST_UNIT")
    total_cost = reconcile_costs(
        evaluation_cost_units=session.budget.used_cost_units,
        llm_cost={**llm_cost, "currency": currency} if isinstance(llm_cost, dict) else {},
        currency_per_evaluation_unit=float(unit_rate) if unit_rate is not None else None,
        currency=currency)
    return {"status": driver_result.get("status", "unknown"), "mode": "live-agent",
            "endpoint": endpoint.__dict__, "eligible": len(eligible),
            "screened": len(scored), "evaluated": evaluated,
            "pareto": frontier, "events": list(session.events),
            "budget": session.budget.__dict__,
            "model_id": os.getenv("LLM_MODEL", "injected-test-driver"),
            "token_usage": driver_result.get("token_usage", {"status": "missing_provider_usage"}),
            "llm_cost": llm_cost,
            "total_cost": total_cost,
            "llm_currency_budget": driver_result.get("currency_budget"),
            "warnings": ["Predicted ADMET != experimental observation.",
                         "LLM token usage not yet in cost budget; do NOT compare this mode fairly to fixed/rules."]}


def export_live_agent_run(report: dict, out: str | Path) -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent_run.json").write_text(json.dumps(report, indent=2, allow_nan=False),
                                        encoding="utf-8")
    with (out / "events.jsonl").open("w", encoding="utf-8") as fp:
        for event in report["events"]:
            fp.write(json.dumps(event, allow_nan=False) + "\n")
    for name, key in (("evaluated.csv", "evaluated"), ("pareto.csv", "pareto")):
        data = report[key]
        with (out / name).open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(data[0]) if data else ["molecule_id"])
            writer.writeheader()
            writer.writerows(data)
