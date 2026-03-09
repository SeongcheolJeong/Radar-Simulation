# Our Project vs. RadarSimPy vs. Ansys AVx

## Purpose

Use this page when you need a direct answer to these questions:

- Is this project better than plain `RadarSimPy`?
- Is this project already comparable to `Ansys AVx`?
- What is the current physics level of this simulator?

This is a positioning and physics-level document, not a UI manual.

## Bottom Line

The most accurate short statement is:

```text
plain RadarSimPy < this project < Ansys AVx
```

That statement is true only when the comparison is broken down by layer:

- this project is stronger than plain `RadarSimPy` as a hybrid simulation workbench
- this project is not yet an `Ansys AVx`-class real-time production sensor platform

## Scope Of Comparison

This document compares three things:

1. `RadarSimPy` used directly as a radar simulator
2. this repository, which can use `RadarSimPy` but adds its own backend abstraction, path pipeline, antenna handling, compensation, validation, and frontend workflow
3. `Ansys AVxcelerate Sensors` and `Ansys Perceive EM` as current commercial high-fidelity references

## What This Project Adds Beyond Plain RadarSimPy

### 1. A backend-agnostic simulation pipeline

This repository is explicitly structured around:

- `PathGenerator`
- `AntennaModel`
- `FmcwMultiplexingSynthesizer`
- `OutputWriter`

See:

- [03_architecture.md](03_architecture.md)

That separation matters because the project can run:

- low fidelity through `radarsimpy_rt`
- high fidelity through `sionna_rt`
- higher-fidelity asymptotic EM path generation through `po_sbr_rt`

while still writing the same output contract.

Core execution entrypoints:

- [scene_pipeline.py](../src/avxsim/scene_pipeline.py)

### 2. Stronger antenna and polarization handling

Plain `RadarSimPy` is useful for radar system and signal-chain work, but this project adds repo-level antenna handling such as:

- FFD antenna patterns
- Jones vector and matrix handling
- global Jones transforms

Shared synth and antenna logic:

- [synth.py](../src/avxsim/synth.py)
- [scene_pipeline.py](../src/avxsim/scene_pipeline.py)

### 3. Compensation and realism layers above the raw path list

This repository includes explicit compensation hooks for:

- wideband correction
- manifold asset gain and phase
- diffuse spawn
- clutter spawn

See:

- [radar_compensation.py](../src/avxsim/radar_compensation.py)

This means the project is not only a path tracer or only a waveform simulator. It can adjust the returned path set before synthesis.

### 4. A stronger validation and operator workflow

Plain `RadarSimPy` does not provide this repository's integrated workflow for:

- low-vs-high track comparison
- frontend runtime selection
- artifact inspection
- stable evidence reports
- release-gate and parity validation

Relevant documents and reports:

- [289_canonical_validation_scenario_pack.md](289_canonical_validation_scenario_pack.md)
- [docs/reports/README.md](reports/README.md)
- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

## Where This Project Is Still Below Ansys AVx

This project should not be described as already equivalent to `Ansys AVx`.

The official `Ansys AVxcelerate Sensors` positioning is for physically accurate real-time sensor simulation, SiL/HiL usage, multi-sensor workflows, and GPU radar with multi-bounce and dielectric transmission behavior. Official `Ansys Perceive EM` positioning is for a PO-based SBR solver with GPU acceleration, large-scale radar/wireless modeling, and real-time channel modeling. Those are product-level claims, not just algorithm claims.

Official references:

- [Ansys AVxcelerate Sensors](https://www.ansys.com/products/av-simulation/ansys-avxcelerate-sensors)
- [Ansys Perceive EM](https://www.ansys.com/products/electronics/ansys-perceive-em)

Practically, this repository is still below that level in several areas.

### 1. Real-time productization

This repository has working high-fidelity backends, but the current interactive high-fidelity recommendation is still:

- `Sionna-style RT` for interactive frontend use
- `PO-SBR` for dedicated validation

Evidence:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

That is not the same as claiming a broadly real-time, GPU-scaled production radar platform.

### 2. Scene and material complexity

`Ansys AVx` and `Perceive EM` are positioned around large-scale scenes, richer material behavior, multi-bounce, transmission, and productized solver stacks.

This repository has:

- path-based high-fidelity options
- a PO-SBR backend path
- stronger-than-basic scene realism

but it is still a repo-scale hybrid simulator, not a commercial end-to-end autonomy sensor platform.

### 3. HIL/raw-sensor production story

`Ansys AVx` explicitly presents raw-sensor and HiL/SiL/MiL connectivity as product capabilities.

This repository has strong evidence export, output contracts, and operator workflows, but that is not the same as a mature commercial raw-sensor integration product.

## Physics Level Of This Project

The most accurate statement is:

```text
This project is a hybrid radar simulator.
It is not a full-wave Maxwell solver.
Its physics level depends on which backend generated the path set.
```

## Shared Physics Strength

Across all tracks, this repository is strongest in:

- FMCW signal-chain synthesis
- ADC generation from path data
- downstream radar-map generation
- antenna/polarization augmentation
- output and evidence contracts

That shared signal-chain layer lives mostly in:

- [synth.py](../src/avxsim/synth.py)
- [scene_pipeline.py](../src/avxsim/scene_pipeline.py)

## Physics Ladder By Runtime Track

### Low Fidelity: `RadarSimPy + FFD`

This level is best described as:

- strong system-level radar simulation
- good waveform and DSP realism
- moderate antenna realism when FFD/Jones are used
- limited scene EM realism compared with ray-tracing or PO-SBR backends

Practical interpretation:

- signal-chain physics: strong
- antenna and polarization physics: moderate to strong
- scene propagation and scattering realism: low to moderate

Relevant provider:

- [radarsimpy_rt_provider.py](../src/avxsim/runtime_providers/radarsimpy_rt_provider.py)

### High Fidelity: `Sionna-style RT`

This level is best described as:

- geometric ray/path realism above low fidelity
- path generation from ray-intersection style logic
- better propagation realism than plain analytic or point-target-only flow
- still not full EM

Practical interpretation:

- signal-chain physics: strong
- antenna and polarization physics: moderate to strong
- propagation realism: moderate
- scattering realism: moderate at best

Relevant provider:

- [mitsuba_rt_provider.py](../src/avxsim/runtime_providers/mitsuba_rt_provider.py)

### High Fidelity: `PO-SBR`

This is currently the highest-physics backend path in the repository.

It is best described as:

- asymptotic EM-oriented path generation
- PO/SBR-style scattering workflow
- better large-scene physical plausibility than the low-fidelity path
- still not a full-wave solver

Practical interpretation:

- signal-chain physics: strong
- antenna and polarization physics: moderate to strong
- propagation and scattering realism: moderate to high within repo scope
- full-wave EM: no

Relevant provider:

- [po_sbr_rt_provider.py](../src/avxsim/runtime_providers/po_sbr_rt_provider.py)

## What We Should Say Publicly

The safest accurate product statement is:

```text
This repository is a hybrid FMCW radar simulation workbench.
It is stronger than plain RadarSimPy in backend abstraction, antenna handling,
compensation layers, validation, and operator workflow.
It is not yet an Ansys AVx-class real-time production radar platform.
```

## Comparative Summary Table

| Dimension | Plain RadarSimPy | This Project | Ansys AVx / Perceive EM |
| --- | --- | --- | --- |
| FMCW and DSP simulation | strong | strong | strong |
| Backend interchangeability | limited | strong | strong |
| FFD and Jones handling | limited | present | product-level |
| Compensation layer | limited | present | product-level |
| Ray/path backend options | limited | present | present |
| PO/SBR-style backend | limited | present | strong |
| Stable validation and evidence workflow | limited | strong | product workflow |
| Real-time GPU production path | limited | not yet productized | strong |
| Full-wave EM | no | no | usually no for this product line |

## Practical Release Judgment

For the current release cut, the correct engineering judgment is:

1. this project is already more capable than plain `RadarSimPy` for hybrid workflow and operator-facing validation
2. this project is not yet comparable to `Ansys AVx` as a production-scale, real-time, GPU sensor platform
3. the current physics level should be described as:
   - low fidelity for `RadarSimPy + FFD`
   - medium fidelity for `Sionna-style RT`
   - medium to higher fidelity for `PO-SBR`
   - hybrid overall, not full-wave

## Related Documents

- [Graph Lab Low/High Fidelity Execution Flow](338_graph_lab_low_high_fidelity_execution_flow.md)
- [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md)
- [Release-Candidate Snapshot](291_release_candidate_snapshot_2026_03_08.md)
- [Generated Reports Index](reports/README.md)

