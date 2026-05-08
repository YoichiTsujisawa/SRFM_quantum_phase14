from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
RESULTS = ROOT / "results"
PAPER = ROOT / "paper"
FIGS = PAPER / "figures"

PAPER.mkdir(parents=True, exist_ok=True)

FILES = {
    "step01": RESULTS / "phase14_step01_import_summary.csv",
    "step02_class": RESULTS / "phase14_step02_basin_class_summary.csv",
    "step02_coord": RESULTS / "phase14_step02_basin_coordinate_summary.csv",
    "step03": RESULTS / "phase14_step03_entropy_headline_summary.csv",
    "step04": RESULTS / "phase14_step04_transition_headline_summary.csv",
    "step05": RESULTS / "phase14_step05_boundary_headline_summary.csv",
    "step05_thresholds": RESULTS / "phase14_step05_collapse_thresholds.csv",
    "step06_manifest": RESULTS / "phase14_step06_figure_manifest.csv",
}

OUT_FINDINGS = RESULTS / "phase14_step07_core_findings_summary.csv"
OUT_METRICS = RESULTS / "phase14_step07_metric_summary.csv"
OUT_MANIFEST = RESULTS / "phase14_step07_figure_manifest.csv"
OUT_MD = PAPER / "phase14_interim_summary.md"

def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)

def first(df: pd.DataFrame, col: str, default=np.nan):
    return df[col].iloc[0] if col in df.columns and len(df) else default

def fmt(x, digits=6):
    try:
        if pd.isna(x):
            return "NA"
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def main():
    step01 = read_csv(FILES["step01"])
    step02_class = read_csv(FILES["step02_class"])
    step02_coord = read_csv(FILES["step02_coord"])
    step03 = read_csv(FILES["step03"])
    step04 = read_csv(FILES["step04"])
    step05 = read_csv(FILES["step05"])
    thresholds = read_csv(FILES["step05_thresholds"])
    manifest = read_csv(FILES["step06_manifest"])

    def class_count(name):
        row = step02_class[step02_class["phase14_basin_class"] == name]
        if len(row) == 0:
            return 0, 0.0
        return int(row["count"].iloc[0]), float(row["ratio"].iloc[0])

    topology_count, topology_ratio = class_count("topology_only_basin")
    stable_topology_count, stable_topology_ratio = class_count("stable_topology_only_basin")
    coupled_count, coupled_ratio = class_count("coupled_memory_basin")
    stable_coupled_count, stable_coupled_ratio = class_count("stable_coupled_memory_basin")
    transition_count, transition_ratio = class_count("transition_basin")
    erased_count, erased_ratio = class_count("erased_basin")
    transport_count, transport_ratio = class_count("transport_dominant_basin")

    findings = pd.DataFrame([
        {
            "id": "F1",
            "finding": "Phase13 memory classes project into a structured Phase14 basin-coordinate landscape.",
            "metric": "topology_only_basin + stable_topology_only_basin",
            "value": topology_count + stable_topology_count,
            "interpretation": "Topology-only memory remains a distinct basin class in H_phi vs H_spectral space.",
        },
        {
            "id": "F2",
            "finding": "Coupled transport-topology memory remains the dominant basin class.",
            "metric": "coupled_memory_basin + stable_coupled_memory_basin",
            "value": coupled_count + stable_coupled_count,
            "interpretation": "Transport and topology memory frequently coexist before relaxation separation.",
        },
        {
            "id": "F3",
            "finding": "Basin entropy is high across perturbation space.",
            "metric": "mean_basin_entropy",
            "value": first(step03, "mean_basin_entropy"),
            "interpretation": "Memory outcomes are multi-state and competitive rather than deterministic.",
        },
        {
            "id": "F4",
            "finding": "Maximum basin entropy approaches the four-state entropy limit.",
            "metric": "max_basin_entropy",
            "value": first(step03, "max_basin_entropy"),
            "interpretation": "Some perturbation regions exhibit nearly maximal competition among memory states.",
        },
        {
            "id": "F5",
            "finding": "Topology memory mostly survives as full or partial retention.",
            "metric": "global_survival_mass",
            "value": first(step04, "global_survival_mass"),
            "interpretation": "Survival plus partial topology retention accounts for most perturbation outcomes.",
        },
        {
            "id": "F6",
            "finding": "Direct memory erasure remains a minority outcome.",
            "metric": "global_erasure_mass",
            "value": first(step04, "global_erasure_mass"),
            "interpretation": "Perturbation usually redistributes memory rather than directly annihilating it.",
        },
        {
            "id": "F7",
            "finding": "Transition entropy remains high in the global transition matrix.",
            "metric": "global_transition_entropy_norm",
            "value": first(step04, "global_transition_entropy_norm"),
            "interpretation": "Memory transitions form a probabilistic basin network.",
        },
        {
            "id": "F8",
            "finding": "No collapse-boundary regime was detected in the perturbation grid.",
            "metric": "collapse_boundary_count",
            "value": first(step05, "collapse_boundary_count"),
            "interpretation": "Memory degradation is better described as basin erosion than abrupt collapse.",
        },
        {
            "id": "F9",
            "finding": "Broad transition boundaries occupy a large fraction of perturbation space.",
            "metric": "broad_transition_boundary_count",
            "value": first(step05, "broad_transition_boundary_count"),
            "interpretation": "Memory basin boundaries are thick and metastable rather than sharp.",
        },
        {
            "id": "F10",
            "finding": "Erasure remains bounded even at the strongest tested perturbation conditions.",
            "metric": "max_erasure_mass",
            "value": first(step05, "max_erasure_mass"),
            "interpretation": "Even high perturbation does not make erasure the dominant outcome.",
        },
    ])

    metrics = pd.DataFrame([
        {"metric": "output_rows", "value": first(step01, "output_rows")},
        {"metric": "topology_only_basin_total", "value": topology_count + stable_topology_count},
        {"metric": "topology_only_basin_total_ratio", "value": topology_ratio + stable_topology_ratio},
        {"metric": "coupled_memory_basin_total", "value": coupled_count + stable_coupled_count},
        {"metric": "coupled_memory_basin_total_ratio", "value": coupled_ratio + stable_coupled_ratio},
        {"metric": "transition_basin_count", "value": transition_count},
        {"metric": "transport_dominant_basin_count", "value": transport_count},
        {"metric": "erased_basin_count", "value": erased_count},
        {"metric": "mean_basin_entropy", "value": first(step03, "mean_basin_entropy")},
        {"metric": "max_basin_entropy", "value": first(step03, "max_basin_entropy")},
        {"metric": "global_survival_mass", "value": first(step04, "global_survival_mass")},
        {"metric": "global_erasure_mass", "value": first(step04, "global_erasure_mass")},
        {"metric": "global_degradation_index", "value": first(step04, "global_degradation_index")},
        {"metric": "global_transition_entropy_norm", "value": first(step04, "global_transition_entropy_norm")},
        {"metric": "mean_survival_mass", "value": first(step05, "mean_survival_mass")},
        {"metric": "min_survival_mass", "value": first(step05, "min_survival_mass")},
        {"metric": "mean_erasure_mass", "value": first(step05, "mean_erasure_mass")},
        {"metric": "max_erasure_mass", "value": first(step05, "max_erasure_mass")},
        {"metric": "mean_boundary_thickness_proxy", "value": first(step05, "mean_boundary_thickness_proxy")},
        {"metric": "max_boundary_thickness_proxy", "value": first(step05, "max_boundary_thickness_proxy")},
        {"metric": "deep_survival_basin_count", "value": first(step05, "deep_survival_basin_count")},
        {"metric": "survival_dominant_basin_count", "value": first(step05, "survival_dominant_basin_count")},
        {"metric": "broad_transition_boundary_count", "value": first(step05, "broad_transition_boundary_count")},
        {"metric": "collapse_boundary_count", "value": first(step05, "collapse_boundary_count")},
    ])

    manifest = manifest.copy()
    manifest.to_csv(OUT_MANIFEST, index=False)
    findings.to_csv(OUT_FINDINGS, index=False)
    metrics.to_csv(OUT_METRICS, index=False)

    md = f"""---
title: "SRFM Quantum Phase14: Adaptive Basin Geometry and Persistent Structural Memory"
author: "Yoichi Tsujisawa"
date: "2026-05-08"
geometry: margin=1in
fontsize: 11pt
---

# Abstract

This Phase14 report extends the Phase13 discovery of persistent topology-only structural memory by projecting adaptive memory outcomes into a basin-coordinate representation. The analysis shows that persistent topology memory is not best interpreted as a sharply protected state. Instead, it appears as a broad metastable basin geometry with high basin entropy, probabilistic memory-state redistribution, and gradual perturbation-driven erosion.

The central result is that topology memory frequently survives as either full topology-only memory or partial topology memory, while direct erasure remains a minority outcome. Across the tested perturbation grid, no collapse-boundary regime was detected. This supports the interpretation that SRFM Quantum structural memory is basin-supported, perturbation-degradable, and geometrically organized.

# 1. Introduction

Phase13 established that adaptive transport systems can erase observable transport differences while preserving persistent structural memory in coupling topology. In particular, topology-only memory was observed when transport memory was nearly zero while spectral topology memory remained high.

Phase14 asks a different question:

**Where does topology-only memory live in basin space, and how does perturbation move trajectories between memory basins?**

The working hypothesis is that persistent adaptive structural memory survives because coupling-topology trajectories become trapped in metastable basin regions after observable transport variables relax.

# 2. Basin Coordinate Construction

Phase14 uses a three-layer state decomposition.

- Transport state: observable transport memory.
- Topology state: hidden structural memory in coupling topology.
- Basin state: perturbation-conditioned memory survival, partial retention, weakening, or erasure.

The minimal basin coordinates are:

- X = H_phi
- Y = H_spectral
- Z = basin survival probability

The primary basin classes are:

- topology-only basin
- coupled memory basin
- transport-dominant basin
- erased basin
- transition basin

The imported Phase14 coordinate landscape contains {int(first(step01, "output_rows"))} memory points.

![Figure 1. Phase14 basin coordinate map.](figures/figure1_basin_coordinate_map.png){{width=95%}}

# 3. Basin Class Structure

The coordinate projection separates memory states into distinct regions.

Key basin counts:

| Basin class | Count | Ratio |
|---|---:|---:|
| topology-only basin total | {topology_count + stable_topology_count} | {fmt(topology_ratio + stable_topology_ratio)} |
| coupled memory basin total | {coupled_count + stable_coupled_count} | {fmt(coupled_ratio + stable_coupled_ratio)} |
| transition basin | {transition_count} | {fmt(transition_ratio)} |
| transport-dominant basin | {transport_count} | {fmt(transport_ratio)} |
| erased basin | {erased_count} | {fmt(erased_ratio)} |

This confirms that topology-only memory remains a distinct basin-coordinate region rather than a residual artifact of transport memory.

# 4. Basin Entropy

Basin entropy was computed over perturbation-conditioned memory-state distributions:

$$
S_{{basin}} = - \\sum_i p_i \\log(p_i)
$$

where p_i is the occupancy probability of memory state i.

The observed mean basin entropy was {fmt(first(step03, "mean_basin_entropy"))}, and the maximum basin entropy was {fmt(first(step03, "max_basin_entropy"))}. With four memory states, the theoretical maximum is log(4), approximately 1.386. The observed maximum is therefore close to maximal state competition.

![Figure 2. Basin entropy landscape.](figures/figure2_basin_entropy_heatmap.png){{width=90%}}

The high entropy regions indicate that memory does not collapse deterministically into a single outcome. Instead, survival, partial retention, weakening, and erasure compete across broad perturbation regions.

# 5. Basin Transition Matrix

The perturbation outcomes were summarized as transition probabilities from initial topology memory into four memory states.

![Figure 3. Global memory-state transition edges.](figures/figure3_transition_matrix_edges.png){{width=85%}}

The global transition probabilities were:

| Outcome | Probability |
|---|---:|
| topology-only memory survived | {fmt(first(step04, "global_p_topology_only_memory_survived"))} |
| partial topology memory | {fmt(first(step04, "global_p_partial_topology_memory"))} |
| mixed or weak memory | {fmt(first(step04, "global_p_mixed_or_weak_memory"))} |
| memory erased | {fmt(first(step04, "global_p_memory_erased"))} |

The survival mass was {fmt(first(step04, "global_survival_mass"))}, while the erasure mass was {fmt(first(step04, "global_erasure_mass"))}. This shows that perturbation usually redistributes structural memory into partial or weakened states rather than directly erasing it.

# 6. Basin Boundary Regimes

Boundary regimes were classified from survival mass, erasure mass, transition entropy, and degradation index.

![Figure 4. Boundary regime map.](figures/figure4_boundary_regime_map.png){{width=90%}}

The boundary regime counts were:

| Boundary regime | Count |
|---|---:|
| deep survival basin | {int(first(step05, "deep_survival_basin_count"))} |
| survival-dominant basin | {int(first(step05, "survival_dominant_basin_count"))} |
| broad transition boundary | {int(first(step05, "broad_transition_boundary_count"))} |
| collapse boundary | {int(first(step05, "collapse_boundary_count"))} |

The absence of detected collapse-boundary regimes is important. It supports the interpretation that memory loss behaves as basin erosion rather than abrupt collapse.

# 7. Erosion Dynamics

To test whether memory degradation is abrupt or gradual, survival mass, erasure mass, and degradation index were plotted against combined perturbation radius.

![Figure 5. Basin erosion vs perturbation strength.](figures/figure5_survival_erasure_vs_noise.png){{width=90%}}

Survival mass decreases gradually, while erasure mass increases only weakly. The maximum erasure mass was {fmt(first(step05, "max_erasure_mass"))}, and the minimum survival mass was {fmt(first(step05, "min_survival_mass"))}. Thus, even under strong perturbation, direct erasure does not become the dominant outcome.

# 8. Memory-State Redistribution

The redistribution of memory states along coupling perturbation shows that memory loss proceeds primarily through partial degradation.

![Figure 6. Memory-state redistribution by coupling perturbation.](figures/figure6_memory_state_redistribution_by_coupling_noise.png){{width=90%}}

This supports a graded memory-loss pathway:

topology-only survival -> partial topology memory -> mixed or weak memory -> erasure

The key point is that perturbation does not simply destroy memory. It redistributes memory probability across several metastable outcomes.

# 9. Boundary Thickness

A boundary thickness proxy was computed from transition entropy and dominant-state probability. High values indicate distributed basin competition rather than a sharp transition line.

![Figure 7. Basin boundary thickness proxy.](figures/figure7_boundary_thickness_heatmap.png){{width=90%}}

The mean boundary thickness proxy was {fmt(first(step05, "mean_boundary_thickness_proxy"))}, and the maximum was {fmt(first(step05, "max_boundary_thickness_proxy"))}. The broad high-thickness regions support the interpretation of thick metastable basin boundaries.

# 10. Core Findings

| ID | Finding | Metric | Value |
|---|---|---|---:|
"""

    for _, r in findings.iterrows():
        md += f"| {r['id']} | {r['finding']} | {r['metric']} | {fmt(r['value'])} |\n"

    md += f"""

# 11. Scientific Interpretation

Phase14 suggests that persistent topology-only memory is a basin-geometric phenomenon. The memory is not simply a high transport state, nor a permanently protected topological state. Instead, it appears as a metastable region of coupling-topology space where transport variables can relax while structural topology differences persist.

The most important conceptual transition is:

Phase13: topology remembers transport history.

Phase14: topology memory lives in broad metastable basin geometries.

The results also suggest a relaxation hierarchy:

$$
\\tau_{{transport}} \\ll \\tau_{{topology}}
$$

This does not yet prove a rigorous attractor theorem. However, it gives a reproducible phenomenological basis for describing adaptive structural memory as a basin-supported and perturbation-erodible state.

# 12. Limitations

This Phase14 report is numerical and phenomenological.

It does not claim:

- true topological protection
- universal attractor theorem
- physical quantum memory
- quantum error correction
- quantum hardware validation
- thermodynamic proof
- many-body derivation

The basin classes are threshold-based and should be refined in future phases. The current analysis uses Phase13 perturbation outputs rather than new microscopic simulations.

# 13. Conclusion

Phase14 shows that persistent topology-only memory in SRFM Quantum systems is organized as a broad adaptive basin geometry. Memory degradation is not dominated by abrupt collapse. Instead, perturbation produces gradual erosion and probabilistic redistribution among survival, partial retention, weakening, and erasure states.

One-sentence summary:

**Persistent topology-only memory in SRFM Quantum systems is supported by broad metastable basin geometry with gradual erosion and probabilistic redistribution, rather than by sharp protected thresholds.**
"""

    OUT_MD.write_text(md, encoding="utf-8")

    print("Phase14 Step07 complete.")
    print(f"Saved: {OUT_FINDINGS}")
    print(f"Saved: {OUT_METRICS}")
    print(f"Saved: {OUT_MANIFEST}")
    print(f"Saved: {OUT_MD}")

if __name__ == "__main__":
    main()