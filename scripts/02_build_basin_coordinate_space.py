from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
RESULTS_DIR = ROOT / "results"

IN_FILE = RESULTS_DIR / "phase14_step01_memory_landscape_import.csv"

OUT_COORDS = RESULTS_DIR / "phase14_step02_basin_coordinates.csv"
OUT_CLASS_SUMMARY = RESULTS_DIR / "phase14_step02_basin_class_summary.csv"
OUT_COORD_SUMMARY = RESULTS_DIR / "phase14_step02_basin_coordinate_summary.csv"

EPS = 1.0e-12

def safe_numeric(df: pd.DataFrame, col: str, default=np.nan) -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")

def normalize_01(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    xmin = x.min(skipna=True)
    xmax = x.max(skipna=True)

    if pd.isna(xmin) or pd.isna(xmax) or abs(xmax - xmin) < EPS:
        return pd.Series(0.0, index=x.index)

    return (x - xmin) / (xmax - xmin + EPS)

def classify_phase14_basin(row) -> str:
    h_phi = row["X_transport_memory"]
    h_spec = row["Y_topology_memory"]
    z_surv = row["Z_basin_survival"]

    if pd.isna(h_phi) or pd.isna(h_spec):
        return "unclassified_basin"

    if h_phi < 0.10 and h_spec > 0.50:
        if not pd.isna(z_surv) and z_surv >= 0.50:
            return "stable_topology_only_basin"
        return "topology_only_basin"

    if h_phi > 0.50 and h_spec > 0.50:
        if not pd.isna(z_surv) and z_surv >= 0.50:
            return "stable_coupled_memory_basin"
        return "coupled_memory_basin"

    if h_phi > 0.50 and h_spec <= 0.40:
        return "transport_dominant_basin"

    if h_phi < 0.10 and h_spec < 0.10:
        return "erased_basin"

    return "transition_basin"

def assign_relaxation_layer(row) -> str:
    h_phi = row["X_transport_memory"]
    h_spec = row["Y_topology_memory"]

    if pd.isna(h_phi) or pd.isna(h_spec):
        return "unknown_relaxation"

    if h_phi < 0.10 and h_spec > 0.50:
        return "transport_relaxed_topology_persistent"

    if h_phi > 0.50 and h_spec > 0.50:
        return "transport_and_topology_unrelaxed"

    if h_phi > 0.50 and h_spec <= 0.40:
        return "transport_unrelaxed_topology_relaxed"

    if h_phi < 0.10 and h_spec < 0.10:
        return "transport_and_topology_relaxed"

    return "intermediate_relaxation"

def main():
    if not IN_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {IN_FILE}")

    df = pd.read_csv(IN_FILE)

    coords = pd.DataFrame()
    coords["phase14_case_key"] = df["phase14_case_key"].astype(str)

    # Preserve useful identifiers if present
    for col in [
        "source_table",
        "case_id",
        "sample_id",
        "case_name",
        "sample_name",
        "label",
        "model_name",
        "coupling_model",
        "case_category",
        "adaptive_transport_regime",
        "adaptive_topology_regime",
        "phase14_initial_basin_class",
    ]:
        if col in df.columns:
            coords[col] = df[col]

    # Core Phase14 coordinates
    coords["X_transport_memory"] = safe_numeric(df, "H_phi")
    coords["Y_topology_memory"] = safe_numeric(df, "H_spectral_radius")
    coords["E_entropy_memory"] = safe_numeric(df, "H_entropy")
    coords["M_memory_strength"] = safe_numeric(df, "memory_strength")

    # Robustness / basin persistence coordinates
    survival_candidates = [
        "survival_probability",
        "mean_survival_probability",
        "topology_memory_survival_probability",
    ]
    erased_candidates = [
        "erased_probability",
        "mean_erased_probability",
    ]
    topology_only_candidates = [
        "topology_only_survival_probability",
        "mean_topology_only_survival_probability",
    ]
    retention_candidates = [
        "memory_retention_ratio",
        "mean_memory_retention_ratio",
    ]

    def first_existing_numeric(candidates):
        for c in candidates:
            if c in df.columns:
                return safe_numeric(df, c)
        return pd.Series(np.nan, index=df.index)

    coords["Z_basin_survival"] = first_existing_numeric(survival_candidates)
    coords["P_erasure"] = first_existing_numeric(erased_candidates)
    coords["P_topology_only_survival"] = first_existing_numeric(topology_only_candidates)
    coords["R_memory_retention"] = first_existing_numeric(retention_candidates)

    # Derived coordinates
    coords["XY_memory_radius"] = np.sqrt(
        coords["X_transport_memory"].fillna(0.0) ** 2
        + coords["Y_topology_memory"].fillna(0.0) ** 2
    )

    coords["topology_minus_transport_memory"] = (
        coords["Y_topology_memory"] - coords["X_transport_memory"]
    )

    coords["transport_topology_asymmetry"] = (
        coords["Y_topology_memory"] - coords["X_transport_memory"]
    ) / (
        coords["Y_topology_memory"].abs()
        + coords["X_transport_memory"].abs()
        + EPS
    )

    coords["normalized_entropy_memory"] = normalize_01(coords["E_entropy_memory"])
    coords["normalized_memory_strength"] = normalize_01(coords["M_memory_strength"])

    # A simple phenomenological basin depth proxy:
    # survival + retention + topology dominance - erasure
    coords["basin_depth_proxy"] = (
        coords["Z_basin_survival"].fillna(0.0)
        + coords["R_memory_retention"].fillna(0.0)
        + np.maximum(coords["topology_minus_transport_memory"].fillna(0.0), 0.0)
        - coords["P_erasure"].fillna(0.0)
    )

    coords["basin_depth_proxy_norm"] = normalize_01(coords["basin_depth_proxy"])

    coords["phase14_basin_class"] = coords.apply(classify_phase14_basin, axis=1)
    coords["relaxation_layer"] = coords.apply(assign_relaxation_layer, axis=1)

    # Save coordinate table
    coords.to_csv(OUT_COORDS, index=False)

    # Class summary
    class_summary = (
        coords["phase14_basin_class"]
        .value_counts(dropna=False)
        .rename_axis("phase14_basin_class")
        .reset_index(name="count")
    )
    class_summary["ratio"] = class_summary["count"] / len(coords)
    class_summary.to_csv(OUT_CLASS_SUMMARY, index=False)

    # Coordinate summary
    numeric_cols = [
        "X_transport_memory",
        "Y_topology_memory",
        "E_entropy_memory",
        "M_memory_strength",
        "Z_basin_survival",
        "P_erasure",
        "P_topology_only_survival",
        "R_memory_retention",
        "XY_memory_radius",
        "topology_minus_transport_memory",
        "transport_topology_asymmetry",
        "normalized_entropy_memory",
        "normalized_memory_strength",
        "basin_depth_proxy",
        "basin_depth_proxy_norm",
    ]

    rows = []
    for col in numeric_cols:
        s = coords[col]
        rows.append({
            "coordinate": col,
            "count": int(s.count()),
            "missing": int(s.isna().sum()),
            "mean": s.mean(skipna=True),
            "median": s.median(skipna=True),
            "std": s.std(skipna=True),
            "min": s.min(skipna=True),
            "max": s.max(skipna=True),
        })

    coord_summary = pd.DataFrame(rows)
    coord_summary.to_csv(OUT_COORD_SUMMARY, index=False)

    print("Phase14 Step02 complete.")
    print(f"Saved: {OUT_COORDS}")
    print(f"Saved: {OUT_CLASS_SUMMARY}")
    print(f"Saved: {OUT_COORD_SUMMARY}")
    print("")
    print(class_summary.to_string(index=False))
    print("")
    print(coord_summary.to_string(index=False))

if __name__ == "__main__":
    main()