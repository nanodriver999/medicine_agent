"""Read-only Streamlit dashboard for offline/research run outputs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def load_report(folder: str | Path) -> dict:
    root = Path(folder)
    with (root / "comparison.json").open(encoding="utf-8") as fp:
        result = json.load(fp)
    if not isinstance(result.get("runs"), list) or not isinstance(result.get("summary"), list):
        raise ValueError("not a valid comparison report")
    return result


def main():
    import pandas as pd
    import streamlit as st
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="outputs/compare")
    args, _ = parser.parse_known_args()
    root = Path(args.runs)
    st.set_page_config(page_title="Molecular Evaluation Benchmark", layout="wide")
    st.title("Molecular Evaluation Benchmark")
    st.warning("Offline fixture values are synthetic. No toxicity, target activity, "
               "efficacy, or clinical safety is established by these results.")
    try:
        report = load_report(root)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        st.error(f"Could not load comparison report: {type(exc).__name__}")
        st.stop()
    data = pd.DataFrame(report["runs"])
    if data.empty:
        st.info("No benchmark runs available.")
        return
    st.subheader("Policy comparison — identical configured evaluation budget")
    seed = st.selectbox("Seed", sorted(data["seed"].unique().tolist()))
    st.dataframe(data.loc[data["seed"] == seed], use_container_width=True)
    st.subheader("All seeds — best synthetic objective")
    st.line_chart(data.pivot(index="seed", columns="policy",
                             values="best_fixture_objective"))
    st.subheader("Cost by policy and seed")
    st.bar_chart(data.pivot(index="seed", columns="policy", values="cost_units"))
    st.subheader("Aggregate summary")
    st.dataframe(pd.DataFrame(report["summary"]), use_container_width=True)
    manifest = root / "manifest.json"
    if manifest.exists():
        with st.expander("Reproducibility manifest"):
            st.json(json.loads(manifest.read_text(encoding="utf-8")))
    st.caption(report.get("warning", ""))


if __name__ == "__main__":
    main()
