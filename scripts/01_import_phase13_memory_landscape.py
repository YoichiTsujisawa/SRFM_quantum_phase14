from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
IN_DIR = ROOT / "data" / "phase13_import"
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "hysteresis": "phase13_step03c_hysteresis_summary_tanhbounded.csv",
    "topology_zone": "phase13_step06b_topology_only_memory_zone.csv",
    "topology_summary": "phase13_step06b_topology_only_memory_summary.csv",
    "classified_points": "phase13_step06c_memory_classified_points.csv",
    "lifetime_summary": "phase13_step07_memory_lifetime_summary.csv",
    "robustness_trials": "phase13_step08_memory_robustness_trials.csv",
    "robustness_summary": "phase13_step08_memory_robustness_summary.csv",
    "phase_transition": "phase13_step08_memory_phase_transition.csv",
    "core_findings": "phase13_step09_core_findings_summary.csv",
}

def read_csv_required(name: str, filename: str) -> pd.DataFrame:
    path = IN_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    df = pd.read_csv(path)
    df["source_table"] = name
    return df

def normalize_case_id(df: pd.DataFrame) -> pd.DataFrame:
    candidates = [
        "case_id",
        "sample_id",
        "case_name",
        "sample_name",
        "label",
        "trial_id",
    ]

    found = None
    for c in candidates:
        if c in df.columns:
            found = c
            break

    if found is None:
        df["phase14_case_key"] = np.arange(len(df)).astype(str)
    else:
        df["phase14_case_key"] = df[found].astype(str)

    return df

def add_safe_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def classify_basin_from_metrics(row) -> str:
    h_phi = row.get("H_phi", np.nan)
    h_spec = row.get("H_spectral_radius", np.nan)

    if pd.isna(h_phi) or pd.isna(h_spec):
        return "unclassified"

    if h_phi < 0.10 and h_spec > 0.50:
        return "topology_only_basin"
    if h_phi > 0.50 and h_spec > 0.50:
        return "coupled_memory_basin"
    if h_phi > 0.50 and h_spec <= 0.40:
        return "transport_dominant_basin"
    if h_phi < 0.10 and h_spec < 0.10:
        return "erased_basin"

    return "transition_basin"

def main():
    loaded = {}
    import_rows = []

    for name, filename in FILES.items():
        df = read_csv_required(name, filename)
        df = normalize_case_id(df)
        loaded[name] = df

        import_rows.append({
            "table_name": name,
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": "|".join(df.columns.astype(str)),
        })

    hysteresis = loaded["hysteresis"].copy()

    numeric_cols = [
        "H_phi",
        "H_sync",
        "H_spectral_radius",
        "H_entropy",
        "memory_strength",
        "phi_forward",
        "phi_backward",
        "spectral_radius_forward",
        "spectral_radius_backward",
        "entropy_forward",
        "entropy_backward",
    ]
    hysteresis = add_safe_numeric(hysteresis, numeric_cols)

    if "H_phi" in hysteresis.columns and "H_spectral_radius" in hysteresis.columns:
        hysteresis["phase14_initial_basin_class"] = hysteresis.apply(
            classify_basin_from_metrics,
            axis=1
        )
    else:
        hysteresis["phase14_initial_basin_class"] = "unclassified"

    # Optional merge with robustness summary if case key overlaps
    robustness_summary = loaded["robustness_summary"].copy()
    robustness_summary = normalize_case_id(robustness_summary)

    robust_numeric_candidates = [
        "survival_probability",
        "erased_probability",
        "topology_only_survival_probability",
        "partial_topology_memory_probability",
        "mean_memory_retention_ratio",
        "memory_retention_ratio",
    ]
    robustness_summary = add_safe_numeric(robustness_summary, robust_numeric_candidates)

    overlap = set(hysteresis["phase14_case_key"]) & set(robustness_summary["phase14_case_key"])

    if len(overlap) > 0:
        keep_cols = ["phase14_case_key"]
        keep_cols += [c for c in robust_numeric_candidates if c in robustness_summary.columns]
        keep_cols = list(dict.fromkeys(keep_cols))

        basin_import = hysteresis.merge(
            robustness_summary[keep_cols],
            on="phase14_case_key",
            how="left"
        )
        merge_status = "merged_by_phase14_case_key"
    else:
        basin_import = hysteresis.copy()
        merge_status = "no_case_key_overlap_with_robustness_summary"

    # Save main Phase14 import table
    basin_import.to_csv(
        OUT_DIR / "phase14_step01_memory_landscape_import.csv",
        index=False
    )

    # Basin class summary
    basin_class_summary = (
        basin_import["phase14_initial_basin_class"]
        .value_counts(dropna=False)
        .rename_axis("phase14_initial_basin_class")
        .reset_index(name="count")
    )
    basin_class_summary["ratio"] = basin_class_summary["count"] / len(basin_import)

    basin_class_summary.to_csv(
        OUT_DIR / "phase14_step01_initial_basin_class_summary.csv",
        index=False
    )

    # Import summary
    import_summary = pd.DataFrame(import_rows)
    import_summary.to_csv(
        OUT_DIR / "phase14_step01_import_file_summary.csv",
        index=False
    )

    headline = pd.DataFrame([{
        "phase": "Phase14",
        "step": "Step01",
        "purpose": "Import Phase13 memory landscape for adaptive basin geometry analysis",
        "hysteresis_rows": len(loaded["hysteresis"]),
        "topology_zone_rows": len(loaded["topology_zone"]),
        "classified_points_rows": len(loaded["classified_points"]),
        "lifetime_summary_rows": len(loaded["lifetime_summary"]),
        "robustness_trials_rows": len(loaded["robustness_trials"]),
        "robustness_summary_rows": len(loaded["robustness_summary"]),
        "phase_transition_rows": len(loaded["phase_transition"]),
        "core_findings_rows": len(loaded["core_findings"]),
        "output_rows": len(basin_import),
        "case_key_overlap_with_robustness_summary": len(overlap),
        "merge_status": merge_status,
        "topology_only_basin_count": int((basin_import["phase14_initial_basin_class"] == "topology_only_basin").sum()),
        "coupled_memory_basin_count": int((basin_import["phase14_initial_basin_class"] == "coupled_memory_basin").sum()),
        "transport_dominant_basin_count": int((basin_import["phase14_initial_basin_class"] == "transport_dominant_basin").sum()),
        "erased_basin_count": int((basin_import["phase14_initial_basin_class"] == "erased_basin").sum()),
        "transition_basin_count": int((basin_import["phase14_initial_basin_class"] == "transition_basin").sum()),
        "unclassified_count": int((basin_import["phase14_initial_basin_class"] == "unclassified").sum()),
    }])

    headline.to_csv(
        OUT_DIR / "phase14_step01_import_summary.csv",
        index=False
    )

    print("Phase14 Step01 complete.")
    print(f"Saved: {OUT_DIR / 'phase14_step01_memory_landscape_import.csv'}")
    print(f"Saved: {OUT_DIR / 'phase14_step01_import_summary.csv'}")
    print(f"Saved: {OUT_DIR / 'phase14_step01_initial_basin_class_summary.csv'}")
    print(f"Saved: {OUT_DIR / 'phase14_step01_import_file_summary.csv'}")
    print("")
    print(headline.to_string(index=False))
    print("")
    print(basin_class_summary.to_string(index=False))

if __name__ == "__main__":
    main()