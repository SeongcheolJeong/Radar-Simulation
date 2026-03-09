# Graph Lab Low/High Fidelity Execution Flow

## Purpose

Use this page when you want to understand what actually happens after you click:

- `Low Fidelity: RadarSimPy + FFD`
- `High Fidelity: Sionna-style RT`
- `High Fidelity: PO-SBR`

This is not a button map. It is the execution-flow view from frontend preset selection to backend artifacts.

## Scope

This guide explains:

1. where the low/high presets start in the UI
2. which backend entrypoint each preset uses
3. where low and high paths diverge
4. where they join again into the common synth/output pipeline
5. what files and UI signs you should expect at each stage

## Quick Difference

```text
Low fidelity
= RadarSimPy-centered provider path
+ optional RadarSimPy ADC
+ repo synth when FFD/Jones/compensation requires path-based synthesis

High fidelity
= ray/path provider first
+ repo synth always builds ADC from returned paths
```

The preset definitions live in:

- [runtime_purpose_presets.mjs](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs)

The backend execution entrypoints live in:

- [scene_pipeline.py](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py)

## Shared Frontend Start

All three runtime tracks begin the same way in Graph Lab:

1. Open Graph Lab.
2. Click `Load #1`.
3. Choose a runtime preset in the left runtime panel.
4. Click `Run Graph (API)`.
5. The API writes a graph-run record and starts the backend selected by the preset.

What changes between tracks is:

- `runtimeBackendType`
- `runtimeProviderSpec`
- `runtimeRequiredModules`
- `runtimeSimulationMode`
- optional advanced runtime input fields

Preset values are defined here:

- [runtime_purpose_presets.mjs:89](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L89)

## Low Fidelity Sequence

### Preset Configuration

When you click `Low Fidelity: RadarSimPy + FFD`, Graph Lab applies:

- backend: `radarsimpy_rt`
- provider: `avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths`
- required modules: `radarsimpy`
- simulation mode: `radarsimpy_adc`
- device hint: `cpu`

Source:

- [runtime_purpose_presets.mjs:92](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L92)

### Backend Entry

The backend enters:

- [scene_pipeline.py:656](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L656)

This step resolves:

- `tx_pos_m`
- `rx_pos_m`
- `n_chirps`
- `tx_schedule`
- `RadarConfig`

Source:

- [scene_pipeline.py:661](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L661)

### Provider Stage

The runtime provider call happens here:

- [scene_pipeline.py:686](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L686)

The provider itself is:

- [radarsimpy_rt_provider.py:14](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L14)

Inside that provider:

1. runtime input and optional license override are read
2. analytic targets are converted into canonical `paths_by_chirp`
3. `simulation_mode` is checked
4. if possible, RadarSimPy `sim_radar` is called to produce ADC
5. the provider returns:
   - always: `paths_by_chirp`
   - optionally: `adc_sctr`

Important branches:

- `analytic_paths`
  - path list only
- `radarsimpy_adc`
  - path list plus RadarSimPy ADC when runtime is available
- `auto`
  - try ADC, otherwise stay analytic if fallback is allowed

Sources:

- [radarsimpy_rt_provider.py:41](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L41)
- [radarsimpy_rt_provider.py:51](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L51)
- [radarsimpy_rt_provider.py:72](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L72)

### Multiplexing Stage

Low fidelity is also where RadarSimPy runtime multiplexing is applied.

The provider builds the TX plan for:

- `tdm`
- `bpm`
- `custom`

Sources:

- [radarsimpy_rt_provider.py:170](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L170)
- [radarsimpy_rt_provider.py:176](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L176)
- [radarsimpy_rt_provider.py:249](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L249)

### ADC Decision Stage

Back in the scene pipeline, low fidelity chooses between:

- runtime ADC from RadarSimPy
- common repo synth

The decision happens here:

- [scene_pipeline.py:708](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L708)
- [scene_pipeline.py:723](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L723)

Runtime ADC is used only when all of these are true:

- provider returned `adc_sctr`
- radar compensation is not enabled
- antenna path synthesis is not required

If any of these are true, the pipeline ignores runtime ADC and synthesizes from paths:

- FFD is enabled
- Jones/global Jones is enabled
- compensation is enabled

### FFD/Jones Stage

FFD and Jones handling is common synth logic, not a separate backend.

This logic lives here:

- [scene_pipeline.py:799](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L799)

It resolves:

- `tx_ffd_files`
- `rx_ffd_files`
- antenna mode
- whether path-based synth is required

### Common Synthesis Stage

If repo synthesis is needed, the path list goes into:

- [scene_pipeline.py:843](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L843)

This calls `synth_fmcw_tdm` and produces ADC in the repo contract shape.

### Low Fidelity Outputs

The low-fidelity run always writes:

- `path_list.json`
- `adc_cube.npz`

The save stage is here:

- [scene_pipeline.py:758](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L758)

Downstream pipeline stages then derive:

- `radar_map.npz`
- `graph_run_summary.json`
- optional `lgit_customized_output.npz`

### What You Should Recognize In The UI

If low fidelity is working, you should usually recognize:

- status line shows `backend radarsimpy_rt`
- runtime diagnostics mention RadarSimPy provider/module state
- `Graph Run Result` ends with `status: completed`
- artifact area contains `path_list.json`, `adc_cube.npz`, `radar_map.npz`

## High Fidelity Sequence

### Common High-Fidelity Shape

Both high-fidelity presets work like this:

```text
frontend preset
-> runtime provider generates canonical paths
-> optional compensation
-> common repo synth builds ADC
-> common output contract writes artifacts
```

The key difference from low fidelity is:

- high-fidelity providers do not try to give the final ADC to the pipeline
- they provide the path list first
- the common synth always builds ADC from those paths

## High Fidelity: Sionna-style RT

### Preset Configuration

When you click `High Fidelity: Sionna-style RT`, Graph Lab applies:

- backend: `sionna_rt`
- provider: `avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba`
- required modules: `mitsuba,drjit`
- simulation mode: `auto`
- device hint: `gpu`
- advanced fields:
  - `ego_origin_m`
  - `chirp_interval_s`
  - `min_range_m`
  - `spheres`

Source:

- [runtime_purpose_presets.mjs:102](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L102)

### Backend Entry

The backend enters:

- [scene_pipeline.py:495](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L495)

This resolves the same radar geometry basics as low fidelity:

- `tx_pos_m`
- `rx_pos_m`
- `n_chirps`
- `tx_schedule`
- `RadarConfig`

### Provider Stage

The runtime provider call happens here:

- [scene_pipeline.py:523](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L523)

The provider itself is:

- [mitsuba_rt_provider.py:10](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L10)

Inside that provider:

1. validate `ego_origin_m`
2. validate non-empty `spheres`
3. import Mitsuba and choose a variant
4. build a Mitsuba scene from spheres
5. for each chirp:
   - update sphere position by velocity
   - cast a ray from ego origin
   - intersect scene
   - derive range, delay, Doppler, amplitude
   - emit canonical path records

Sources:

- [mitsuba_rt_provider.py:15](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L15)
- [mitsuba_rt_provider.py:28](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L28)
- [mitsuba_rt_provider.py:33](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L33)
- [mitsuba_rt_provider.py:45](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L45)

### Synthesis And Output

After the provider returns `paths_by_chirp`, the scene pipeline:

1. adapts payload into canonical paths
2. applies optional compensation
3. calls common synth
4. writes `path_list.json`
5. writes `adc_cube.npz`

Sources:

- [scene_pipeline.py:534](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L534)
- [scene_pipeline.py:539](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L539)
- [scene_pipeline.py:546](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L546)
- [scene_pipeline.py:556](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L556)

### Operational Meaning

This is the current interactive high-fidelity path.

Current timing evidence:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

At the current evidence snapshot, this path completes within the interactive budget.

## High Fidelity: PO-SBR

### Preset Configuration

When you click `High Fidelity: PO-SBR`, Graph Lab applies:

- backend: `po_sbr_rt`
- provider: `avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr`
- required modules: `rtxpy,igl`
- simulation mode: `auto`
- device hint: `gpu`
- advanced fields:
  - `po_sbr_repo_root`
  - `geometry_path`
  - `chirp_interval_s`
  - `bounces`
  - `rays_per_lambda`
  - angle fields
  - `components`

Source:

- [runtime_purpose_presets.mjs:116](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L116)

### Backend Entry

The backend enters:

- [scene_pipeline.py:575](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L575)

### Provider Stage

The runtime provider call happens here:

- [scene_pipeline.py:603](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L603)

The provider itself is:

- [po_sbr_rt_provider.py:13](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L13)

Inside that provider:

1. validate chirp count and carrier frequency
2. resolve repo root and geometry path
3. validate `rays_per_lambda`, `bounces`, and component fields
4. check runtime prerequisites:
   - `igl`
   - `rtxpy`
5. load `POsolver.py`
6. build geometry
7. for each chirp and component:
   - call `po.simulate(...)`
   - derive amplitude, delay, Doppler, direction
   - emit canonical path records

Sources:

- [po_sbr_rt_provider.py:24](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L24)
- [po_sbr_rt_provider.py:70](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L70)
- [po_sbr_rt_provider.py:72](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L72)
- [po_sbr_rt_provider.py:75](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L75)
- [po_sbr_rt_provider.py:84](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L84)

### Synthesis And Output

After the provider returns canonical paths, the scene pipeline:

1. adapts payload into canonical paths
2. applies optional compensation
3. calls the common synth
4. writes `path_list.json`
5. writes `adc_cube.npz`

Sources:

- [scene_pipeline.py:614](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L614)
- [scene_pipeline.py:619](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L619)
- [scene_pipeline.py:627](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L627)
- [scene_pipeline.py:637](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L637)

### Operational Meaning

This is the dedicated validation high-fidelity path, not the default interactive path.

Current timing evidence:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

At the current evidence snapshot, this path is not interactive-ready and should be treated as a longer-running or dedicated-env validation path.

## Where Low And High Join Again

The three tracks join again in the common synth/output contract:

1. canonical `paths_by_chirp`
2. optional compensation
3. optional FFD/Jones antenna handling
4. common ADC synthesis
5. common output artifacts

Join points:

- [scene_pipeline.py:799](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L799)
- [scene_pipeline.py:843](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L843)

This is why:

- low fidelity can still use FFD
- high fidelity can still use FFD
- low-vs-high comparison can use the same artifact contract

## Output Recognition Checklist

### If the run reached the provider stage

You should recognize:

- runtime diagnostics show a concrete backend/provider pair
- `Graph Run Result` has a real `graph_run_id`

### If the run reached the synthesis stage

You should recognize:

- `adc_cube.npz` exists
- `path_list.json` exists

### If the full contract completed

You should recognize:

- `radar_map.npz` exists
- `graph_run_summary.json` exists
- compare/export actions become meaningful

## Which Path To Use

Use this rule unless the release scope changes:

- `Low Fidelity: RadarSimPy + FFD`
  - fast baseline
  - compare reference
- `High Fidelity: Sionna-style RT`
  - interactive high-fidelity path
- `High Fidelity: PO-SBR`
  - dedicated validation or closure path

For current runtime verdict, always check:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)
