"""Fixed and rules baseline using real or injected ADMET evaluator."""
from .core import Budget, descriptors, pareto_front, prepare
from .objectives import check_constraints
from .agent_policy import EvaluationSession
from .admet import ADMETAdapter

def run_baseline(rows, endpoint, policy, budget_units, adapter=None):
    if policy not in ("fixed", "rules"):
        raise ValueError("unsupported baseline")
    if not isinstance(budget_units, int) or isinstance(budget_units, bool) or budget_units < 0:
        raise ValueError("invalid budget")
    scored = [{"molecule_id": m["molecule_id"], **descriptors(m["smiles"])}
              for m in prepare(rows)]
    eligible = [m for m in scored if check_constraints(m)["passes"]]
    if len({m["molecule_id"] for m in eligible}) != len(eligible):
        raise ValueError("duplicate ID")
    if policy == "rules":
        eligible.sort(key=lambda m: (-m["qed"], m["molecule_id"]))
    injected = adapter is not None
    adapter = adapter or ADMETAdapter(endpoint)
    session = EvaluationSession(
        {m["molecule_id"]: m["smiles"] for m in eligible},
        lambda smiles, tool, task: adapter.evaluate(smiles),
        {"admet_ai": {endpoint.name}},
        {"admet_ai": endpoint.cost_units * adapter.max_attempts},
        Budget(endpoint.cost_units * budget_units, budget_units),
        max_actions=max(1, len(eligible)))
    for candidate in eligible:
        if not session.budget.permits(endpoint.cost_units * adapter.max_attempts):
            break
        session.evaluate(candidate["molecule_id"], "admet_ai", endpoint.name)
    lookup = {m["molecule_id"]: m for m in eligible}
    evaluated = [{**lookup[event["molecule_id"]], endpoint.name: event["result"]["value"]}
                 for event in session.events if event["kind"] == "evaluated"]
    return {"policy": policy, "evaluated": evaluated,
            "pareto": pareto_front(evaluated, {"qed": "max", endpoint.name: endpoint.direction}),
            "budget": session.budget.__dict__, "events": session.events,
            "source": "injected-adapter" if injected else "live-admet-ai"}
