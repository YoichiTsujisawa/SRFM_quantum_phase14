from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
IN_DIR = ROOT / "data" / "phase13_import"
RESULTS_DIR = ROOT / "results"

ROBUST_TRIALS = IN_DIR / "phase13_step08_memory_robustness_trials.csv"
BASIN_COORDS = RESULTS_DIR / "phase14_step02_basin_coordinates.csv"

OUT_ENTROPY = RESULTS_DIR / "phase14_step03_basin_entropy.csv"
OUT_ENTROPY_BY_NOISE = RESULTS_DIR / "phase14_step03_entropy_by_noise.csv"
OUT_ENTROPY_BY_MEMORY_CLASS = RESULTS_DIR / "phase14_step03_entropy_by_memory_class.csv"
OUT_HEADLINE = RESULTS_DIR / "phase14_step03_entropy_headline_summary.csv"

EPS = 1.0e-12

def shannon_entropy(counts: pd.Series) -> float:
    total = counts.sum()
    if total <= 0:
        return np.nan
    p = counts / total
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())

def normalized_entropy(entropy: float, n_states: int) -> float:
    if n_states <= 1 or pd.isna(entropy):
        return 0.0
    return float(entropy / np.log(n_states))

def find_col(df: pd.DataFrame, candidates: list[str], required=True) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"None of these columns found: {candidates}")
    return None

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
        case_col = "phase14_case_key"
    else:
        trials["phase14_case_key"] = trials[case_col].astype(str)

    trials["memory_state_phase14"] = trials[memory_state_col].astype(str)

    state_order = sorted(trials["memory_state_phase14"].dropna().unique().tolist())
    n_possible_states = len(state_order)

    # ------------------------------------------------------------
    # 1. Entropy by exact perturbation coordinate
    # ------------------------------------------------------------
    rows = []

    group_cols = [state_noise_col, coupling_noise_col]

    for (s_noise, c_noise), g in trials.groupby(group_cols, dropna=False):
        counts = g["memory_state_phase14"].value_counts()
        entropy = shannon_entropy(counts)
        n_observed = int((counts > 0).sum())

        row = {
            "state_noise": s_noise,
            "coupling_noise": c_noise,
            "trial_count": len(g),
            "observed_state_count": n_observed,
            "basin_entropy": entropy,
            "basin_entropy_norm_observed": normalized_entropy(entropy, n_observed),
            "basin_entropy_norm_global": normalized_entropy(entropy, n_possible_states),
            "dominant_state": counts.idxmax(),
            "dominant_state_probability": float(counts.max() / counts.sum()),
        }

        for st in state_order:
            row[f"p_{st}"] = float(counts.get(st, 0) / counts.sum())

        rows.append(row)

    entropy_df = pd.DataFrame(rows).sort_values(["state_noise", "coupling_noise"])
    entropy_df.to_csv(OUT_ENTROPY, index=False)

    # ------------------------------------------------------------
    # 2. Entropy by combined noise magnitude
    # ------------------------------------------------------------
    trials["combined_noise_radius"] = np.sqrt(
        trials[state_noise_col].fillna(0.0) ** 2
        + trials[coupling_noise_col].fillna(0.0) ** 2
    )

    unique_radii = np.sort(trials["combined_noise_radius"].dropna().unique())

    rows = []
    for radius, g in trials.groupby("combined_noise_radius", dropna=False):
        counts = g["memory_state_phase14"].value_counts()
        entropy = shannon_entropy(counts)
        n_observed = int((counts > 0).sum())

        row = {
            "combined_noise_radius": radius,
            "trial_count": len(g),
            "observed_state_count": n_observed,
            "basin_entropy": entropy,
            "basin_entropy_norm_observed": normalized_entropy(entropy, n_observed),
            "basin_entropy_norm_global": normalized_entropy(entropy, n_possible_states),
            "dominant_state": counts.idxmax(),
            "dominant_state_probability": float(counts.max() / counts.sum()),
        }

        for st in state_order:
            row[f"p_{st}"] = float(counts.get(st, 0) / counts.sum())

        rows.append(row)

    entropy_by_noise = pd.DataFrame(rows).sort_values("combined_noise_radius")
    entropy_by_noise.to_csv(OUT_ENTROPY_BY_NOISE, index=False)

    # ------------------------------------------------------------
    # 3. Entropy by imported Phase14 basin class, if key overlaps
    # ------------------------------------------------------------
    entropy_by_class = pd.DataFrame()

    if BASIN_COORDS.exists():
        coords = pd.read_csv(BASIN_COORDS)
        coords["phase14_case_key"] = coords["phase14_case_key"].astype(str)

        merged = trials.merge(
            coords[["phase14_case_key", "phase14_basin_class", "relaxation_layer"]],
            on="phase14_case_key",
            how="left"
        )

        rows = []
        for basin_class, g in merged.groupby("phase14_basin_class", dropna=False):
            counts = g["memory_state_phase14"].value_counts()
            if len(counts) == 0:
                continue

            entropy = shannon_entropy(counts)
            n_observed = int((counts > 0).sum())

            row = {
                "phase14_basin_class": basin_class,
                "trial_count": len(g),
                "observed_state_count": n_observed,
                "basin_entropy": entropy,
                "basin_entropy_norm_observed": normalized_entropy(entropy, n_observed),
                "basin_entropy_norm_global": normalized_entropy(entropy, n_possible_states),
                "dominant_state": counts.idxmax(),
                "dominant_state_probability": float(counts.max() / counts.sum()),
            }

            for st in state_order:
                row[f"p_{st}"] = float(counts.get(st, 0) / counts.sum())

            rows.append(row)

        entropy_by_class = pd.DataFrame(rows)
        entropy_by_class.to_csv(OUT_ENTROPY_BY_MEMORY_CLASS, index=False)
    else:
        entropy_by_class.to_csv(OUT_ENTROPY_BY_MEMORY_CLASS, index=False)

    # ------------------------------------------------------------
    # 4. Headline summary
    # ------------------------------------------------------------
    max_entropy_row = entropy_df.loc[entropy_df["basin_entropy"].idxmax()]
    max_entropy_noise_row = entropy_by_noise.loc[entropy_by_noise["basin_entropy"].idxmax()]

    headline = pd.DataFrame([{
        "phase": "Phase14",
        "step": "Step03",
        "purpose": "Analyze basin entropy of Phase13 perturbation-supported memory states",
        "trial_rows": len(trials),
        "state_noise_levels": trials[state_noise_col].nunique(dropna=True),
        "coupling_noise_levels": trials[coupling_noise_col].nunique(dropna=True),
        "memory_state_count": n_possible_states,
        "memory_states": "|".join(state_order),
        "mean_basin_entropy": entropy_df["basin_entropy"].mean(),
        "median_basin_entropy": entropy_df["basin_entropy"].median(),
        "max_basin_entropy": entropy_df["basin_entropy"].max(),
        "max_entropy_state_noise": max_entropy_row["state_noise"],
        "max_entropy_coupling_noise": max_entropy_row["coupling_noise"],
        "max_entropy_dominant_state": max_entropy_row["dominant_state"],
        "max_entropy_dominant_state_probability": max_entropy_row["dominant_state_probability"],
        "max_entropy_noise_radius": max_entropy_noise_row["combined_noise_radius"],
        "max_entropy_noise_radius_dominant_state": max_entropy_noise_row["dominant_state"],
        "max_entropy_noise_radius_dominant_probability": max_entropy_noise_row["dominant_state_probability"],
    }])

    headline.to_csv(OUT_HEADLINE, index=False)

    print("Phase14 Step03 complete.")
    print(f"Saved: {OUT_ENTROPY}")
    print(f"Saved: {OUT_ENTROPY_BY_NOISE}")
    print(f"Saved: {OUT_ENTROPY_BY_MEMORY_CLASS}")
    print(f"Saved: {OUT_HEADLINE}")
    print("")
    print(headline.to_string(index=False))
    print("")
    print("Top entropy perturbation coordinates:")
    print(
        entropy_df.sort_values("basin_entropy", ascending=False)
        .head(10)
        .to_string(index=False)
    )
    print("")
    if len(entropy_by_class) > 0:
        print("Entropy by Phase14 basin class:")
        print(entropy_by_class.to_string(index=False))

if __name__ == "__main__":
    main()