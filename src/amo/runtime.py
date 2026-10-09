"""Safety boundaries for proposed evaluation actions and a versioned local cache."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .core import Budget, standardize


@dataclass(frozen=True)
class Action:
    kind: str
    molecule_id: str | None = None
    tool: str | None = None
    task: str | None = None


def validate_action(raw: Any, *, molecule_ids: set[str],
                    allowed_tasks: dict[str, set[str]], budget: Budget,
                    costs: dict[str, float]) -> Action:
    """Never delegate authority or budget checks to an LLM's text."""
    if not isinstance(raw, dict):
        raise ValueError("action must be an object")
    if raw.get("kind") == "stop" and set(raw) == {"kind"}:
        return Action("stop")
    if raw.get("kind") != "evaluate" or set(raw) != {"kind", "molecule_id", "tool", "task"}:
        raise ValueError("invalid action schema")
    molecule_id, tool, task = raw["molecule_id"], raw["tool"], raw["task"]
    if not all(isinstance(x, str) for x in (molecule_id, tool, task)):
        raise ValueError("action fields must be strings")
    if molecule_id not in molecule_ids:
        raise ValueError("unknown molecule")
    if tool not in allowed_tasks or task not in allowed_tasks[tool]:
        raise ValueError("tool/task not permitted")
    if tool not in costs or not budget.permits(costs[tool]):
        raise ValueError("budget exceeded or tool not priced")
    return Action("evaluate", molecule_id, tool, task)


class ScoreCache:
    """SQLite cache keyed by molecule, endpoint, model revision, and preprocessing.

    Scoped per independent benchmark run unless a shared warm-cache protocol is declared.
    """
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(str(path))
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS scores (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )

    @staticmethod
    def key(smiles: str, tool: str, endpoint: str, revision: str,
            preprocessing: str = "rdkit-canonical-isomeric-v1") -> str:
        canonical = standardize(smiles)
        if canonical is None or not all((tool, endpoint, revision, preprocessing)):
            raise ValueError("invalid cache key")
        value = json.dumps([canonical, tool, endpoint, revision, preprocessing],
                           separators=(",", ":"))
        return hashlib.sha256(value.encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        row = self.connection.execute(
            "SELECT payload FROM scores WHERE cache_key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key: str, value: dict) -> None:
        if not isinstance(value, dict) or value.get("status") != "ok":
            raise ValueError("only successful verified outputs can be cached")
        self.connection.execute("INSERT OR REPLACE INTO scores VALUES (?, ?)",
                                (key, json.dumps(value, allow_nan=False)))
        self.connection.commit()

    def close(self):
        self.connection.close()
