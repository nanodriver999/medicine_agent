"""Retrospective blinded ChEMBL assay replay.

Measured data are held privately until a candidate is selected. This is a
replay of existing observations, not new wet-lab synthesis or experiments.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import json
import math
from pathlib import Path
from typing import Callable, Iterable
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from .core import Budget, descriptors, prepare


@dataclass(frozen=True)
class Observation:
    molecule_id: str
    smiles: str
    value: float
    assay_id: str
    standard_type: str
    unit: str


def curate_assay(rows: Iterable[dict], *, assay_id: str,
                 standard_type: str = "IC50", unit: str = "nM") -> list[Observation]:
    """Select exact assay/type/unit, remove censored and conflicting duplicates.

    Accept only standard_relation '=' and finite positive nM values.
    ChEMBL values are not pooled across unrelated assays or assay conditions.
    """
    if not assay_id or not standard_type or not unit:
        raise ValueError("assay metadata is mandatory")
    observations: list[Observation] = []
    for row in rows:
        if (str(row.get("assay_chembl_id", "")) != assay_id
            or row.get("standard_type") != standard_type
            or row.get("standard_units") != unit
            or row.get("standard_relation") != "="):
            continue
        raw = row.get("standard_value")
        smiles = row.get("canonical_smiles")
        molecule_id = row.get("molecule_chembl_id")
        if not isinstance(smiles, str) or not isinstance(molecule_id, str):
            continue
        try:
            measured = float(raw)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(measured) or measured <= 0:
            continue
        canonical = prepare([{"molecule_id": molecule_id, "smiles": smiles}])
        if not canonical:
            continue
        observations.append(Observation(molecule_id, canonical[0]["smiles"],
                                         measured, assay_id, standard_type, unit))
    # Conflicting duplicate measurements cannot silently be averaged;
    # only structures with one unambiguous measurement are kept.
    grouped: dict[str, list[Observation]] = {}
    for observation in observations:
        grouped.setdefault(observation.smiles, []).append(observation)
    clean = []
    for smi, values in sorted(grouped.items()):
        if len({entry.value for entry in values}) == 1:
            clean.append(values[0])
    return clean


def scaffold_group(smiles: str) -> str:
    """Murcko scaffold or canonical fallback when no ring scaffold exists."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("invalid canonical SMILES")
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
    return scaffold or f"acyclic:{smiles}"


def split_scaffolds(observations: list[Observation], *, train_fraction: float = 0.8,
                    seed: int = 42) -> tuple[list[Observation], list[Observation]]:
    """Allocate whole scaffolds between train and holdout, never split a scaffold."""
    import random
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction out of range")
    groups: dict[str, list[Observation]] = {}
    for obs in observations:
        groups.setdefault(scaffold_group(obs.smiles), []).append(obs)
    group_keys = sorted(groups)
    rng = random.Random(seed)
    rng.shuffle(group_keys)
    if len(group_keys) < 2:
        raise ValueError("need at least two distinct scaffolds")
    cutoff = max(1, min(len(group_keys) - 1, round(train_fraction * len(group_keys))))
    training = [obs for key in group_keys[:cutoff] for obs in groups[key]]
    holdout = [obs for key in group_keys[cutoff:] for obs in groups[key]]
    assert {scaffold_group(x.smiles) for x in training}.isdisjoint(
        {scaffold_group(x.smiles) for x in holdout})
    return training, holdout


class HiddenAssay:
    """Only reveal observations for valid, selected IDs after charging budget."""
    def __init__(self, observations: list[Observation], cost_units: int = 1,
                 max_evaluations: int = 5):
        if cost_units <= 0:
            raise ValueError("observation cost must be positive")
        if len({o.molecule_id for o in observations}) != len(observations):
            raise ValueError("molecule ID collisions")
        self._hidden = {o.molecule_id: o for o in observations}
        self.budget = Budget(cost_units * max_evaluations, max_evaluations)
        self.cost_units = cost_units
        self._revealed: dict[str, dict] = {}

    def visible_pool(self) -> list[dict]:
        """No activity value or assay label in this policy-visible projection."""
        return [{"molecule_id": obs.molecule_id, **descriptors(obs.smiles)}
                for obs in sorted(self._hidden.values(), key=lambda o: o.molecule_id)]

    def reveal(self, molecule_id: str) -> dict:
        if molecule_id not in self._hidden:
            raise ValueError("unknown candidate")
        if molecule_id in self._revealed:
            return {**self._revealed[molecule_id], "cache_hit": True, "cost_units": 0}
        if not self.budget.permits(self.cost_units):
            raise ValueError("budget exceeded")
        self.budget.debit(self.cost_units)
        obs = self._hidden[molecule_id]
        # pActivity= -log10(molar concentration), for valid nM endpoint only.
        if obs.unit != "nM":
            raise ValueError("pActivity conversion requires verified nM values")
        p_activity = 9.0 - math.log10(obs.value)
        result = {"molecule_id": molecule_id, "observed_value": obs.value,
                  "observed_unit": obs.unit, "p_activity": p_activity,
                  "measurement_source": "chembl_retrospective_assay",
                  "status": "measured_historical", "cost_units": self.cost_units,
                  "cache_hit": False}
        self._revealed[molecule_id] = result
        return result


def replay(observations: list[Observation], *, budget: int,
           selector: Callable[[list[dict]], list[str]]) -> dict:
    """Selector receives a fresh *unlabeled* pool, outputs molecule IDs."""
    hidden = HiddenAssay(observations, max_evaluations=budget)
    public = hidden.visible_pool()
    selected = selector(public)
    if not isinstance(selected, list):
        raise ValueError("selector must return a list of IDs")
    results = []
    for molecule_id in selected:
        if len(results) >= budget:
            break
        if not isinstance(molecule_id, str):
            raise ValueError("invalid selector ID")
        outcome = hidden.reveal(molecule_id)
        if outcome["cache_hit"]:
            continue
        results.append(outcome)
    return {"mode": "retrospective_dmta", "observations": results,
            "eligible_pool_size": len(public),
            "consumed_cost_units": hidden.budget.used_cost_units,
            "notice": "Historical measured assay values, not prospective wet-lab measurements."}
