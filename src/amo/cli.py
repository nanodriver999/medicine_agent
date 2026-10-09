"""Initial CLI: deterministic offline smoke and policy runs."""
import argparse
import csv
import json
from pathlib import Path
from .core import prepare, descriptors, run, save_run
from .evaluation import run_comparison, export_comparison
from .admet_smoke import run_smoke, export_smoke
from .admet import Endpoint


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
    compare = sub.add_parser("compare")
    compare.add_argument("--input", required=True)
    compare.add_argument("--out", required=True)
    compare.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    compare.add_argument("--policies", nargs="+", choices=["fixed", "rules", "agent"],
                         default=["fixed", "rules", "agent"])
    compare.add_argument("--budget", type=int, default=5)
    dashboard = sub.add_parser("ui")
    dashboard.add_argument("--runs", required=True)
    live = sub.add_parser("admet-smoke", help="opt-in: runs real ADMET-AI predictions")
    live.add_argument("--input", required=True)
    live.add_argument("--out", required=True)
    live.add_argument("--endpoint", required=True)
    live.add_argument("--direction", choices=["min", "max"], required=True)
    live.add_argument("--unit", required=True)
    live.add_argument("--revision", required=True)
    live.add_argument("--count", type=int, default=10)
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
    elif args.command == "compare":
        report = run_comparison(load(args.input), seeds=args.seeds,
                                policies=args.policies, budget=args.budget)
        export_comparison(report, args.out, args.input)
        print(json.dumps({"runs": len(report["runs"]), "out": args.out,
                          "mode": "offline-fixture"}))
    elif args.command == "admet-smoke":
        endpoint = Endpoint(args.endpoint, args.direction, args.unit, args.revision)
        report = run_smoke(load(args.input), endpoint, max_count=args.count)
        export_smoke(report, args.out)
        print(json.dumps({"status": report["status"], "successes": report["successes"],
                          "count": len(report["calls"]), "out": args.out}))
    elif args.command == "ui":
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "streamlit", "run",
                        str(Path(__file__).with_name("ui.py")), "--",
                        "--runs", args.runs], check=True)
    else:
        result = run(load(args.input), args.policy, args.seed, args.budget, args.budget)
        save_run(result, args.out)
        print(json.dumps({"evaluated": len(result["evaluated"]), "cost": result["budget"]["used_cost_units"]}))


if __name__ == "__main__":
    main()
