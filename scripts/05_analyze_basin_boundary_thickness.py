from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
RESULTS_DIR = ROOT / "results"

IN_BY_NOISE = RESULTS_DIR / "phase14_step04_transition_by_noise.csv"

OUT_BOUNDARY = RESULTS_DIR / "phase14_step05_boundary_thickness.csv"
OUT_THRESHOLDS = RESULTS_DIR / "phase14_step05_collapse_thresholds.csv"
OUT_HEADLINE = RESULTS_DIR / "phase14_step05_boundary_headline_summary.csv"

EPS = 1.0e-12

def classify_boundary_regime(row) -> str:
    survival = row["survival_mass"]
    erasure = row["erasure_mass"]
    entropy = row["transition_entropy_norm"]
    degradation = row["degradation_index"]

    if survival >= 0.80 and erasure <= 0.05:
        return "deep_survival_basin"

    if survival >= 0.60 and erasure <= 0.15:
        return "survival_dominant_basin"

    if entropy >= 0.90 and 0.10 <= erasure <= 0.25:
        return "broad_transition_boundary"

    if degradation >= 0.50 or erasure >= 0.25:
        return "collapse_boundary"

    return "mixed_boundary_region"

def estimate_threshold(df: pd.DataFrame, x_col: str, y_col: str, target: float, direction: str):
    """
    Estimate first x where y crosses target.

    direction:
      "below": first y <= target
      "above": first y >= target
    """
    d = df[[x_col, y_col]].dropna().sort_values(x_col)

    if len(d) == 0:
        return np.nan

    if direction == "below":
        crossed = d[d[y_col] <= target]
    elif direction == "above":
        crossed = d[d[y_col] >= target]
    else:
        raise ValueError(direction)

    if len(crossed) == 0:
        return np.nan

    return float(crossed.iloc[0][x_col])

def compute_slope(df: pd.DataFrame, x_col: str, y_col: str):
    d = df[[x_col, y_col]].dropna().sort_values(x_col)

    if len(d) < 2:
        return np.nan

    x = d[x_col].to_numpy(dtype=float)
    y = d[y_col].to_numpy(dtype=float)

    if np.allclose(x.max(), x.min()):
        return np.nan

    slope, intercept = np.polyfit(x, y, deg=1)
    return float(slope)

def main():
    if not IN_BY_NOISE.exists():
        raise FileNotFoundError(f"Missing input: {IN_BY_NOISE}")

    df = pd.read_csv(IN_BY_NOISE)

    required = [
        "state_noise",
        "coupling_noise",
        "combined_noise_radius",
        "survival_mass",
        "erasure_mass",
        "degradation_index",
        "transition_entropy_norm",
        "p_topology_only_memory_survived",
        "p_partial_topology_memory",
        "p_mixed_or_weak_memory",
        "p_memory_erased",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in Step04 output: {missing}")

    for c in required:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    boundary = df.copy()

    boundary["boundary_regime"] = boundary.apply(classify_boundary_regime, axis=1)

    boundary["memory_loss_mass"] = (
        boundary["p_mixed_or_weak_memory"]
        + boundary["p_memory_erased"]
    )

    boundary["partial_retention_ratio"] = (
        boundary["p_partial_topology_memory"]
        / (
            boundary["p_topology_only_memory_survived"]
            + boundary["p_partial_topology_memory"]
            + EPS
        )
    )

    boundary["erasure_given_loss"] = (
        boundary["p_memory_erased"]
        / (
            boundary["p_mixed_or_weak_memory"]
            + boundary["p_memory_erased"]
            + EPS
        )
    )

    boundary["boundary_thickness_proxy"] = (
        boundary["transition_entropy_norm"]
        * (1.0 - boundary["dominant_probability"])
    )

    boundary["erosion_index"] = (
        boundary["memory_loss_mass"]
        + boundary["degradation_index"]
        - boundary["p_memory_erased"]
    )

    boundary.to_csv(OUT_BOUNDARY, index=False)

    # ------------------------------------------------------------
    # Thresholds along coupling noise, averaged over state_noise
    # ------------------------------------------------------------
    by_coupling = (
        boundary
        .groupby("coupling_noise", dropna=False)
        .agg(
            mean_survival_mass=("survival_mass", "mean"),
            mean_erasure_mass=("erasure_mass", "mean"),
            mean_degradation_index=("degradation_index", "mean"),
            mean_transition_entropy_norm=("transition_entropy_norm", "mean"),
            mean_boundary_thickness_proxy=("boundary_thickness_proxy", "mean"),
            mean_erosion_index=("erosion_index", "mean"),
        )
        .reset_index()
        .sort_values("coupling_noise")
    )

    # Thresholds along state noise, averaged over coupling_noise
    by_state = (
        boundary
        .groupby("state_noise", dropna=False)
        .agg(
            mean_survival_mass=("survival_mass", "mean"),
            mean_erasure_mass=("erasure_mass", "mean"),
            mean_degradation_index=("degradation_index", "mean"),
            mean_transition_entropy_norm=("transition_entropy_norm", "mean"),
            mean_boundary_thickness_proxy=("boundary_thickness_proxy", "mean"),
            mean_erosion_index=("erosion_index", "mean"),
        )
        .reset_index()
        .sort_values("state_noise")
    )

    # Thresholds by combined noise radius
    by_radius = (
        boundary
        .groupby("combined_noise_radius", dropna=False)
        .agg(
            mean_survival_mass=("survival_mass", "mean"),
            mean_erasure_mass=("erasure_mass", "mean"),
            mean_degradation_index=("degradation_index", "mean"),
            mean_transition_entropy_norm=("transition_entropy_norm", "mean"),
            mean_boundary_thickness_proxy=("boundary_thickness_proxy", "mean"),
            mean_erosion_index=("erosion_index", "mean"),
        )
        .reset_index()
        .sort_values("combined_noise_radius")
    )

    thresholds = []

    for axis_name, table, x_col in [
        ("coupling_noise_axis", by_coupling, "coupling_noise"),
        ("state_noise_axis", by_state, "state_noise"),
        ("combined_noise_radius_axis", by_radius, "combined_noise_radius"),
    ]:
        thresholds.append({
            "axis": axis_name,
            "survival_below_0p80": estimate_threshold(table, x_col, "mean_survival_mass", 0.80, "below"),
            "survival_below_0p70": estimate_threshold(table, x_col, "mean_survival_mass", 0.70, "below"),
            "survival_below_0p60": estimate_threshold(table, x_col, "mean_survival_mass", 0.60, "below"),
            "erasure_above_0p10": estimate_threshold(table, x_col, "mean_erasure_mass", 0.10, "above"),
            "erasure_above_0p15": estimate_threshold(table, x_col, "mean_erasure_mass", 0.15, "above"),
            "erasure_above_0p20": estimate_threshold(table, x_col, "mean_erasure_mass", 0.20, "above"),
            "degradation_above_0p40": estimate_threshold(table, x_col, "mean_degradation_index", 0.40, "above"),
            "degradation_above_0p50": estimate_threshold(table, x_col, "mean_degradation_index", 0.50, "above"),
            "entropy_above_0p90": estimate_threshold(table, x_col, "mean_transition_entropy_norm", 0.90, "above"),
            "survival_slope": compute_slope(table, x_col, "mean_survival_mass"),
            "erasure_slope": compute_slope(table, x_col, "mean_erasure_mass"),
            "degradation_slope": compute_slope(table, x_col, "mean_degradation_index"),
            "boundary_thickness_slope": compute_slope(table, x_col, "mean_boundary_thickness_proxy"),
        })

    thresholds_df = pd.DataFrame(thresholds)
    thresholds_df.to_csv(OUT_THRESHOLDS, index=False)

    # ------------------------------------------------------------
    # Headline
    # ------------------------------------------------------------
    regime_counts = (
        boundary["boundary_regime"]
        .value_counts()
        .rename_axis("boundary_regime")
        .reset_index(name="count")
    )
    regime_counts["ratio"] = regime_counts["count"] / len(boundary)

    max_thickness_row = boundary.loc[boundary["boundary_thickness_proxy"].idxmax()]
    max_erosion_row = boundary.loc[boundary["erosion_index"].idxmax()]
    max_erasure_row = boundary.loc[boundary["erasure_mass"].idxmax()]
    min_survival_row = boundary.loc[boundary["survival_mass"].idxmin()]

    headline = pd.DataFrame([{
        "phase": "Phase14",
        "step": "Step05",
        "purpose": "Analyze basin boundary thickness and collapse/erosion thresholds",
        "noise_grid_points": len(boundary),
        "mean_survival_mass": boundary["survival_mass"].mean(),
        "min_survival_mass": boundary["survival_mass"].min(),
        "mean_erasure_mass": boundary["erasure_mass"].mean(),
        "max_erasure_mass": boundary["erasure_mass"].max(),
        "mean_degradation_index": boundary["degradation_index"].mean(),
        "max_degradation_index": boundary["degradation_index"].max(),
        "mean_transition_entropy_norm": boundary["transition_entropy_norm"].mean(),
        "mean_boundary_thickness_proxy": boundary["boundary_thickness_proxy"].mean(),
        "max_boundary_thickness_proxy": boundary["boundary_thickness_proxy"].max(),
        "max_thickness_state_noise": max_thickness_row["state_noise"],
        "max_thickness_coupling_noise": max_thickness_row["coupling_noise"],
        "max_erosion_state_noise": max_erosion_row["state_noise"],
        "max_erosion_coupling_noise": max_erosion_row["coupling_noise"],
        "max_erasure_state_noise": max_erasure_row["state_noise"],
        "max_erasure_coupling_noise": max_erasure_row["coupling_noise"],
        "min_survival_state_noise": min_survival_row["state_noise"],
        "min_survival_coupling_noise": min_survival_row["coupling_noise"],
        "deep_survival_basin_count": int((boundary["boundary_regime"] == "deep_survival_basin").sum()),
        "survival_dominant_basin_count": int((boundary["boundary_regime"] == "survival_dominant_basin").sum()),
        "broad_transition_boundary_count": int((boundary["boundary_regime"] == "broad_transition_boundary").sum()),
        "collapse_boundary_count": int((boundary["boundary_regime"] == "collapse_boundary").sum()),
        "mixed_boundary_region_count": int((boundary["boundary_regime"] == "mixed_boundary_region").sum()),
    }])

    headline.to_csv(OUT_HEADLINE, index=False)

    print("Phase14 Step05 complete.")
    print(f"Saved: {OUT_BOUNDARY}")
    print(f"Saved: {OUT_THRESHOLDS}")
    print(f"Saved: {OUT_HEADLINE}")
    print("")
    print("Headline:")
    print(headline.to_string(index=False))
    print("")
    print("Boundary regime counts:")
    print(regime_counts.to_string(index=False))
    print("")
    print("Collapse / erosion thresholds:")
    print(thresholds_df.to_string(index=False))
    print("")
    print("Top boundary thickness points:")
    print(
        boundary.sort_values("boundary_thickness_proxy", ascending=False)
        .head(10)
        .to_string(index=False)
    )

if __name__ == "__main__":
    main()