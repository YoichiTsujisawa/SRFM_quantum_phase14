from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(r"E:\SRFM_QUANTUM_PHASE14")
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures"
PAPER_FIG_DIR = ROOT / "paper" / "figures"

FIG_DIR.mkdir(parents=True, exist_ok=True)
PAPER_FIG_DIR.mkdir(parents=True, exist_ok=True)

COORDS_FILE = RESULTS_DIR / "phase14_step02_basin_coordinates.csv"
ENTROPY_FILE = RESULTS_DIR / "phase14_step03_basin_entropy.csv"
EDGES_FILE = RESULTS_DIR / "phase14_step04_transition_graph_edges.csv"
BOUNDARY_FILE = RESULTS_DIR / "phase14_step05_boundary_thickness.csv"
THRESHOLD_FILE = RESULTS_DIR / "phase14_step05_collapse_thresholds.csv"

def savefig(name: str):
    out1 = FIG_DIR / name
    out2 = PAPER_FIG_DIR / name
    plt.tight_layout()
    plt.savefig(out1, dpi=300)
    plt.savefig(out2, dpi=300)
    plt.close()
    print(f"Saved: {out1}")
    print(f"Saved: {out2}")

def load_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)

def pivot_grid(df, value_col):
    return df.pivot_table(
        index="state_noise",
        columns="coupling_noise",
        values=value_col,
        aggfunc="mean"
    ).sort_index(ascending=True)

def figure1_basin_coordinate_map(coords: pd.DataFrame):
    plt.figure(figsize=(8, 6))

    classes = coords["phase14_basin_class"].fillna("unknown").unique()

    for cls in sorted(classes):
        g = coords[coords["phase14_basin_class"].fillna("unknown") == cls]
        plt.scatter(
            g["X_transport_memory"],
            g["Y_topology_memory"],
            s=18,
            alpha=0.65,
            label=f"{cls} (n={len(g)})"
        )

    plt.axvline(0.10, linestyle="--", linewidth=1)
    plt.axvline(0.50, linestyle="--", linewidth=1)
    plt.axhline(0.10, linestyle="--", linewidth=1)
    plt.axhline(0.50, linestyle="--", linewidth=1)

    plt.xlabel("Transport memory coordinate X = H_phi")
    plt.ylabel("Topology memory coordinate Y = H_spectral")
    plt.title("Phase14 Basin Coordinate Map")
    plt.legend(fontsize=7, loc="best")
    savefig("figure1_basin_coordinate_map.png")

def figure2_basin_entropy_heatmap(entropy: pd.DataFrame):
    grid = pivot_grid(entropy, "basin_entropy_norm_global")

    plt.figure(figsize=(7, 6))
    im = plt.imshow(
        grid.values,
        origin="lower",
        aspect="auto",
        extent=[
            grid.columns.min(),
            grid.columns.max(),
            grid.index.min(),
            grid.index.max(),
        ],
    )
    plt.colorbar(im, label="Normalized basin entropy")
    plt.xlabel("Coupling noise")
    plt.ylabel("State noise")
    plt.title("Phase14 Basin Entropy Landscape")
    savefig("figure2_basin_entropy_heatmap.png")

def figure3_transition_matrix_edges(edges: pd.DataFrame):
    labels = edges["target_state"].tolist()
    probs = edges["probability"].to_numpy()

    plt.figure(figsize=(8, 5))
    x = np.arange(len(labels))
    plt.bar(x, probs)

    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel("Transition probability")
    plt.ylim(0, max(0.5, probs.max() * 1.2))
    plt.title("Phase14 Global Memory-State Transition Edges")

    for i, p in enumerate(probs):
        plt.text(i, p + 0.01, f"{p:.3f}", ha="center", va="bottom", fontsize=9)

    savefig("figure3_transition_matrix_edges.png")

def figure4_boundary_regime_map(boundary: pd.DataFrame):
    regime_code = {
        "deep_survival_basin": 0,
        "survival_dominant_basin": 1,
        "broad_transition_boundary": 2,
        "collapse_boundary": 3,
        "mixed_boundary_region": 4,
    }

    boundary = boundary.copy()
    boundary["regime_code"] = boundary["boundary_regime"].map(regime_code)

    grid = pivot_grid(boundary, "regime_code")

    plt.figure(figsize=(7, 6))
    im = plt.imshow(
        grid.values,
        origin="lower",
        aspect="auto",
        extent=[
            grid.columns.min(),
            grid.columns.max(),
            grid.index.min(),
            grid.index.max(),
        ],
    )

    cbar = plt.colorbar(im)
    cbar.set_label("Boundary regime code")
    cbar.set_ticks(list(regime_code.values()))
    cbar.set_ticklabels(list(regime_code.keys()))

    plt.xlabel("Coupling noise")
    plt.ylabel("State noise")
    plt.title("Phase14 Boundary Regime Map")
    savefig("figure4_boundary_regime_map.png")

def figure5_survival_erasure_vs_noise(boundary: pd.DataFrame):
    data = boundary.copy()

    # Bin combined perturbation radius to avoid misleading zig-zag lines
    n_bins = 8
    data["noise_bin"] = pd.cut(
        data["combined_noise_radius"],
        bins=n_bins,
        include_lowest=True
    )

    by_bin = (
        data
        .groupby("noise_bin", observed=False)
        .agg(
            noise_radius_mean=("combined_noise_radius", "mean"),
            survival_mass_mean=("survival_mass", "mean"),
            survival_mass_std=("survival_mass", "std"),
            erasure_mass_mean=("erasure_mass", "mean"),
            erasure_mass_std=("erasure_mass", "std"),
            degradation_index_mean=("degradation_index", "mean"),
            degradation_index_std=("degradation_index", "std"),
            trial_points=("combined_noise_radius", "count"),
        )
        .reset_index()
        .dropna(subset=["noise_radius_mean"])
        .sort_values("noise_radius_mean")
    )

    plt.figure(figsize=(8, 5))

    # Raw points, faint
    plt.scatter(
        data["combined_noise_radius"],
        data["survival_mass"],
        s=18,
        alpha=0.25,
        label="Survival mass raw"
    )
    plt.scatter(
        data["combined_noise_radius"],
        data["erasure_mass"],
        s=18,
        alpha=0.25,
        label="Erasure mass raw"
    )
    plt.scatter(
        data["combined_noise_radius"],
        data["degradation_index"],
        s=18,
        alpha=0.25,
        label="Degradation index raw"
    )

    # Binned mean trend
    plt.errorbar(
        by_bin["noise_radius_mean"],
        by_bin["survival_mass_mean"],
        yerr=by_bin["survival_mass_std"],
        marker="o",
        linewidth=2,
        capsize=3,
        label="Survival mass binned mean"
    )
    plt.errorbar(
        by_bin["noise_radius_mean"],
        by_bin["erasure_mass_mean"],
        yerr=by_bin["erasure_mass_std"],
        marker="o",
        linewidth=2,
        capsize=3,
        label="Erasure mass binned mean"
    )
    plt.errorbar(
        by_bin["noise_radius_mean"],
        by_bin["degradation_index_mean"],
        yerr=by_bin["degradation_index_std"],
        marker="o",
        linewidth=2,
        capsize=3,
        label="Degradation index binned mean"
    )

    plt.xlabel("Combined perturbation radius")
    plt.ylabel("Probability / index")
    plt.title("Phase14 Basin Erosion vs Perturbation Strength")
    plt.legend(fontsize=8)
    savefig("figure5_survival_erasure_vs_noise.png")

def figure6_topology_survival_partial_erasure(boundary: pd.DataFrame):
    by_coupling = (
        boundary
        .groupby("coupling_noise", dropna=False)
        .agg(
            p_topology_only_memory_survived=("p_topology_only_memory_survived", "mean"),
            p_partial_topology_memory=("p_partial_topology_memory", "mean"),
            p_mixed_or_weak_memory=("p_mixed_or_weak_memory", "mean"),
            p_memory_erased=("p_memory_erased", "mean"),
        )
        .reset_index()
        .sort_values("coupling_noise")
    )

    plt.figure(figsize=(8, 5))
    plt.plot(
        by_coupling["coupling_noise"],
        by_coupling["p_topology_only_memory_survived"],
        marker="o",
        label="Topology-only survived"
    )
    plt.plot(
        by_coupling["coupling_noise"],
        by_coupling["p_partial_topology_memory"],
        marker="o",
        label="Partial topology memory"
    )
    plt.plot(
        by_coupling["coupling_noise"],
        by_coupling["p_mixed_or_weak_memory"],
        marker="o",
        label="Mixed / weak memory"
    )
    plt.plot(
        by_coupling["coupling_noise"],
        by_coupling["p_memory_erased"],
        marker="o",
        label="Memory erased"
    )

    plt.xlabel("Coupling noise")
    plt.ylabel("Mean transition probability")
    plt.title("Phase14 Memory-State Redistribution along Coupling Perturbation")
    plt.legend()
    savefig("figure6_memory_state_redistribution_by_coupling_noise.png")

def figure7_boundary_thickness_heatmap(boundary: pd.DataFrame):
    grid = pivot_grid(boundary, "boundary_thickness_proxy")

    plt.figure(figsize=(7, 6))
    im = plt.imshow(
        grid.values,
        origin="lower",
        aspect="auto",
        extent=[
            grid.columns.min(),
            grid.columns.max(),
            grid.index.min(),
            grid.index.max(),
        ],
    )
    plt.colorbar(im, label="Boundary thickness proxy")
    plt.xlabel("Coupling noise")
    plt.ylabel("State noise")
    plt.title("Phase14 Basin Boundary Thickness Proxy")
    savefig("figure7_boundary_thickness_heatmap.png")

def main():
    coords = load_required(COORDS_FILE)
    entropy = load_required(ENTROPY_FILE)
    edges = load_required(EDGES_FILE)
    boundary = load_required(BOUNDARY_FILE)

    figure1_basin_coordinate_map(coords)
    figure2_basin_entropy_heatmap(entropy)
    figure3_transition_matrix_edges(edges)
    figure4_boundary_regime_map(boundary)
    figure5_survival_erasure_vs_noise(boundary)
    figure6_topology_survival_partial_erasure(boundary)
    figure7_boundary_thickness_heatmap(boundary)

    manifest = pd.DataFrame([
        {
            "figure": "figure1_basin_coordinate_map.png",
            "role": "Projects Phase13 memory classes into Phase14 basin-coordinate space using H_phi and H_spectral.",
        },
        {
            "figure": "figure2_basin_entropy_heatmap.png",
            "role": "Shows where multiple memory states compete under state/coupling perturbations.",
        },
        {
            "figure": "figure3_transition_matrix_edges.png",
            "role": "Summarizes global transition probabilities from initial topology memory to survival, partial retention, weakening, and erasure.",
        },
        {
            "figure": "figure4_boundary_regime_map.png",
            "role": "Maps deep survival, survival-dominant, and broad transition boundary regimes.",
        },
        {
            "figure": "figure5_survival_erasure_vs_noise.png",
            "role": "Tests whether memory loss behaves like abrupt collapse or gradual erosion with perturbation strength.",
        },
        {
            "figure": "figure6_memory_state_redistribution_by_coupling_noise.png",
            "role": "Shows redistribution among memory states as coupling perturbation increases.",
        },
        {
            "figure": "figure7_boundary_thickness_heatmap.png",
            "role": "Visualizes broad basin-boundary thickness rather than a sharp collapse line.",
        },
    ])

    manifest.to_csv(RESULTS_DIR / "phase14_step06_figure_manifest.csv", index=False)

    print("Phase14 Step06 figures complete.")
    print(f"Saved manifest: {RESULTS_DIR / 'phase14_step06_figure_manifest.csv'}")

if __name__ == "__main__":
    main()