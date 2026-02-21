# Execution Plan

## Goal

Build an AVX-like offline radar simulator for FMCW + TDM-MIMO that can emit:

- propagation path list
- raw ADC cube

## Milestones

- [x] M0: Paper-to-code traceability matrix
- [x] M1: Documentation baseline and contracts
- [x] M2: Minimal path-to-ADC synthesis core
- [x] M3: Deterministic validation script (3 scenarios)
- [x] M3.5: Reference adapter scaffolding + smoke validation
- [x] M4: P-code replacement wave-1 (`generate_channel`, `Doppler`, `concatenated Dop`, `Angle`)
- [x] M5: RT adapter base (HybridDynamicRT frame ingestion, first version)
- [x] M5.5: Hybrid ingest pipeline and canonical output writer
- [x] M6: P-code replacement wave-2 (`path power` models and calibration)
- [x] M7: `.ffd` parser + interpolation
- [x] M7.5: Jones polarization flow through path/antenna/synth
- [x] M7.6: RD/RA parity metrics comparator baseline
- [x] M7.7: Global Jones calibration bootstrap (LS fitter + ingest hook)
- [x] M7.8: Calibration sample builder (`path_list + adc + ffd -> calibration_samples.npz`)
- [x] M7.9: Measured CSV converter (`measurement.csv -> calibration_samples.npz`)
- [x] M7.10: Scenario profile lock (`global_jones + parity thresholds + evaluator`)
- [x] M8: Motion compensation baseline for TDM virtual array
- [x] M8.1: Motion compensation tuning workflow and profile-default lock
- [x] M8.2: Moving-target replay batch automation and reporting
- [x] M8.25: Replay-based scenario profile lock finalization tooling
- [x] M8.26: Measured replay execution orchestration (multi-pack batch)
- [x] M8.27: Measured replay plan auto-builder (pack discovery)
- [x] M8.28: Per-pack replay manifest auto-builder
- [x] M8.29: Mock measured packs generator for no-data bootstrap
- [x] M8.3: Measured moving-target replay execution and profile lock finalization
- [x] M9.0: Public dataset conversion scaffolding (`MAT->ADC NPZ->pack`)
- [x] M9.05: One-command onboarding pipeline (`input->pack->plan->replay`)
- [x] M9.1: First public dataset schema lock and real subset conversion run
- [x] M10.0: Path-power tuning tooling + parity drift quantification baseline
- [x] M10.05: Path-power fit ingest integration (`--path-power-fit-json`) + CLI validation
- [x] M10.08: Path-power fit cycle orchestration (`baseline->samples->fit->tuned`) + summary automation
- [x] M10.09: Cross-family parity shift evaluator (`baseline/tuned x familyA/familyB`) + Xiangyu report
- [x] M10.10: Path-power fit batch runner (`multi CSV x multi model`) + demo summary
- [x] M10.11: Xiangyu label+ADC -> path_power_samples converter + real 128-frame CSV runs
- [x] M10.12: Xiangyu label-fit experiment matrix runner (`frame-count sweep`) + 128/512 report
- [x] M10.13: Path-power fit selection/lock from experiment summary (`largest_frame_then_rmse`)
- [x] M10.14: Hybrid cross-family fit comparator (`caseA ref`, `caseB baseline/tuned`) + first demo run
- [x] M10.15: Cross-family fit ranking objective (`comparator-based score`) + Xiangyu reflection/scattering ranking reports
- [x] M10.16: Cross-family ranking-based fit lock selection + Xiangyu RMSE-vs-cross-family selection delta report
- [x] M10.17: RMSE-lock vs cross-family-lock A/B comparator replay report (reflection/scattering)
- [x] M10.18: Mixed lock publish from A/B reports (`reflection keep`, `scattering cross-family`) + targeted comparator verification
- [x] M10.19: Measured replay fit-change impact gate (dependency audit) + Xiangyu no-op skip decision
- [x] M10.20: Fit-aware measured pack rebuild path + real-plan replay impact confirmation (`bms1000_run1`)
- [x] M10.21: Fit-aware measured replay batch scaling to target plans + no-gain stop gate execution
- [x] M10.22: Fit-aware replay saturation sanity gate and target-batch risk classification
- [x] M10.23: Current-code baseline rerun gate for fit-aware batch + stale-baseline correction report
- [x] M10.24: Fit-aware replay adoption policy gate (non-degradation + min-improvement) + Xiangyu decision
- [x] M10.25: Fit-lock policy selection with baseline fallback (candidate search on batch summary)
- [x] M10.26: Fit-lock candidate search orchestrator with headroom short-circuit (efficiency gate)
- [x] M10.27: Saturated-baseline drift objective and exploratory fit ranking path
- [x] M10.28: Constrained refit loop (preset grids) + drift-objective search ranking
- [x] M10.29: Multi-case constrained-refit consistency gate + Xiangyu target decision
- [x] M10.30: Targeted flat-refine constrained search + full-candidate evidence pass
- [x] M10.31: Case-partitioned fit-lock strategy evaluation (global -> family fallback)
- [x] M11.0: Object-scene pipeline V0 (`scene_json -> path_list + adc + radar_map`)
- [x] M11.1: Case-level family lock manifest materialization + replay verification
- [x] M11.2: Native scene path generator interface + non-frame backend stub
- [x] M11.3: Propagation output schema expansion (`path_id`, `material_tag`, reflection order)
- [x] M11.4: Multi-backend parity harness on shared scenes
- [x] M12.0: First mesh/material-aware scene backend adapter candidate (`mesh_material_stub`)
- [x] M12.1: Mesh scene import adapter contract (object/material manifest from external scene assets)
- [x] M12.2: Scene asset parser candidate for glTF/OBJ sidecar extraction to bridge manifest
- [x] M12.3: Sidecar schema profile/version lock and parser strict-mode policy
- [x] M12.4: Sidecar strict/non-strict compatibility matrix and bridge E2E regression lock
- [x] M12.5: Real-scene asset onboarding pilot (`public glTF/OBJ sample -> scene pipeline`) and lockable fixture path
- [x] M12.6: Public multi-object scene fixture pack and deterministic replay bundle lock
- [ ] M12.7: Public OBJ sample parity onboarding and mixed-format fixture matrix lock

## Iteration Rule (One-by-One Verification)

Each milestone is accepted only if:

1. Contract is documented (`docs/*.md`)
2. Reproducible validation command exists (`scripts/*.py`)
3. Pass/fail criteria are explicit
4. Result is logged in `docs/validation_log.md`

## Immediate Next Step

Start M12.7: add OBJ public-sample onboarding path and mixed-format fixture regression matrix.

## M10.19 Decision Gate

Accept M10.19 only if at least one holds:

1. mixed lock improves replay lock quality vs prior strict-tuned baseline
2. mixed lock keeps quality within tolerance while reducing cross-family drift score

Stop and re-plan M10.19 when:

- two attempts show no improvement/no new failure signal
- measured replay inputs are insufficient to evaluate lock quality

M10.19 outcome (2026-02-21):

- measured replay plans show no dependency on selected fit JSON assets
- rerun skipped as no-op per workflow Value-Gate/Repetition rules

M10.20 outcome (2026-02-21):

- fit-aware pack rebuild path implemented from existing packs
- representative real plan (`bms1000_run1`) replay became fit-sensitive (`pass_count 1 -> 12`)

M10.21 outcome (2026-02-21):

- fit-aware measured replay batch runner executed on target plans (`bms1000_512`, `bms1000_full897`, `cms1000_128`)
- all 3 cases improved over baseline (`improved_case_count=3`)
- stop gate condition (`max_no_gain_attempts=2`) remained armed; no case hit no-gain streak in this run
- superseded by M10.23 due stale historical baseline reports

M10.22 outcome (2026-02-21):

- saturation sanity gate added for fit-aware replay batch summaries
- Xiangyu target batch analysis flagged `2/3` saturated cases (`bms1000_512`, `bms1000_full897`)
- recommendation emitted: `proxy_strength_review_required`
- superseded by M10.23 rerun-baseline analysis

M10.23 outcome (2026-02-21):

- fit-aware batch runner updated with `baseline-mode=rerun|provided` (default `rerun`) to remove stale baseline dependency
- rerun-baseline Xiangyu target batch result: `improved_case_count=0` (`3/3` no-gain, stop gate triggered)
- rerun-baseline saturation gate result: `saturated_case_count=0`, recommendation `proxy_strength_within_expected_range`
- key conclusion corrected: current issue is not saturation uplift but fit-aware degradation vs current baseline

M10.24 outcome (2026-02-21):

- policy gate added to formalize adoption decision using rerun-baseline batch summary
- Xiangyu rerun-baseline policy result: `degrade_only_case_count=3`, `improved_case_count=0`
- recommendation fixed as `reject_fit_lock_due_to_degradation`

M10.25 outcome (2026-02-21):

- fit-lock selector added to rank/accept/reject fit candidates from batch summary
- Xiangyu rerun-baseline selection result: no eligible fit candidate
- deterministic fallback selected: `baseline_no_fit`

M10.26 outcome (2026-02-21):

- fit-lock search orchestrator added (`baseline -> feasibility -> batch/policy/selection`)
- Xiangyu rerun-baseline search with 6 fit candidates detected `headroom=0`
- search short-circuited before fit-aware batch rerun and emitted fallback `baseline_no_fit`

M10.27 outcome (2026-02-21):

- drift-objective fit selector implemented for saturated baseline use-cases
- Xiangyu 3-case rerun-baseline drift ranking selected `reflection` as least-distorting candidate
- recommendation explicitly marked exploratory because pass/fail degradation still exists
- search orchestrator supports `--objective-mode drift` for non-short-circuited exploratory analysis

M10.28 outcome (2026-02-21):

- constrained refit loop implemented (`run_path_power_fit_batch -> run_measured_replay_fit_lock_search[drift]`) with preset-wise ranking
- default `flat` preset grid corrected to valid positive range exponents (`range_power_exponent > 0`)
- synthetic end-to-end validation added (`validate_run_constrained_refit_drift_search.py`)
- Xiangyu `bms1000_512` 3-preset probe selected `flat` as best (`adopt_selected_fit_by_drift_objective`, score `0.0512`)

M10.29 outcome (2026-02-21):

- multi-case constrained search executed on Xiangyu targets (`bms1000_512`, `bms1000_full897`, `cms1000_128`)
- consistency gate added to convert preset-search results into deterministic adopt/fallback decision
- gate diagnostics showed all presets violate non-degradation constraints on the 3-case set
- final decision fixed as fallback `baseline_no_fit`

M10.30 outcome (2026-02-21):

- constrained search upgraded with drift/fit-proxy pass-through and `max-no-gain-attempts` control
- targeted flat-refine sweep executed (`flat_fine_a/b/c`) under strict non-degradation limits
- no-gain truncation inefficiency removed (all 4 fit candidates evaluated per preset)
- all presets still fell back to `baseline_no_fit`; strict multi-case adoption remained unavailable

M10.31 outcome (2026-02-21):

- case-partitioned lock search orchestrator implemented with optional global-summary reuse
- global Xiangyu target decision remained `baseline_no_fit` (reused from targeted flat refine)
- family fallback recovered adoptable lock for `bms1000` (`bms1000_reflection.json`)
- `cms1000` kept baseline fallback, yielding final strategy `mixed_family_partitioned_lock`

M11.0 outcome (2026-02-21):

- object-scene pipeline V0 added (`scene_json -> path_list + adc + radar_map`)
- new CLI added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_object_scene_to_radar_map.py`
- new contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/87_object_scene_radar_map_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_to_radar_map.py`

M11.1 outcome (2026-02-21):

- case-partition summary to case-level manifest materializer added
- replay verification path integrated in one command
- new CLI added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_case_partitioned_lock_manifest_replay.py`
- new contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/89_case_partitioned_lock_manifest_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_case_partitioned_lock_manifest_replay.py`

M11.2 outcome (2026-02-21):

- `scene_pipeline` backend routing expanded to `hybrid_frames` + `analytic_targets`
- native non-frame path generator stub added (`analytic_targets`)
- new validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_analytic_backend.py`
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/90_native_scene_path_generator_contract.md`

M11.3 outcome (2026-02-21):

- canonical path schema expanded with `path_id`, `material_tag`, `reflection_order`
- propagation metadata serialization wired in `path_list.json`
- hybrid and analytic backends both emit path metadata
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/91_propagation_schema_expansion_contract.md`

M11.4 outcome (2026-02-21):

- multi-backend parity harness CLI added (`reference scene` vs `candidate scene`)
- parity summary includes backend IDs, map paths, metrics/failures
- validation added for `hybrid_frames` vs `analytic_targets` synthetic scene pair
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/92_multi_backend_parity_harness_contract.md`

M12.0 outcome (2026-02-21):

- `mesh_material_stub` backend added to `scene_pipeline`
- object/material scene inputs now map to canonical path/ADC/radar-map outputs
- acceptance contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/93_mesh_material_backend_candidate_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_mesh_material_backend.py`

M12.1 outcome (2026-02-21):

- external asset-manifest to scene-json bridge module added
- bridge CLI added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_mesh_scene_from_asset_manifest.py`
- bridge contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/94_mesh_scene_import_bridge_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py`

M12.2 outcome (2026-02-21):

- sidecar parser module added for `glTF/OBJ -> asset_manifest`
- parser CLI added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_asset_manifest_from_sidecar.py`
- parser contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/95_sidecar_asset_parser_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py`

M12.3 outcome (2026-02-21):

- sidecar schema lock defaults defined (`schema_profile=v1`, `schema_version=1`)
- strict-mode parse gate added for unknown keys and profile/version mismatch
- strict/locked parser metadata emitted in manifest (`strict_mode`, `schema_profile`, `schema_version`)
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/96_sidecar_schema_lock_contract.md`
- validations rerun: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py`

M12.4 outcome (2026-02-21):

- strict/non-strict compatibility matrix validator added
- non-strict parser diagnostics expanded (`unknown_top_level_keys`, `unknown_object_keys`)
- non-strict manifest bridge E2E path verified (`asset_manifest -> scene_json -> canonical artifacts`)
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/97_sidecar_compatibility_matrix_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_schema_compat_matrix.py`

M12.5 outcome (2026-02-21):

- public scene-asset onboarding runner added (`asset download/source -> sidecar -> manifest -> scene -> outputs`)
- offline validator added for local-source fixture (no network dependency)
- real public sample onboarding executed with Khronos `Box.glb` and summary locked
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/98_public_scene_asset_onboarding_contract.md`
- summary evidence: `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_khronos_box_v1_2026_02_21.json`

M12.6 outcome (2026-02-21):

- onboarding runner extended with object layout presets (`single`, `triple_lane`)
- deterministic replay-bundle manifest added (`artifact hashes + tx schedule + frame count`)
- multi-object deterministic validator added (repeat-run hash consistency check)
- real public `Box.glb` triple-lane run executed and summary locked
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/99_public_multi_object_fixture_bundle_contract.md`
- summary evidence: `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_khronos_box_triple_lane_v1_2026_02_21.json`
