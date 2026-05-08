from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
IN_DIR = ROOT / "data" / "phase13_import"
RESULTS_DIR = ROOT / "results"

ROBUST_TRIALS = IN_DIR / "phase13_step08_memory_robustness_trials.csv"
BASIN_COORDS = RESULTS_DIR / "phase14_step02_basin_coordinates.csv"

OUT_MATRIX = RESULTS_DIR / "phase14_step04_transition_matrix.csv"
OUT_EDGES = RESULTS_DIR / "phase14_step04_transition_graph_edges.csv"
OUT_BY_NOISE = RESULTS_DIR / "phase14_step04_transition_by_noise.csv"
OUT_BY_CLASS = RESULTS_DIR / "phase14_step04_transition_by_basin_class.csv"
OUT_HEADLINE = RESULTS_DIR / "phase14_step04_transition_headline_summary.csv"

STATE_ORDER = [
    "topology_only_memory_survived",
    "partial_topology_memory",
    "mixed_or_weak_memory",
    "memory_erased",
]

STATE_RANK = {
    "topology_only_memory_survived": 3,
    "partial_topology_memory": 2,
    "mixed_or_weak_memory": 1,
    "memory_erased": 0,
}

EPS = 1.0e-12

def find_col(df: pd.DataFrame, candidates: list[str], required=True) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"None of these columns found: {candidates}")
    return None

def normalize_counts(counts: pd.Series) -> dict:
    total = counts.sum()
    if total <= 0:
        return {s: 0.0 for s in STATE_ORDER}
    return {s: float(counts.get(s, 0) / total) for s in STATE_ORDER}

def degradation_index(prob: dict) -> float:
    """
    Expected degradation from full topology survival.
    0 = all topology_only_memory_survived
    1 = all memory_erased
    """
    expected_rank = sum(prob[s] * STATE_RANK[s] for s in STATE_ORDER)
    return float((3.0 - expected_rank) / 3.0)

def transition_sharpness(prob: dict) -> float:
    """
    Concentration of transition outcome.
    1 = deterministic
    lower = distributed / competing basin outcomes
    """
    return float(max(prob.values()))

def state_entropy(prob: dict) -> float:
    p = np.array([prob[s] for s in STATE_ORDER], dtype=float)
    p = p[p > 0]
    if len(p) == 0:
        return np.nan
    return float(-(p * np.log(p)).sum())

def summarize_group(g: pd.DataFrame, label_cols: dict) -> dict:
    counts = g["memory_state_phase14"].value_counts()
    prob = normalize_counts(counts)

    row = dict(label_cols)
    row["trial_count"] = int(len(g))

    for s in STATE_ORDER:
        row[f"count_{s}"] = int(counts.get(s, 0))
        row[f"p_{s}"] = prob[s]

    row["dominant_state"] = max(prob, key=prob.get)
    row["dominant_probability"] = transition_sharpness(prob)
    row["transition_entropy"] = state_entropy(prob)
    row["transition_entropy_norm"] = row["transition_entropy"] / np.log(len(STATE_ORDER))
    row["degradation_index"] = degradation_index(prob)
    row["survival_mass"] = prob["topology_only_memory_survived"] + prob["partial_topology_memory"]
    row["erasure_mass"] = prob["memory_erased"]
    row["ambiguous_mass"] = prob["partial_topology_memory"] + prob["mixed_or_weak_memory"]

    return row

def main():
    if not ROBUST_TRIALS.exists():
        raise FileNotFoundError(f"Missing file: {ROBUST_TRIALS}")

    trials = pd.read_csv(ROBUST_TRIALS)

    state_noise_col = find_col(trials, ["state_noise", "sigma_state", "M_noise", "initial_state_noise"])
    coupling_noise_col = find_col(trials, ["coupling_noise", "sigma_coupling", "C_noise", "initial_coupling_noise"])
    memory_state_col = find_col(trials, ["memory_state", "final_memory_state", "basin_state", "state"])
    case_col = find_col(trials, ["case_id", "sample_id", "case_name", "sample_name", "phase14_case_key"], required=False)

    trials[state_noise_col] = pd.to_numeric(trials[state_noise_col], errors="coerce")
    trials[coupling_noise_col] = pd.to_numeric(trials[coupling_noise_col], errors="coerce")

    if case_col is None:
        trials["phase14_case_key"] = np.arange(len(trials)).astype(str)
    else:
        trials["phase14_case_key"] = trials[case_col].astype(str)

    trials["memory_state_phase14"] = trials[memory_state_col].astype(str)

    unknown_states = sorted(set(trials["memory_state_phase14"]) - set(STATE_ORDER))
    if unknown_states:
        raise ValueError(f"Unknown memory states found: {unknown_states}")

    trials["state_noise_phase14"] = trials[state_noise_col]
    trials["coupling_noise_phase14"] = trials[coupling_noise_col]
    trials["combined_noise_radius"] = np.sqrt(
        trials["state_noise_phase14"].fillna(0.0) ** 2
        + trials["coupling_noise_phase14"].fillna(0.0) ** 2
    )

    # Merge basin class if available
    if BASIN_COORDS.exists():
        coords = pd.read_csv(BASIN_COORDS)
        coords["phase14_case_key"] = coords["phase14_case_key"].astype(str)

        keep_cols = [
            "phase14_case_key",
            "phase14_basin_class",
            "relaxation_layer",
            "X_transport_memory",
            "Y_topology_memory",
            "basin_depth_proxy_norm",
        ]
        keep_cols = [c for c in keep_cols if c in coords.columns]

        trials = trials.merge(
            coords[keep_cols],
            on="phase14_case_key",
            how="left"
        )
    else:
        trials["phase14_basin_class"] = np.nan
        trials["relaxation_layer"] = np.nan

    # ------------------------------------------------------------
    # 1. Global transition matrix-like probability vector
    # ------------------------------------------------------------
    global_row = summarize_group(
        trials,
        {"transition_scope": "global"}
    )

    global_matrix = pd.DataFrame([global_row])
    global_matrix.to_csv(OUT_MATRIX, index=False)

    # ------------------------------------------------------------
    # 2. Graph edge list from ideal initial memory to observed states
    # ------------------------------------------------------------
    global_prob = {
        s: global_row[f"p_{s}"]
        for s in STATE_ORDER
    }

    edges = []
    for target in STATE_ORDER:
        edges.append({
            "source_state": "initial_topology_memory",
            "target_state": target,
            "probability": global_prob[target],
            "count": global_row[f"count_{target}"],
            "edge_type": (
                "survival"
                if target == "topology_only_memory_survived"
                else "partial_retention"
                if target == "partial_topology_memory"
                else "weakening"
                if target == "mixed_or_weak_memory"
                else "erasure"
            ),
        })

    edges_df = pd.DataFrame(edges)
    edges_df.to_csv(OUT_EDGES, index=False)

    # ------------------------------------------------------------
    # 3. Transition probabilities by perturbation coordinate
    # ------------------------------------------------------------
    rows = []
    for (s_noise, c_noise), g in trials.groupby(
        ["state_noise_phase14", "coupling_noise_phase14"],
        dropna=False
    ):
        rows.append(summarize_group(
            g,
            {
                "state_noise": s_noise,
                "coupling_noise": c_noise,
                "combined_noise_radius": float(np.sqrt((s_noise or 0.0) ** 2 + (c_noise or 0.0) ** 2)),
            }
        ))

    by_noise = pd.DataFrame(rows).sort_values(["state_noise", "coupling_noise"])
    by_noise.to_csv(OUT_BY_NOISE, index=False)

    # ------------------------------------------------------------
    # 4. Transition probabilities by Phase14 initial basin class
    # ------------------------------------------------------------
    rows = []
    if "phase14_basin_class" in trials.columns:
        for basin_class, g in trials.groupby("phase14_basin_class", dropna=False):
            rows.append(summarize_group(
                g,
                {"phase14_basin_class": basin_class}
            ))

    by_class = pd.DataFrame(rows)
    by_class.to_csv(OUT_BY_CLASS, index=False)

    # ------------------------------------------------------------
    # 5. Headline
    # ------------------------------------------------------------
    max_entropy_row = by_noise.loc[by_noise["transition_entropy"].idxmax()]
    max_erasure_row = by_noise.loc[by_noise["erasure_mass"].idxmax()]
    max_degradation_row = by_noise.loc[by_noise["degradation_index"].idxmax()]
    max_survival_row = by_noise.loc[by_noise["survival_mass"].idxmax()]

    headline = pd.DataFrame([{
        "phase": "Phase14",
        "step": "Step04",
        "purpose": "Build basin transition matrix and perturbation-conditioned transition graph",
        "trial_rows": len(trials),
        "global_p_topology_only_memory_survived": global_row["p_topology_only_memory_survived"],
        "global_p_partial_topology_memory": global_row["p_partial_topology_memory"],
        "global_p_mixed_or_weak_memory": global_row["p_mixed_or_weak_memory"],
        "global_p_memory_erased": global_row["p_memory_erased"],
        "global_survival_mass": global_row["survival_mass"],
        "global_erasure_mass": global_row["erasure_mass"],
        "global_degradation_index": global_row["degradation_index"],
        "global_transition_entropy": global_row["transition_entropy"],
        "global_transition_entropy_norm": global_row["transition_entropy_norm"],
        "max_entropy_state_noise": max_entropy_row["state_noise"],
        "max_entropy_coupling_noise": max_entropy_row["coupling_noise"],
        "max_transition_entropy": max_entropy_row["transition_entropy"],
        "max_erasure_state_noise": max_erasure_row["state_noise"],
        "max_erasure_coupling_noise": max_erasure_row["coupling_noise"],
        "max_erasure_mass": max_erasure_row["erasure_mass"],
        "max_degradation_state_noise": max_degradation_row["state_noise"],
        "max_degradation_coupling_noise": max_degradation_row["coupling_noise"],
        "max_degradation_index": max_degradation_row["degradation_index"],
        "max_survival_state_noise": max_survival_row["state_noise"],
        "max_survival_coupling_noise": max_survival_row["coupling_noise"],
        "max_survival_mass": max_survival_row["survival_mass"],
    }])

    headline.to_csv(OUT_HEADLINE, index=False)

    print("Phase14 Step04 complete.")
    print(f"Saved: {OUT_MATRIX}")
    print(f"Saved: {OUT_EDGES}")
    print(f"Saved: {OUT_BY_NOISE}")
    print(f"Saved: {OUT_BY_CLASS}")
    print(f"Saved: {OUT_HEADLINE}")
    print("")
    print("Headline:")
    print(headline.to_string(index=False))
    print("")
    print("Global transition matrix:")
    print(global_matrix.to_string(index=False))
    print("")
    print("Transition graph edges:")
    print(edges_df.to_string(index=False))
    print("")
    print("Top erasure coordinates:")
    print(
        by_noise.sort_values("erasure_mass", ascending=False)
        .head(10)
        .to_string(index=False)
    )
    print("")
    print("Transition by Phase14 basin class:")
    print(by_class.to_string(index=False))

if __name__ == "__main__":
    main()