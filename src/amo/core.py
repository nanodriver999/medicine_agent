"""Validated molecular descriptors, multiobjective selection, and budget enforcement.

Outputs are computational screening signals, never measured toxicity or efficacy.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import Descriptors, Crippen, QED, rdMolDescriptors
from rdkit.Contrib.SA_Score import sascorer
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator

FP = GetMorganGenerator(radius=2, fpSize=2048)


def standardize(smiles: str) -> str | None:
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None or mol.GetNumHeavyAtoms() == 0:
            return None
        return Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    except Exception:
        return None


def prepare(rows: Iterable[dict]) -> list[dict]:
    """Preserve first occurrence; reject invalid and duplicate structures."""
    seen = set()
    result = []
    for index, row in enumerate(rows):
        canonical = standardize(row.get("smiles", ""))
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        result.append({"molecule_id": str(row.get("molecule_id") or f"mol_{index:05d}"),
                       "smiles": canonical})
    return result


def descriptors(smiles: str) -> dict:
    canonical = standardize(smiles)
    if canonical is None:
        return {"status": "invalid", "smiles": smiles}
    mol = Chem.MolFromSmiles(canonical)
    return {"status": "ok", "smiles": canonical, "qed": float(QED.qed(mol)),
            "mw": float(Descriptors.MolWt(mol)),
            "clogp": float(Crippen.MolLogP(mol)),
            "tpsa": float(rdMolDescriptors.CalcTPSA(mol)),
            "sa": float(sascorer.calculateScore(mol)),
            "rdkit_version": rdBase.rdkitVersion}


def similarity(first: str, second: str) -> float:
    a, b = standardize(first), standardize(second)
    if a is None or b is None:
        raise ValueError("invalid SMILES")
    return float(DataStructs.TanimotoSimilarity(FP.GetFingerprint(Chem.MolFromSmiles(a)),
                                                 FP.GetFingerprint(Chem.MolFromSmiles(b))))


def diversity(smiles: list[str]) -> float | None:
    """Mean pairwise 1-Tanimoto; unavailable for fewer than two molecules."""
    if len(smiles) < 2:
        return None
    differences = [1 - similarity(smiles[i], smiles[j])
                   for i in range(len(smiles)) for j in range(i + 1, len(smiles))]
    return sum(differences) / len(differences)


def dominates(a: dict, b: dict, directions: dict[str, str]) -> bool:
    """Missing/failed measurements are incomparable, never assumed safe."""
    if not directions or any(
        not isinstance(a.get(k), (int, float))
        or not isinstance(b.get(k), (int, float))
        or not math.isfinite(a[k]) or not math.isfinite(b[k])
        for k in directions
    ):
        return False
    if any(v not in ("min", "max") for v in directions.values()):
        raise ValueError("direction must be min or max")
    better_or_equal = all(a[k] >= b[k] if d == "max" else a[k] <= b[k]
                          for k, d in directions.items())
    strictly_better = any(a[k] > b[k] if d == "max" else a[k] < b[k]
                          for k, d in directions.items())
    return better_or_equal and strictly_better


def pareto_front(rows: list[dict], directions: dict[str, str]) -> list[dict]:
    complete = [r for r in rows if all(
        isinstance(r.get(k), (int, float)) and math.isfinite(r[k])
        for k in directions)]
    return [r for i, r in enumerate(complete) if not any(
        dominates(other, r, directions)
        for j, other in enumerate(complete) if i != j)]


@dataclass
class Budget:
    max_cost_units: float
    max_tool_calls: int
    used_cost_units: float = 0
    tool_calls: int = 0

    def __post_init__(self):
        if (not math.isfinite(self.max_cost_units) or self.max_cost_units < 0
            or self.max_tool_calls < 0 or self.used_cost_units < 0
            or self.tool_calls < 0):
            raise ValueError("invalid budget")

    def permits(self, cost: float) -> bool:
        return (math.isfinite(cost) and cost >= 0
                and self.tool_calls < self.max_tool_calls
                and self.used_cost_units + cost <= self.max_cost_units + 1e-12)

    def debit(self, cost: float) -> None:
        if not self.permits(cost):
            raise ValueError("budget exceeded")
        self.used_cost_units += cost
        self.tool_calls += 1


def offline_oracle(smiles: str) -> float:
    """Explicit synthetic test fixture, NOT an ADMET/experimental estimate."""
    canonical = standardize(smiles)
    if canonical is None:
        raise ValueError("invalid molecule")
    value = hashlib.sha256(canonical.encode()).digest()
    return int.from_bytes(value[:4], "big") / (2**32 - 1)


def choose(rows: list[dict], policy: str, seed: int) -> list[dict]:
    import random
    rng = random.Random(seed)
    ordered = list(rows)
    if policy == "fixed":
        return ordered
    if policy == "rules":
        return sorted(ordered, key=lambda r: (-r["qed"], r["molecule_id"]))
    if policy == "agent":
        # A deterministic offline stand-in, NOT an LLM or Strands agent.
        rng.shuffle(ordered)
        return sorted(ordered, key=lambda r: (-r["qed"] + 0.05 * rng.random(), r["molecule_id"]))
    raise ValueError("unknown policy")


def run(rows: list[dict], policy: str, seed: int = 42,
        max_cost_units: float = 5, max_tool_calls: int = 5) -> dict:
    budget = Budget(max_cost_units, max_tool_calls)
    prepared = prepare(rows)
    scored = [{"molecule_id": r["molecule_id"], **descriptors(r["smiles"])}
              for r in prepared]
    calls, evaluations = [], []
    for molecule in choose(scored, policy, seed):
        if not budget.permits(1):
            break
        budget.debit(1)
        synthetic = offline_oracle(molecule["smiles"])
        evaluated = {**molecule, "fixture_risk": synthetic,
                     "fixture_risk_status": "ok", "fixture_risk_source": "offline-fixture"}
        evaluations.append(evaluated)
        calls.append({"molecule_id": molecule["molecule_id"], "tool": "offline-fixture",
                      "cost_units": 1, "cache_hit": False, "status": "ok"})
    frontier = pareto_front(evaluations, {"qed": "max", "fixture_risk": "min"})
    return {"policy": policy, "seed": seed, "molecules": scored, "evaluated": evaluations,
            "calls": calls, "pareto": frontier, "budget": asdict(budget),
            "mode": "offline-fixture",
            "warning": "Synthetic oracle; not ADMET, toxicity, target activity or measured evidence."}


def save_run(result: dict, out: str | Path) -> None:
    import csv
    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (dest / "calls.jsonl").write_text(
        "".join(json.dumps(c) + "\n" for c in result["calls"]), encoding="utf-8")
    for filename, key in (("molecules.csv", "molecules"), ("pareto.csv", "pareto"),
                          ("top_candidates.csv", "evaluated")):
        data = result[key]
        with (dest / filename).open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(data[0]) if data else ["molecule_id"])
            writer.writeheader()
            writer.writerows(data)
