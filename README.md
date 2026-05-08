# SRFM Quantum Phase14

Adaptive Basin Geometry and Persistent Structural Memory

## Overview

SRFM Quantum Phase14 investigates whether persistent topology-only structural memory can be interpreted as metastable basin geometry in adaptive coupling-topology space.

This phase extends the results of:

* Phase11: coherent transport dynamics
* Phase12: adaptive transport topology formation
* Phase13: persistent topology-only memory

Phase14 focuses on:

* basin geometry
* metastability
* perturbation-driven erosion
* memory-state redistribution
* boundary thickness
* adaptive structural memory landscapes

The central question is:

> Where does topology-only memory live in basin space, and how does perturbation move trajectories between memory basins?

---

## Core Concept

Phase13 established that:

observable transport output can converge while coupling topology retains persistent history.

Phase14 reinterprets this phenomenon geometrically.

Instead of treating memory as a binary protected state, Phase14 models structural memory as:

* metastable basin structure
* broad adaptive memory landscapes
* perturbation-degradable topology memory
* probabilistic redistribution between memory states

The key interpretation is:

transport memory and topology memory are partially decoupled.

---

## Main Findings

### F1 — Basin-coordinate memory landscape

Phase13 memory classes project into a structured basin-coordinate space.

Main coordinates:

* X = transport memory (H_phi)
* Y = topology memory (H_spectral)
* Z = survival probability

---

### F2 — Topology-only memory forms a stable basin region

Topology-only memory remains a distinct basin class:

* topology_only_basin ≈ 21.8%
* coupled_memory_basin ≈ 43.3%

---

### F3 — High basin entropy

The basin landscape exhibits high transition entropy.

Observed:

* mean basin entropy ≈ 1.1626
* max basin entropy ≈ 1.3740

Theoretical 4-state maximum:

S_max = log(4) ≈ 1.386

Interpretation:

memory outcomes compete probabilistically rather than collapsing deterministically.

---

### F4 — Gradual erosion dominates over collapse

No collapse-boundary regime was detected.

Instead:

* survival gradually decreases
* partial memory increases
* erasure remains limited

This supports:

basin erosion rather than abrupt collapse.

---

### F5 — Memory-state redistribution

Perturbation redistributes memory through graded transitions:

topology-only survival
→ partial topology memory
→ mixed / weak memory
→ erasure

Direct erasure remains a minority outcome.

---

## Scientific Interpretation

Phase14 suggests that persistent structural memory behaves as a metastable basin phenomenon in adaptive coupling-topology space.

The results support:

* basin-supported memory
* perturbation-degradable memory
* probabilistic memory redistribution
* relaxation hierarchy
* broad metastable boundary regions

rather than:

* sharp topological protection
* binary collapse thresholds
* frozen memory states

The observed dynamics resemble:

* hysteresis systems
* metastable basin dynamics
* glass-like redistribution behavior

although no physical equivalence is claimed.

---

## Repository Structure

```text
SRFM_QUANTUM_PHASE14
│
├─data
│  └─phase13_import
│
├─paper
│   └─figures
│
├─results
│
└─scripts
```

---

## Main Figures

### Figure1 — Basin coordinate map

Shows the separation of:

* topology-only memory
* coupled memory
* transport-dominant memory
* erased states

in H_phi vs H_spectral space.

---

### Figure2 — Basin entropy landscape

Shows high-entropy perturbation regions and distributed memory-state competition.

---

### Figure4 — Boundary regime map

Demonstrates:

* survival-dominant basins
* broad transition regions
* absence of collapse-boundary regimes

---

### Figure5 — Basin erosion dynamics

Shows gradual survival degradation and limited erasure growth under perturbation.

---

## Reproducibility

Main pipeline:

```powershell
python .\scripts\01_import_phase13_memory_landscape.py
python .\scripts\02_build_basin_coordinate_space.py
python .\scripts\03_analyze_basin_entropy.py
python .\scripts\04_build_basin_transition_matrix.py
python .\scripts\05_analyze_basin_boundary_thickness.py
python .\scripts\06_make_phase14_figures.py
python .\scripts\07_build_phase14_summary_tables.py
```

---

## Requirements

Main Python packages:

* numpy
* pandas
* matplotlib
* scipy
* networkx

---

## Publication

Zenodo:

(To be added)

GitHub:

(To be added)

---

## Citation

```text
Yoichi Tsujisawa,
SRFM Quantum Phase14:
Adaptive Basin Geometry and Persistent Structural Memory,
2026.
```

---

## Limitations

This project is a phenomenological adaptive-memory model.

It does NOT claim:

* physical quantum memory
* topological quantum protection
* quantum error correction
* hardware validation
* universal attractor theorem
* thermodynamic proof

---

## One-Sentence Summary

Persistent topology-only memory in SRFM Quantum systems behaves as a broad metastable basin geometry with gradual erosion and probabilistic redistribution rather than sharp protected collapse.
