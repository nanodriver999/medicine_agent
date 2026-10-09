"""Initial CLI: deterministic offline smoke and policy runs."""
import argparse
import csv
import json
from pathlib import Path
from .core import prepare, descriptors, run, save_run


def load(path):
    with open(path, newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def main():
    parser = argparse.ArgumentParser(prog="amo")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--input", required=True)
    prep.add_argument("--output", required=True)
    score = sub.add_parser("score")
    score.add_argument("--input", required=True)
    score.add_argument("--out", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--input", required=True)
    execute.add_argument("--out", required=True)
    execute.add_argument("--policy", choices=["fixed", "rules", "agent"], required=True)
    execute.add_argument("--seed", type=int, default=42)
    execute.add_argument("--budget", type=int, default=5)
    args = parser.parse_args()
    if args.command == "prepare":
        data = prepare(load(args.input))
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=["molecule_id", "smiles"])
            writer.writeheader()
            writer.writerows(data)
        print(json.dumps({"valid_unique": len(data)}))
    elif args.command == "score":
        data = [descriptors(r["smiles"]) for r in prepare(load(args.input))]
        target = Path(args.out)
        target.mkdir(parents=True, exist_ok=True)
        (target / "scores.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps({"scored": len(data)}))
    else:
        result = run(load(args.input), args.policy, args.seed, args.budget, args.budget)
        save_run(result, args.out)
        print(json.dumps({"evaluated": len(result["evaluated"]), "cost": result["budget"]["used_cost_units"]}))


if __name__ == "__main__":
    main()
