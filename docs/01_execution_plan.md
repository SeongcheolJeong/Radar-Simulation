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
- [x] M12.7: Public OBJ sample parity onboarding and mixed-format fixture matrix lock
- [x] M13.0: Mesh-geometry proxy extraction baseline (`centroid/area`) from OBJ/glTF metadata for auto-populated scene objects
- [x] M13.1: Sionna RT backend adapter (`scene -> paths_by_chirp`) and canonical parity lock
- [x] M13.2: PO-SBR backend adapter candidate for high-fidelity scattering path modeling
- [x] M13.3: RadarSimPy periodic parity-lock automation (signal-chain drift guard, optional runtime dependency)
- [x] M14.0: Direct Sionna/PO-SBR runtime coupling feasibility spike (no pre-exported path JSON)
- [x] M14.1: Runtime environment contract + readiness probe (`sionna`/`po-sbr`)
- [x] M14.2: Real runtime engine binding pilot (Mitsuba-backed `sionna_rt` first scene run)
- [x] M14.3: Runtime blocker gate + `sionna` PHY runtime sanity enablement
- [x] M14.4: `sionna.rt` LLVM candidate probe + blocker evidence lock
- [x] M14.5: `sionna.rt` full runtime enablement (working LLVM backend on target host)
- [x] M14.6: `po-sbr` runtime pilot on Linux+NVIDIA environment
- [x] M15.0: Web E2E orchestration API phase-0 skeleton (`/health`, `/api/runs`, run summary quicklook)
- [x] M15.1: Web run summary schema v2 (frontend-compatible `outputs/path_summary/adc_summary/radar_map_summary`)
- [x] M15.2: Dashboard API-run mode (`POST /api/runs` + polling + summary auto-load) and dual-server local launcher
- [x] M15.3a: Compare API v1 (`POST /api/compare`, `/api/comparisons`) + dashboard compare panel
- [x] M15.3b: Baseline pinning and regression policy verdict payload (`/api/baselines`, `/api/compare/policy`)
- [x] M15.4: Regression session API (`/api/regression-sessions`, baseline + candidate set + batched policy verdicts`)
- [x] M15.5: Regression artifacts export API (`/api/regression-exports`, session CSV/JSON package + summary index)
- [x] M15.6: Regression history dashboard wiring (session/export browse + download actions)
- [x] M15.7: Regression gate overview panel (latest verdict KPIs + quick adopt/hold cues)
- [x] M15.8: Regression policy tuning controls (dashboard thresholds/policy presets)
- [x] M15.9: Regression decision audit panel (per-rule failure histogram + recent trend)
- [x] M15.10: Regression review bundle export hook (dashboard one-click package copy path)
- [x] M15.11: Regression decision report template export (markdown handoff skeleton)
- [x] M15.12: Regression report auto-include policy-eval excerpts (top failure evidence block)
- [x] M15.13: Regression evidence drill-down panel (session row/policy-eval quick pivot for reviewer loop)
- [x] M16.0: Simulink-style Graph contract freeze (ReactFlow node/edge schema + validator contract)
- [x] M16.1: ReactFlow shell bootstrap (graph canvas + property inspector + template loader)
- [x] M16.2: Graph executor API bridge (`/api/graph/*` validation/run/status)
- [x] M16.3: Artifact inspector panels (Path/ADC/RD/RA + node-output trace)
- [x] M16.4: Regression gate integration on graph runs (policy/gate/evidence/report one-click)
- [x] M16.5: Performance/reliability hardening (partial rerun cache/cancel/failure recovery)
- [x] M17.0: Graph Lab async run monitor (sync/async mode + polling progress + manual poll controls)
- [x] M17.1: Graph Lab frontend modularization (inline script -> ES modules, helper/runtime split)
- [x] M17.2: Graph Lab component/API split (`app` orchestration + panel components + api client)
- [x] M17.3: Graph Lab action hooks split (`useGraphRunOps`, `useGateOps`)
- [x] M17.4: Graph input panel model grouping (reduce action/state fan-out)
- [x] M17.5: Frontend typed contract + runtime guard (`contracts.mjs` for panel/hook bindings)
- [x] M17.6: Contract diagnostics surface (warning counters + debug panel actions)
- [x] M17.7: Auto contract diagnostics propagation (run/gate text + inspector auto-sync)
- [x] M17.8: Contract overlay timeline (opt-in overlay + run/gate delta event wiring)
- [x] M17.9: Contract timeline filter/export + gate report diagnostics slice
- [x] M17.10: Contract compact timeline + run pin + gate tail refs
- [x] M17.11: Timeline row -> graph run jump action
- [x] M17.12: Policy failure correlation tags on timeline rows
- [x] M17.13: Timeline -> gate evidence deep-link + failure-rule badges
- [x] M17.14: Historical policy-eval fetch fallback (`policy_eval_id -> run_id/summary`) for persisted gate evidence
- [x] M17.15: Policy-eval filtered pagination + frontend evidence cache (large-history scan control)
- [x] M17.16: Overlay gate-history window controls + incremental page-budget lookup UX
- [x] M17.17: Timeline row-window virtualization + overlay preference persistence
- [x] M17.18: Overlay shortcut keys + preset/reset operations
- [x] M17.19: Row detail lazy-expansion controls + detail rendering on demand
- [x] M17.20: Overlay shortcut remap + profile persistence
- [x] M17.21: Row detail field-level toggles + core/all presets
- [x] M17.22: Shortcut profile transfer import/export (team-shareable JSON)
- [x] M17.23: Detail-view copy ergonomics (row/visible copy actions)
- [x] M17.24: Severity-first triage filter (all/high/med/low with scoped counts)
- [x] M17.25: Policy-first triage filter (all/hold/adopt/none with scoped counts)
- [x] M17.26: Active filter summary chips + filter-only reset action
- [x] M17.27: Filter preset profiles (load/save/delete with persistence)
- [x] M17.28: Filter preset transfer import/export (team-shareable JSON bundle)
- [x] M17.29: Filter preset import guardrails (merge/replace mode + conflict preview)
- [x] M17.30: Selective filter preset import + dry-run conflict visibility
- [x] M17.31: Replace-mode confirmation + one-click undo recovery
- [x] M17.32: Import audit trail + multi-level undo/redo stacks
- [x] M17.33: Audit detail drilldown + local persistence for import history
- [x] M17.34: Import history maintenance controls + audit search/filter
- [x] M17.35: Audit query reset ergonomics + row-volume guardrails
- [x] M17.36: Audit row pagination cap + query preset shortcuts
- [x] M17.37: Audit deep-link copy bundle + preset pinning ergonomics
- [x] M17.38: Audit bundle import/restore + pinned preset quick toggle shortcut
- [x] M17.39: Audit bundle schema guardrails + operator hints
- [x] M17.40: Audit bundle partial-restore toggles + pin state chips
- [x] M17.41: Audit restore preset shortcuts + pin-chip filter controls
- [x] M17.42: Audit scoped quick-apply actions + restore/pin operator hints
- [x] M17.43: Quick-apply/restore coupling + operator-safe reset affordances
- [x] M17.44: Quick-apply telemetry/export hooks + guided reset safety hints
- [x] M17.45: Quick telemetry trend chips + safe reset copy/countdown refinements
- [x] M17.46: Quick telemetry drilldown controls (failure-only + reason focus)
- [x] M17.47: Quick telemetry drilldown presets + filtered export/copy handoff bundle
- [x] M17.48: Quick telemetry custom profile save/load + team-share transfer
- [x] M17.49: Quick telemetry profile import diff/merge guardrails + rollback hint
- [x] M17.50: Quick telemetry profile selective import toggles (subset pick + conflict-only view)
- [x] M17.51: Quick telemetry profile import pagination ergonomics (row-cap/window nav + selection safety hints)
- [x] M17.52: Quick telemetry profile import query/filter aids (name search + conflict-class chips)
- [x] M17.53: Quick telemetry profile import filter presets + one-click reset bundles
- [x] M17.54: Quick telemetry import filter-bundle transfer (copy/export/import + preview)
- [x] M17.55: Quick telemetry import filter-bundle schema guardrails (kind/schema checks + operator hints)
- [x] M17.56: Quick telemetry import filter-bundle strict/compat mode toggle (legacy bare-object accept vs strict wrapped payload)
- [x] M17.57: Quick telemetry strict-mode rollout helper (legacy payload auto-wrap preview + migration hints)
- [x] M17.58: Quick telemetry strict-mode adoption readiness gate (legacy-wrap usage signal + default-switch checklist)
- [x] M17.59: Quick telemetry strict-default cutover helper (default-on preset + compat fallback reminder)
- [x] M17.60: Quick telemetry strict-cutover timeline ledger (apply/fallback event rows + export-ready status trail)
- [x] M17.61: Quick telemetry strict-cutover rollback drill helper (failure-tagged fallback presets + operator checklist)
- [x] M17.62: Quick telemetry strict-cutover rollback drill package (preset snapshot + checklist report export)
- [x] M17.63: Quick telemetry strict-cutover rollback package replay helper (package import preview + checklist delta guard)
- [x] M17.64: Quick telemetry strict-cutover rollback package provenance guard (source stamp + checksum hint)
- [x] M17.65: Quick telemetry strict-cutover rollback package trust policy (provenance strict-mode reject + operator override log)
- [x] M17.66: Quick telemetry strict-cutover rollback trust audit bundle (override log + provenance snapshot export package)
- [x] M17.67: Quick telemetry strict-cutover rollback trust audit bundle handoff parser (schema guard + import preview)
- [x] M17.68: Quick telemetry strict-cutover rollback trust audit bundle apply helper (policy/log hydrate from handoff)
- [x] M17.69: Quick telemetry strict-cutover rollback trust audit bundle apply safety gate (replace-confirm + operator hint)
- [x] M17.70: Quick telemetry strict-cutover rollback trust audit bundle apply safety auto-disarm (confirm reset timer + countdown hint)
- [x] M17.71: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run diff summary (incoming vs live policy/log snapshot)
- [x] M17.72: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package (summary export + copy)
- [x] M17.73: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package parser (schema guard + import preview)
- [x] M17.74: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply helper (imported snapshot hydrate + status)
- [x] M17.75: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety gate (hydrate-overwrite confirm + operator hint)
- [x] M17.76: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety auto-disarm (confirm timer + countdown hint)
- [x] M17.77: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity trail (confirm arm/disarm timeline + hint)
- [x] M17.78: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity controls (trail reset + export/copy)
- [x] M17.79: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity replay (schema guard + import preview)
- [x] M17.80: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity replay gate (replacement confirm + operator hint)
- [x] M17.81: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity replay auto-disarm (confirm timer + countdown hint)
- [ ] M17.82: Quick telemetry strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity replay timeline trail (arm/disarm/auto-disarm event log + hint)

## Iteration Rule (One-by-One Verification)

Each milestone is accepted only if:

1. Contract is documented (`docs/*.md`)
2. Reproducible validation command exists (`scripts/*.py`)
3. Pass/fail criteria are explicit
4. Result is logged in `docs/validation_log.md`

## Immediate Next Step

Advance post-M17.81 frontend hardening track: add strict-cutover rollback trust audit bundle apply dry-run handoff package apply safety activity replay timeline trail (arm/disarm/auto-disarm event log + hint) while keeping M16.5+M17.0 semantics (cache/cancel/retry/async polling) stable.

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

M12.7 outcome (2026-02-21):

- mixed-format fixture matrix validator added (`glTF + OBJ`)
- public OBJ onboarding run added and summary locked (`WaltHead.obj`)
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/100_public_obj_mixed_format_matrix_contract.md`
- summary evidence: `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_walthead_obj_v1_2026_02_21.json`

M13.0 outcome (2026-02-21):

- mesh-geometry proxy extractor baseline added (`OBJ` + `glTF/GLB`)
- sidecar parser now auto-fills missing `centroid_m` and `mesh_area_m2`
- parser metadata expanded with auto-geometry diagnostics
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/101_mesh_geometry_proxy_extractor_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_geometry_proxy_extractor.py`

M13.1 outcome (2026-02-21):

- `sionna_rt` backend added (`scene -> exported Sionna-style paths -> canonical outputs`)
- Sionna path adapter added (supports `paths_by_chirp` and flat `paths` with chirp index)
- parity lock added for `analytic_targets` vs `sionna_rt` matched scene pair
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/102_sionna_rt_backend_contract.md`
- validations added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_sionna_backend.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_sionna_rt.py`

M13.2 outcome (2026-02-21):

- `po_sbr_rt` backend adapter candidate added (`scene -> PO-SBR-style exported paths -> canonical outputs`)
- PO-SBR path adapter added (delay/range, doppler/velocity, direction, amplitude proxy forms)
- parity lock added for `analytic_targets` vs `po_sbr_rt` matched synthetic scene pair
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/103_po_sbr_backend_contract.md`
- validations added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_po_sbr_backend.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_po_sbr_rt.py`

M13.3 outcome (2026-02-21):

- RadarSimPy periodic parity-lock core added (manifest-driven case checks + threshold gate)
- periodic lock runner CLI added
- gate summary now records RadarSimPy runtime availability diagnostics
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/104_radarsimpy_periodic_lock_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_radarsimpy_periodic_parity_lock.py`

M14.0 outcome (2026-02-21):

- runtime-coupling utility added (`runtime_provider` dynamic import + required-module probe)
- `sionna_rt` / `po_sbr_rt` backends now support runtime provider execution without pre-exported path JSON
- deterministic runtime failure policy added (`error` vs `use_static`) with metadata trace (`runtime_resolution`)
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/105_scene_runtime_coupling_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_runtime_coupling.py`

M14.1 outcome (2026-02-21):

- runtime environment probe runner added (`required modules + external repo presence -> ready gate`)
- runtime readiness summary schema locked for `sionna_rt_mitsuba_runtime`, `sionna_runtime`, `sionna_rt_full_runtime`, `po_sbr_runtime`
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/106_scene_runtime_env_probe_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py`

M14.2 outcome (2026-02-22):

- Mitsuba-backed runtime provider added for `sionna_rt` backend
- first real runtime scene pilot executed without pre-exported path JSON
- real pilot report locked: `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_mitsuba_pilot_v1_2026_02_22.json`
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/107_scene_runtime_mitsuba_pilot_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_mitsuba_pilot.py`

M14.3 outcome (2026-02-22):

- runtime probe expanded with deterministic blocker reasoning (`status`, `blockers`, platform/NVIDIA diagnostics)
- blocker report generator added to convert probe summary into actionable next steps
- `sionna` + `tensorflow` installed in `.venv-sionna311`; `sionna` PHY minimal sanity check passes
- real blocker report locked: `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_blocker_report_m14_3_2026_02_22.json`
- contracts added:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/108_scene_runtime_blocker_report_contract.md`
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/109_sionna_phy_runtime_sanity_contract.md`
- validations added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_blocker_report.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sionna_phy_runtime_minimal.py`

M14.4 outcome (2026-02-22):

- `sionna.rt` LLVM probe runner added to test baseline + candidate `DRJIT_LIBLLVM_PATH` imports
- candidate set includes environment override, llvmlite library, and discovered macOS SDK paths (non-macOS SDK scan optional)
- real probe report archived:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/sionna_rt_llvm_probe_m14_4_2026_02_22.json`
- current host result locked as blocked (`success=false`):
  - llvmlite candidate rejected due LLVM API mismatch
  - Xcode SDK candidates rejected due non-macOS target binaries
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/110_sionna_rt_llvm_probe_contract.md`
- validation added: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_sionna_rt_llvm_probe.py`

M14.5 outcome (2026-02-22):

- compatible macOS `libLLVM.dylib` candidate validated from local runtime cache (`homebrew llvm@17` extracted dylib + ad-hoc codesign)
- direct import gate unlocked:
  - `DRJIT_LIBLLVM_PATH=<candidate> ... import sionna.rt` passes
- runtime probe now supports explicit override:
  - `--drjit-libllvm-path` added to `run_scene_runtime_env_probe.py`
  - probe output now records `applied_overrides`
- blocker priority updated to prefer `sionna_rt_full_runtime` when ready
- real reports archived:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/sionna_rt_llvm_probe_m14_5_2026_02_22.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_5_2026_02_22.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_blocker_report_m14_5_2026_02_22.json`
- contract added: `/Users/seongcheoljeong/Documents/Codex_test/docs/111_sionna_rt_full_runtime_enablement_contract.md`

M14.6 progress (2026-02-22):

- PO-SBR runtime provider added:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/runtime_providers/po_sbr_rt_provider.py`
  - provider maps `POsolver.build/simulate` output to canonical `paths_by_chirp`
- runtime pilot runner added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_po_sbr_pilot.py`
  - deterministic preflight blockers with `pilot_status` contract (`blocked|executed`)
  - `--allow-blocked` mode added to avoid repeated no-op attempts on unsupported hosts
- strict completion gate added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_executed_report.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_po_sbr_linux_strict.sh`
- Linux environment bootstrap added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/bootstrap_po_sbr_linux_env.sh`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_remote_linux_over_ssh.sh` (macOS remote orchestration)
- closure readiness gate added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_closure_readiness.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_m14_6_closure_readiness.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_m14_6_from_linux_report.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_finalize_m14_6_from_linux_report.py`
- validations added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_po_sbr_runtime_provider_stubbed.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_provider_integration_stubbed.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_po_sbr_pilot.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_validate_scene_runtime_po_sbr_executed_report.py`
- contracts/docs added:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/112_scene_runtime_po_sbr_pilot_contract.md`
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/113_po_sbr_linux_runtime_runbook.md`
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/114_m14_6_closure_readiness_contract.md`
- current host evidence (Darwin) locked as blocked:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_2026_02_22.json`
  - blockers: missing modules (`rtxpy`, `igl`), unsupported platform, missing NVIDIA runtime
- closure readiness report:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_2026_02_22.json`
  - current state: `ready=false`, missing only `linux_executed_report_missing`
- M14.6 closure status (2026-02-28):
  - strict pilot executed on Linux+NVIDIA host and archived with `pilot_status=executed`
  - closure readiness is `ready=true`

M15.0 outcome (2026-02-22):

- web orchestration API skeleton added:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- run script and validation added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- contract added:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/118_web_e2e_orchestrator_api_contract.md`

M15.1 outcome (2026-02-22):

- run summary upgraded to frontend-compatible v2 schema:
  - `scene_json`, `outputs`, `path_summary`, `adc_summary`, `radar_map_summary`, `quicklook`
- backward compatibility kept via `artifacts` mirror of `outputs`
- validator upgraded to assert v2 fields and output file existence

M15.2 outcome (2026-02-22):

- dashboard API-run mode added in:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
  - new controls: `apiBase`, `scene_json_path`, `profile`, async toggle, run status
  - run flow: `POST /api/runs` -> poll `/api/runs/{id}` -> auto-load `/api/runs/{id}/summary`
- local combined launcher added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_dashboard_local.sh`
  - starts orchestrator API + static dashboard server in one command

M15.3a outcome (2026-02-22):

- comparison API added in orchestrator:
  - `POST /api/compare` (run/summary targets + parity thresholds override)
  - `GET /api/comparisons`
  - `GET /api/comparisons/{comparison_id}`
- compare result persistence added under:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/web_e2e/comparisons/*.json`
- dashboard compare panel added:
  - reference/candidate `run_id` inputs
  - API compare trigger and parity quick-result display (`pass`, failures, `rd/ra_shape_nmse`)

M15.3b outcome (2026-02-22):

- baseline pinning API added:
  - `POST /api/baselines`
  - `GET /api/baselines`
  - `GET /api/baselines/{baseline_id}`
- policy verdict API added:
  - `POST /api/compare/policy`
  - `GET /api/policy-evals`
  - `GET /api/policy-evals/{policy_eval_id}`
- orchestration store expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/web_e2e/baselines/*.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/web_e2e/policy_evals/*.json`
- dashboard compare section expanded:
  - baseline ID input + baseline pin action
  - policy verdict action and gate-failure details view

M15.4 outcome (2026-02-22):

- regression session API added:
  - `POST /api/regression-sessions`
  - `GET /api/regression-sessions`
  - `GET /api/regression-sessions/{session_id}`
- batch policy-evaluation workflow added:
  - baseline source: `baseline_id` or `reference_*`
  - candidate source: `candidate_run_ids`, `candidate_summary_jsons`, `candidates[]`
  - optional early stop: `stop_on_first_fail`
- orchestration store expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/web_e2e/regression_sessions/*.json`
- dashboard compare section expanded:
  - regression session id input
  - candidate run-id list input (comma/newline)
  - regression session run action + session summary view

M15.5 outcome (2026-02-22):

- regression export API added:
  - `POST /api/regression-exports`
  - `GET /api/regression-exports`
  - `GET /api/regression-exports/{export_id}`
- export artifacts standardized per session:
  - `regression_session.json`
  - `regression_rows.csv`
  - `regression_summary_index.json`
  - `regression_package.json`
- orchestration store expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/web_e2e/regression_exports/<export_id>.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/web_e2e/regression_exports/<export_id>/...`
- validator expanded to assert export manifest endpoints and artifact file integrity

M15.6 outcome (2026-02-22):

- dashboard regression history wiring added in:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- new UI controls added:
  - `Refresh History` (`/api/regression-sessions`, `/api/regression-exports`)
  - session/export history selectors
  - export action (`POST /api/regression-exports`) and artifact download links
- dashboard bootstrap/query handling expanded:
  - query support: `regression_export_id`
  - startup history refresh + selector state restore
- local launcher default URL expanded with regression export query:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_dashboard_local.sh`

M15.7 outcome (2026-02-22):

- dashboard regression gate overview panel added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- overview computes latest gate KPIs from history APIs:
  - session/export counts
  - latest session adopted/held summary
  - linked export coverage
  - quick cue (`ADOPT` / `HOLD` / `REVIEW` / `EMPTY`)
- auto-refresh wiring completed:
  - panel updates on history refresh and startup bootstrap
  - panel reflects new session/export results without page reload

M15.8 outcome (2026-02-22):

- dashboard policy-tuning controls added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- controls include:
  - preset selector (`default` / `strict` / `loose`)
  - `require parity`, `stop on first fail` toggles
  - numeric gates (`max_fail`, `rd_nmse_max`, `ra_nmse_max`)
- API payload wiring expanded:
  - `POST /api/compare` receives `thresholds`
  - `POST /api/compare/policy` receives `policy + thresholds`
  - `POST /api/regression-sessions` receives `policy + thresholds + stop_on_first_fail`
- launcher URL defaults include policy preset query:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_dashboard_local.sh`

M15.9 outcome (2026-02-22):

- dashboard decision-audit panel added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- audit panel summarizes latest decision quality signals:
  - selected/latest session summary (`evaluated`, `held`, export linked)
  - recent hold-rate trend across last sessions
  - per-rule gate-failure histogram (`gate_failures.rule`)
  - hot candidate line (max gate-failure count row)
- history fetch path expanded:
  - `GET /api/policy-evals` joined with sessions/exports to build rule histogram
- panel auto-updates on bootstrap/history refresh/session selection

M15.10 outcome (2026-02-22):

- dashboard review-bundle hook added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- one-click flow implemented:
  - export (or reuse) review bundle via `POST /api/regression-exports` (`include_policy_payload=true`)
  - derive package path from export artifacts (`package_json` preferred)
  - copy package path to clipboard
- new UI elements:
  - `copyReviewBundleBtn`
  - `reviewBundleStatus`
  - `reviewBundlePathBox`
- state wiring completed:
  - selected export updates review bundle path/status
  - history refresh syncs active review bundle path

M15.11 outcome (2026-02-22):

- dashboard decision report template export added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- one-click markdown handoff skeleton:
  - button: `Export Decision Report (.md)`
  - generated file includes metadata, policy config, gate overview, decision-audit snapshot, artifact pointers, and reviewer checklist
  - markdown template is downloaded and copy-to-clipboard is attempted
- new UI state fields:
  - `decisionReportStatus`
  - `decisionReportFileBox`

M15.12 outcome (2026-02-22):

- decision report exporter enhanced with auto evidence extraction:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- new helper flow:
  - `collectTopFailureEvidenceRows(maxItems)` ranks gate-failure evidence from focused regression session rows joined with `policy_evals`
  - `formatEvidenceValue(v)` normalizes numeric/non-numeric evidence values for markdown readability
- markdown template now auto-adds:
  - `Top Failure Evidence (Auto-Extracted)` section
  - top-N failure lines (`candidate`, `policy_eval_id`, `rule`, optional `metric`, `value`, `limit`, `row_failures`)
  - graceful fallback line when no gate-failure evidence exists

M15.13 outcome (2026-02-22):

- dashboard evidence drill-down panel added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- new reviewer loop controls:
  - failed candidate selector (`evidenceCandidateSelect`)
  - per-failure rule selector (`evidenceRuleSelect`)
  - quick actions (`Use Candidate`, `Open Policy Eval`)
- new evidence join/render flow:
  - `collectFocusedSessionFailureRows()` joins focused session rows with `policy_evals`
  - `updateEvidenceDrillDown()` renders focused candidate/policy-eval/failure details
  - `pivotCompareCandidateFromDrill()` and `openEvidencePolicyEvalFromDrill()` shorten review workflow
- history/session refresh paths now auto-sync evidence panel state with gate/audit state

M16.0 outcome (2026-02-22):

- ReactFlow-first graph contract baseline added:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/graph_contract.py`
- new graph endpoints on orchestrator API:
  - `GET /api/graph/templates`
  - `POST /api/graph/validate`
  - `/health` now includes `graph_template_count`
- validation harness expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
  - covers valid template graph pass + cycle graph fail
- planning/contract docs added:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/126_reactflow_simulink_style_plan.md`
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/128_web_e2e_graph_contract_validation_api.md`

M16.1 outcome (2026-02-22):

- ReactFlow graph shell page added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- v1 shell capabilities:
  - graph canvas (`@xyflow/react`) with edge connect/edit
  - template fetch/load via `GET /api/graph/templates`
  - node inspector with JSON params editor
  - contract validation action via `POST /api/graph/validate`
  - graph export (`web_e2e_graph_schema_v1` payload)
- local launcher added:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_graph_lab_local.sh`

M16.2 outcome (2026-02-22):

- graph run bridge API added to orchestrator:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- new endpoints:
  - `POST /api/graph/runs` (`async` query supported)
  - `GET /api/graph/runs`
  - `GET /api/graph/runs/{graph_run_id}`
  - `GET /api/graph/runs/{graph_run_id}/summary`
- graph run persistence added:
  - `data/web_e2e/graph_runs/<graph_run_id>/graph_run_record.json`
  - `data/web_e2e/graph_runs/<graph_run_id>/graph_run_summary.json`
  - `data/web_e2e/graph_runs/<graph_run_id>/graph_payload.json`
- health payload expanded:
  - `graph_run_count`
- ReactFlow shell bridge hookup:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - `Run Graph (API)` action now executes graph and shows summary/artifact pointers

M16.3 outcome (2026-02-22):

- Graph Lab artifact inspector panel expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- artifact visibility features:
  - direct links for `path_list_json`, `adc_cube_npz`, `radar_map_npz`, `graph_run_summary_json`
  - run-level KPIs (`path_count_total`, `adc_shape`, `rd_shape`, `ra_shape`)
  - per-node output trace from `execution.node_results`
  - visual thumbnails (`rd_map`, `ra_map`, `adc`, `path_scatter`) when available
- path normalization helper added for absolute->served repo path mapping:
  - `normalizeRepoPath(pathValue)`

M16.4 outcome (2026-02-22):

- Graph Lab gate workflow added on graph-run outputs:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- one-screen gate loop:
  - `Pin Baseline` (baseline from `graph_run_summary_json`)
  - `Policy Gate` (baseline vs candidate graph summary)
  - `Export Gate Report (.md)` (gate-failure markdown handoff)
- frontend state additions:
  - `baselineId`, `gateResultText`, `lastPolicyEval`
- backend robustness fix for summary-based baselines:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
  - `_resolve_target_with_optional_prefix` now treats `None/null` run-id tokens as empty and falls back to summary path resolution
- validator expanded to cover graph-summary baseline + policy gate path:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`

M16.5 outcome (2026-02-22):

- graph run hardening completed on orchestrator:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- performance/reliability additions:
  - cache keying (`scene revision + graph payload`) and full cache reuse on repeated runs
  - partial rerun cache path (RadarMap node): reuse cached Path/ADC and recompute only RD/RA map
  - cooperative cancel handling (`POST /api/graph/runs/{id}/cancel`) and retry endpoint (`POST /api/graph/runs/{id}/retry`)
  - stale active-run recovery on startup (`queued/running/cancel_requested -> failed-recoverable`)
  - failure surface payload (`failure.type/message/traceback`) + structured `recovery` hints
- frontend hardening hooks in Graph Lab:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - run panel now shows cache hit/scope/source
  - failure/recovery details rendered when summary fetch fails or run status is non-completed
  - new controls: `Retry Last Run`, `Cancel Last Run`
- validator coverage extended:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
  - covers full-cache hit, partial rerun hit, async cancel, retry from canceled run, failure guidance, retry from failed run

M17.0 outcome (2026-02-22):

- Graph Lab async run monitor flow added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- run execution UX updates:
  - run mode selector (`sync|async`)
  - async poll config (`Auto Poll`, poll interval ms)
  - poll state/status indicator (`poll_state`, `polling_active`)
  - manual poll action (`Poll Last Run`)
- execution behavior updates:
  - `Run Graph (API)` now submits with `?async=0|1` based on UI mode
  - async submission path can auto-poll until terminal state and auto-load summary on completion
  - retry path also respects sync/async mode and polling behavior
  - non-terminal/failed/canceled rows reuse recovery rendering for consistent operator feedback

M17.1 outcome (2026-02-22):

- Graph Lab frontend modularization completed:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/main.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- helper/runtime modules introduced:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/deps.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/constants.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/graph_helpers.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/run_monitor.mjs`
- behavioral parity preserved for M16.5/M17.0 run controls:
  - cache/cancel/retry/poll flows remain in `app.mjs`
  - async run tokens and endpoint bindings remain unchanged (`?async=...`, retry/cancel routes)

M17.2 outcome (2026-02-22):

- Graph Lab component/API split completed:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/api_client.mjs`
- frontend modular responsibilities clarified:
  - `app.mjs`: state + action orchestration only
  - `panels.mjs`: left/center/right panel rendering components
  - `api_client.mjs`: graph/baseline/policy endpoint wrappers
- M16.5/M17.0 behavior parity preserved:
  - async run/retry query binding (`?async=...`) unchanged
  - cancel/recovery/gate workflows still exposed in UI controls

M17.3 outcome (2026-02-22):

- Graph Lab action hooks split completed:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- responsibilities clarified:
  - `useGraphRunOps`: run submit/poll/retry/cancel/recovery
  - `useGateOps`: baseline pin/policy gate/report export
  - `app.mjs`: state + orchestration wiring
- behavioral parity preserved for existing operator controls:
  - run mode (`sync|async`), auto-poll, poll-last, retry/cancel actions remain wired to same backend endpoints

M17.4 outcome (2026-02-22):

- Graph input panel binding interface grouped to reduce fan-out:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- new panel binding contract shape:
  - `model.values`, `model.setters`, `model.templateActions`, `model.graphActions`, `model.runActions`, `model.gateActions`
- behavior parity maintained:
  - existing run/gate/operator controls preserved with same hook and API route wiring

M17.5 outcome (2026-02-22):

- frontend runtime contract guard module added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
- typed + guarded binding paths applied:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
- contract behavior:
  - panel model contract normalized to `graph_inputs_panel_model_v1`
  - run/gate hook option contracts normalized (`graph_run_ops_options_v1`, `gate_ops_options_v1`)
  - missing/invalid fields degrade safely with one-time warning + no-op fallback handlers

M17.6 outcome (2026-02-22):

- contract diagnostics counters/snapshot APIs added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
  - `getContractWarningSnapshot`, `resetContractWarnings`, `contract_warning_debug_v1`
- diagnostics UI surfaced in Graph Inputs panel:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - new controls: `Contract Guard`, `Refresh Guard`, `Reset Guard`
- diagnostics wiring added in app orchestration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - snapshot formatting + state (`contractDebugText`) + action bridging

M17.7 outcome (2026-02-22):

- automatic contract diagnostics propagation added across run/gate paths:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
- run/gate result surfaces now carry guard counters:
  - graph run text includes `contract_warning_unique`, `contract_warning_attempts`
  - graph run summary path adds `contract_diagnostics:` block
  - policy gate result text includes `contract_warning_unique`, `contract_warning_attempts`
- auto-refresh wiring expanded in app orchestration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - contract snapshot refresh effect now tracks `graphRunText`, `gateResultText`, `validationText`
- Node Inspector diagnostics visibility expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - new auto box: `Contract Diagnostics (Auto)`

M17.8 outcome (2026-02-22):

- opt-in contract overlay/timeline wiring completed:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- contract model/options extended for overlay and event callbacks:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
  - `contractOverlayEnabled`, `contractTimelineCount`, `setContractOverlayEnabled`, `clearContractTimeline`, `onContractDiagnosticsEvent`
- run/gate hooks now emit structured contract diagnostics events and deltas:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - delta tokens: `contract_warning_delta_unique`, `contract_warning_delta_attempts`
  - runtime object: `runtime_contract_diagnostics`
- Artifact Inspector now surfaces per-run contract delta/total KPIs:
  - `contract_delta(unique/attempt)`
  - `contract_total(unique/attempt)`

M17.9 outcome (2026-02-22):

- timeline operator utilities added in overlay:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - source filter, non-zero delta filter, filtered count, `Export JSON`
- overlay filter styling added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - `contract-overlay-filter` block styles
- timeline export action added in app orchestration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - payload version: `contract_timeline_export_v1`
- gate handoff report now includes contract diagnostics slices:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - report section: `## Contract Diagnostics` with `run.*` and `gate.*` delta/total fields

M17.10 outcome (2026-02-22):

- overlay compact mode and run pin filters added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - compact toggle (`Compact: on/off`)
  - run pin selector (`run:`)
- severity badge + row styling added for timeline triage:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - badges/classes: `contract-sev-badge`, `contract-sev-high|med|low`
- gate report now includes timeline tail references:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - section: `## Contract Timeline Tail` (`active_graph_run_id`, `scoped_event_count`, `tail_event_count`, `sev`)
- gate hook contract options extended:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
  - `contractTimeline` option read path + app forwarding from `contractTimeline` state

M17.11 outcome (2026-02-22):

- timeline row -> graph-run jump action added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - new action: `openGraphRunById`
  - overlay-open event sources: `graph_run_overlay_open`, `graph_run_overlay_open_non_completed`
- overlay run-open wiring completed:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - row action: `Open Run` (also pins run filter to selected run id)

M17.12 outcome (2026-02-22):

- policy failure correlation tags auto-attached on timeline rows:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - tag format: `policy:HOLD#<count>` or `policy:ADOPT`
  - style classes: `contract-policy-tag.hold|adopt`
- policy correlation metadata enriched at source:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - event note fields: `failure_count`, `failure_rules`
- gate report timeline tail now includes policy correlation token:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - tail line field: `policy:...`

M17.13 outcome (2026-02-22):

- timeline -> gate evidence deep-link added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - row action: `Open Gate` (policy-evidence summary loaded into `Policy Gate Result`)
- per-rule failure badges added on timeline rows:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - style class: `contract-failure-rule-badge`
- run-open action exposed as reusable hook endpoint:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - action: `openGraphRunById`

M17.14 outcome (2026-02-22):

- persisted policy-eval fetch path added for timeline gate evidence:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/api_client.mjs`
  - new API wrappers: `listPolicyEvals`, `getPolicyEval`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `Open Gate` flow now resolves evidence from persisted policy-eval artifacts first
- fallback lookup strategy added when direct `policy_eval_id` fetch is unavailable:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - match order: `policy_eval_id` -> `run_id+summary_json` -> `run_id` -> `summary_json` -> `baseline_id`
  - evidence trace fields emitted: `evidence_source`, `policy_eval_scan_count`
- gate-event metadata hardened for lookup stability:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
  - timeline note now includes `candidate_run_id` + `candidate_summary_json`

M17.15 outcome (2026-02-22):

- `policy-evals` API now supports filtered pagination for large history:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
  - query params: `candidate_run_id`, `baseline_id`, `limit`, `offset`
  - response page metadata: `total_count`, `returned_count`, `filtered`, `limit`, `offset`
- frontend API client now emits filtered query requests:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/api_client.mjs`
  - `listPolicyEvals(apiBase, { candidateRunId, baselineId, limit, offset })`
- timeline gate evidence lookup now uses cache + scoped queries first:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - cache TTL/eviction applied (`policyEvalListCacheRef`)
  - lookup order: `run_id(+baseline)` -> `baseline` -> `global`
  - trace fields added: `policy_eval_cache_hit_any`, `policy_eval_scan_count`

M17.16 outcome (2026-02-22):

- overlay now exposes gate-history lookup knobs directly:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - controls added: `gate window`, `max pages`, `+page`
  - row `Open Gate` now passes lookup options (`historyLimit`, `pageBudget`)
- gate-evidence resolver supports incremental paged scans per scope:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - per-scope scan loops by page (`offset = page * historyLimit`) until match/end/budget
  - evidence source now records page index (`...:pageN`)
- operator traceability fields expanded for tuning/diagnostics:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `policy_eval_history_limit`, `policy_eval_page_budget`, `policy_eval_page_count_used`

M17.17 outcome (2026-02-22):

- timeline row rendering now uses windowed view instead of full filtered render:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - render path switched to `visibleRows` from `filteredRows`
  - row-window controls added: `rows/window`, `Top`, `Prev`, `Next`
- overlay preference persistence added via browser localStorage:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - key: `graph_lab_contract_overlay_prefs_v1`
  - persisted options: filters, compact mode, gate lookup knobs, row-window size
- operator context indicator improved:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - filter bar now displays window coverage (`window start-end/filtered_count`)

M17.18 outcome (2026-02-22):

- overlay preset operations added for quick mode switching:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Preset: Triage`, `Preset: Deep`, `Reset Preset`
  - preset applier: `applyOverlayPreset("triage"|"deep_gate"|"reset_all")`
- keyboard shortcut layer added for overlay operators:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - shortcuts: `h`, `c`, `n`, `j`, `k`, `g`, `1`, `2`, `0`
  - editable target guard: `isEditableElementTarget` (input/textarea/select/contenteditable 제외)
- shortcut discoverability exposed in UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - toggle: `Shortcuts: on/off`
  - inline hint line with key map summary

M17.19 outcome (2026-02-22):

- row details now render only when requested (lazy-expansion):
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - row actions include `Details`/`Hide` toggle in compact and full modes
  - detail renderer computes payload only when expanded (`formatRowDetailText`)
- batch detail controls added for visible window:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Expand Visible`, `Collapse Details`
  - shortcuts: `e` (expand visible), `x` (collapse details)
- detail UI styling and readability support added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
  - classes: `contract-row-detail-btn`, `contract-overlay-row-detail`

M17.20 outcome (2026-02-22):

- overlay shortcuts are now remappable with profile persistence:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - profile store key: `graph_lab_contract_overlay_shortcut_profiles_v1`
  - profile ops: `Load Profile`, `Save Profile`, `Delete Profile`, `Reset Keys`
- dynamic key dispatch replaces hardcoded shortcut branching:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - dispatch map: `shortcutActionByKey`
  - action router: `triggerShortcutAction(...)`
  - help line now renders from current bindings (`shortcutHintText`)
- remap safety/traceability added for operators:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - per-action inline key editor for all overlay actions
  - duplicate key detection + conflict hint (`first mapping wins`)
  - prefs now persist active profile/draft/bindings in overlay localStorage

M17.21 outcome (2026-02-22):

- row detail payload is now field-selectable at runtime:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - detail fields: `time`, `event/run`, `delta`, `snapshot`, `baseline`, `note_json`
  - per-field checkbox toggles + selection counter (`selected n/6`)
- detail field presets added for faster triage/deep workflows:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Core Fields`, `All Fields`
  - overlay presets now align detail scope (`triage -> core`, `deep -> all`)
- detail rendering and persistence hardened:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `formatRowDetailText` now emits only selected sections
  - `note_json` serialization runs only when selected
  - field-state selection persisted via overlay prefs (`detailFieldStates`)

M17.22 outcome (2026-02-22):

- shortcut profiles are now export/import-shareable as JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - export bundle metadata: `schema_version`, `kind`, `exported_at_iso`, `profiles`
  - import parser accepts bundle form or direct profile-map form
- operator transfer workflow controls added to overlay:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Export Profiles`, `Copy Profiles`, `Load JSON`, `Import Profiles`
  - transfer editor/status fields: `co_shortcut_transfer_text`, `co_shortcut_transfer_status`
- import/export hardening behavior:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - profile names normalized (`normalizeShortcutProfileName`)
  - invalid payload guard with explicit status (`import failed: ...`)
  - imported profiles are normalized to current action schema

M17.23 outcome (2026-02-22):

- detail copy workflow added at overlay-level and row-level:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Copy Visible` + per-row `Copy`
  - copy payload respects current field toggle selection (`formatRowDetailText`)
- clipboard/status handling added for operator feedback:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - helper: `copyTextToClipboard(...)`
  - status field: `detail_copy: ...` (`co_detail_copy_status`)
- copy behavior scope definition:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - visible-copy outputs current row window with row/run/source headers
  - row-copy supports compact/full rows and non-run rows consistently

M17.24 outcome (2026-02-22):

- severity-first triage filtering added to overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - filter options: `all`, `high`, `med`, `low`
  - quick severity buttons with scoped counts: `high:n`, `med:n`, `low:n`
- filter pipeline split for clearer operator context:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `scopedRows` (source/run/non-zero scope) -> `filteredRows` (severity-applied)
  - count line now shows `filtered/scoped/all`
- preset/persistence integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `Preset: Triage` now defaults severity to `high`
  - `severityFilter` persisted in overlay prefs and restored on reload

M17.25 outcome (2026-02-22):

- policy-first triage filtering added to overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - filter options: `all`, `hold`, `adopt`, `none`
  - quick policy buttons with severity-scoped counts: `hold:n`, `adopt:n`, `none:n`
- filter pipeline expanded for clearer diagnostic scope:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `scopedRows` -> `severityScopedRows` -> `filteredRows(policy-applied)`
  - count line now shows `policy/severity/scoped/all`
- preset/persistence integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `Preset: Triage` now defaults policy to `hold`
  - `policyFilter` persisted in overlay prefs and restored on reload

M17.26 outcome (2026-02-22):

- active filter summary surfaced as compact chips:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - summary block: `active filters: ...` (`co_filter_summary`)
  - chips include source/severity/policy/run/non-zero/gate-window/page/rows-window deltas
- filter-only reset action added (view-state preserving):
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - action: `Reset Filters` (`co_reset_filters`)
  - resets scope filters without altering detail/shortcut/compact preference states
- quick button ergonomics expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - severity quick map now includes `all` alongside `high/med/low`
  - policy quick map now includes `all` alongside `hold/adopt/none`

M17.27 outcome (2026-02-22):

- filter preset profiles added for repeatable triage scopes:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - storage key: `graph_lab_contract_overlay_filter_presets_v1`
  - built-ins: `default`, `triage_hold_high`
- filter preset lifecycle controls added in overlay:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Load Filter Preset`, `Save Filter Preset`, `Delete Filter Preset`
  - profile UI keys: `co_filter_preset_select`, `co_filter_preset_draft`
- persistence/normalization hardening:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - profile name sanitizer: `normalizeFilterPresetName`
  - payload normalizer: `normalizeFilterPresetConfig`
  - active preset/draft persisted in overlay prefs and restored on reload

M17.28 outcome (2026-02-22):

- filter preset transfer bundle/export parser added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - helpers: `buildFilterPresetExportBundle`, `serializeFilterPresetExportBundle`, `parseFilterPresetImportText`
  - bundle metadata: `schema_version`, `kind`, `exported_at_iso`, `presets`
- overlay transfer workflow controls added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Export Filter Presets`, `Copy Filter Presets`, `Load Filter JSON`, `Import Filter Presets`
  - UI keys: `co_filter_transfer_cfg`, `co_filter_transfer_text`, `co_filter_transfer_status`
- import/export hardening behavior:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - parser accepts bundle form or direct preset-map form
  - invalid payload guard with explicit status (`import failed: ...`)
  - imported presets normalized to current filter schema before merge

M17.29 outcome (2026-02-22):

- transfer import guardrails expanded with explicit mode control:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - mode options: `merge (overwrite same name)`, `replace custom presets`
  - mode persistence key in overlay prefs: `filterImportMode`
- payload conflict preview surfaced before import apply:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - preview content: `total/new/overwrite/built-in overwrite/mode`
  - preview UI key: `co_filter_import_preview`
- import safety behavior tightened:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - invalid payload now disables import action
  - `replace_custom` mode preserves built-ins while replacing existing custom presets

M17.30 outcome (2026-02-22):

- selective import controls added for transfer payload presets:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions: `Select All`, `Select None`
  - per-preset selectors: `co_filter_import_row_<name>`
- dry-run conflict visibility expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - parsed payload model: `parsedFilterImportPayload`
  - preview now reports selected subset and conflict classes (`new`, `overwrite_custom`, `overwrite_builtin`)
- import apply path now obeys selected subset:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - unselected presets are excluded from apply
  - empty selection returns explicit no-op status (`import skipped: no presets selected`)

M17.31 outcome (2026-02-22):

- replace-mode destructive apply now requires explicit confirmation:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - confirmation control key: `co_filter_replace_confirm`
  - import apply guard status: `confirm required: enable replace confirmation for replace custom`
- import undo recovery path added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - snapshot helper: `cloneNormalizedFilterPresets`
  - actions/keys: `Undo Last Import` (`co_filter_import_undo`), `co_filter_import_undo_hint`
- safety behavior:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - replace confirmation automatically resets on payload change
  - undo restores preset map + active preset + draft name from captured snapshot

M17.32 outcome (2026-02-22):

- import operation audit trail added with change metrics:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - audit state: `filterImportAuditTrail`
  - per-entry summary: `selected`, `added`, `changed`, `removed`, `mode`, `note`
- import history upgraded from single snapshot to multi-level stacks:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - stacks: `filterImportUndoStack`, `filterImportRedoStack`
  - actions: `Undo Import`, `Redo Import`
- snapshot/diff scaffolding hardened:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - helpers: `buildFilterPresetStateSnapshot`, `compactNameList`
  - import status now reports `+added/~changed/-removed` counts

M17.33 outcome (2026-02-22):

- audit detail drilldown controls added in import transfer area:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - controls: `Copy Audit Detail`, `Export Audit JSON`
  - detail panel key: `co_filter_import_audit_detail`
- audit row selection and detail rendering expanded:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - active selector state: `activeFilterImportAuditId`
  - helper: `buildFilterImportAuditDetailText`
  - audit rows now include compact selected-name preview
- import history persistence added (bounded localStorage):
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - storage key: `graph_lab_contract_overlay_filter_import_history_v1`
  - helpers: `loadFilterImportHistoryState`, `saveFilterImportHistoryState`
  - startup restore + runtime sync for undo/redo/audit stacks

M17.34 outcome (2026-02-22):

- import history maintenance controls added in audit toolbar:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - actions/keys: `co_filter_import_prune_keep`, `co_filter_import_prune`, `co_filter_import_clear`
  - behavior: bounded prune for undo/redo/audit stacks + full clear reset
- audit search/filter interactions added for operator drilldown:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - controls/keys: `co_filter_import_audit_search`, `co_filter_import_audit_kind`, `co_filter_import_audit_mode`
  - computed view model: `filterImportAuditRowsFiltered`
- audit list/detail synchronization hardened under filtered views:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - active entry auto-fallback when filtered result changes
  - visibility hint key: `co_filter_import_audit_count`

M17.35 outcome (2026-02-23):

- audit query reset ergonomics added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - callback: `resetFilterImportAuditQuery`
  - UI key: `co_filter_import_audit_reset`
  - reset scope: `search text + kind filter + mode filter`
- row-volume guardrail added for large filtered timelines:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - thresholds: `CONTRACT_ROW_VOLUME_GUARD_TRIGGER`, `CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW`
  - behavior: when guard active and bypass is off, `rows/window` options are capped to safe range
- operator override/persistence and visibility cues:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - toggle key: `co_row_volume_guard_bypass`
  - hint key: `co_row_volume_guard_hint`
  - active-filter token includes `rows_guard:off` when bypass is enabled

M17.36 outcome (2026-02-23):

- audit query preset shortcuts added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - preset model: `FILTER_IMPORT_AUDIT_QUERY_PRESETS`
  - active preset detector: `activeFilterImportAuditQueryPresetId`
  - apply callback: `applyFilterImportAuditQueryPreset`
- audit list pagination cap and window navigation added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - cap options: `FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS`
  - paging state: `filterImportAuditRowCapText`, `filterImportAuditRowOffset`
  - computed window: `filterImportAuditRowsVisible`, `filterImportAuditMaxOffset`, `filterImportAuditRowEnd`
- audit view-state persistence/UX updates:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - overlay prefs key now stores `filterImportAuditRowCap`
  - controls/keys: `co_filter_import_audit_row_cap`, `co_filter_import_audit_top`, `co_filter_import_audit_prev`, `co_filter_import_audit_next`, `co_filter_import_audit_window_hint`

M17.37 outcome (2026-02-23):

- audit detail deep-link copy bundle added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - helpers: `buildFilterImportAuditDeepLinkBundle`, `serializeFilterImportAuditDeepLinkBundle`
  - action callback: `copyFilterImportAuditDeepLinkBundle`
  - UI key: `co_filter_import_audit_copy_deeplink`
- audit query preset pinning ergonomics added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - resolver/helper: `resolveFilterImportAuditQueryPreset`
  - pin state: `filterImportAuditPinnedPresetId`
  - pin action: `toggleFilterImportAuditPinnedPreset`
  - controls/keys: `co_filter_import_audit_preset_pin`, `co_filter_import_audit_preset_pin_hint`
- persistence + reset behavior alignment:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - overlay prefs now persist `filterImportAuditPinnedPreset`
  - `Reset Query` now restores pinned preset when pinned (`audit query reset -> pinned:<id>`)

M17.38 outcome (2026-02-23):

- audit bundle import/restore action added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - parser: `parseFilterImportAuditDeepLinkBundleText`
  - apply callback: `applyFilterImportAuditDeepLinkBundleFromText`
  - controls/keys: `co_filter_import_audit_apply_deeplink`, `co_filter_import_audit_bundle_preview`
- pinned preset quick-toggle shortcut added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - shortcut action id: `audit_pin_toggle`
  - default binding/profile mapping: `p`
  - shortcut execution path integrated in `triggerShortcutAction`
- deep-link import safety behavior:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - bundle kind mismatch/JSON parse errors surfaced via status (`audit bundle apply failed: ...`)
  - restore scope: query (`search/kind/mode`) + paging (`cap/offset`) + pinned preset + active entry id

M17.39 outcome (2026-02-23):

- audit deep-link schema guardrails tightened:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - constants: `FILTER_IMPORT_AUDIT_DEEPLINK_KIND`, `FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION`
  - parser guards: missing/unsupported `schema_version` now explicit errors
- operator-facing bundle expectation hint added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - key: `co_filter_import_audit_bundle_schema_hint`
  - shows expected `kind/schema` for import payload
- audit preset/shortcut operator hints added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - keys: `co_filter_import_audit_preset_active_hint`, `co_filter_import_audit_shortcut_hint`
  - shows current active query preset + pin-toggle shortcut token

M17.40 outcome (2026-02-23):

- audit deep-link bundle partial-restore toggles added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - restore toggle states:
    - `filterImportAuditRestoreQueryChecked`
    - `filterImportAuditRestorePagingChecked`
    - `filterImportAuditRestorePinnedPresetChecked`
    - `filterImportAuditRestoreActiveEntryChecked`
  - controls/keys:
    - `co_filter_import_audit_restore_scopes`
    - `co_filter_import_audit_restore_query`
    - `co_filter_import_audit_restore_paging`
    - `co_filter_import_audit_restore_pinned`
    - `co_filter_import_audit_restore_entry`
- restore apply behavior now scope-aware:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `applyFilterImportAuditDeepLinkBundleFromText` applies only enabled scopes
  - no-scope case guarded with explicit status (`audit bundle apply skipped: no restore scope enabled`)
- preset pin state chips added for operator situational awareness:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - chip container key: `co_filter_import_audit_pin_state_chips`
  - chip keys:
    - `co_filter_import_audit_pin_chip_pinned`
    - `co_filter_import_audit_pin_chip_active`
    - `co_filter_import_audit_pin_chip_custom`
    - `co_filter_import_audit_pin_chip_shortcut`

M17.41 outcome (2026-02-23):

- audit restore preset shortcuts added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - preset constants/helpers:
    - `FILTER_IMPORT_AUDIT_RESTORE_PRESETS`
    - `resolveFilterImportAuditRestorePreset`
    - `activeFilterImportAuditRestorePresetId`
  - controls/keys:
    - `co_filter_import_audit_restore_presets`
    - `co_filter_import_audit_restore_preset_all`
    - `co_filter_import_audit_restore_preset_query_pin`
    - `co_filter_import_audit_restore_preset_paging_entry`
    - `co_filter_import_audit_restore_preset_query_only`
    - `co_filter_import_audit_restore_preset_active`
- deep-link apply status now reports active restore preset:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - status format includes `restore:<preset|custom>`
- pin-state chip filtering controls added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - option constants/helpers:
    - `FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS`
    - `normalizeFilterImportAuditPinChipFilter`
    - `filterImportAuditPinChipVisibility`
  - controls/keys:
    - `co_filter_import_audit_pin_chip_filters`
    - `co_filter_import_audit_pin_chip_filter_all`
    - `co_filter_import_audit_pin_chip_filter_state`
    - `co_filter_import_audit_pin_chip_filter_context`
    - `co_filter_import_audit_pin_chip_filter_shortcut`
    - `co_filter_import_audit_pin_chip_filter_active`
- prefs persistence/reset updated for chip filter mode:
  - state: `filterImportAuditPinChipFilter`
  - persisted key: `filterImportAuditPinChipFilter`

M17.42 outcome (2026-02-23):

- scoped deep-link quick-apply actions added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - constants/helpers:
    - `FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS`
    - `resolveFilterImportAuditQuickApplyOption`
    - `applyFilterImportAuditDeepLinkBundleWithScopes`
    - `applyFilterImportAuditDeepLinkQuickScope`
  - controls/keys:
    - `co_filter_import_audit_apply_quick_scopes`
    - `co_filter_import_audit_apply_quick_<id>` (`all/query/paging/pinned/entry/query_pin/paging_entry`)
    - `co_filter_import_audit_apply_quick_hint`
- deep-link apply behavior unified under scoped apply helper:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - current restore-toggle apply and quick-apply actions now share the same payload parse/apply path
  - applied status continues schema/scope reporting and includes restore tag (`restore:<preset|quick:...|custom>`)
- restore/pin operator hint refinements added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - keys:
    - `co_filter_import_audit_restore_scope_hint`
    - `co_filter_import_audit_pin_operator_hint`
  - hints summarize effective restore toggle vector and pin/chip operator state

M17.43 outcome (2026-02-23):

- quick-apply/restore coupling refinements added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - coupling state/computed ids:
    - `filterImportAuditQuickApplySyncRestoreChecked`
    - `activeFilterImportAuditQuickApplyOptionId`
  - quick-apply controls/keys:
    - `co_filter_import_audit_apply_quick_sync`
    - `co_filter_import_audit_apply_quick_active`
  - behavior:
    - quick-apply button selection reflects current restore scope match
    - optional `sync->restore` applies quick scope into persistent restore toggles on successful apply
- operator-safe reset affordances added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - safe reset arm state:
    - `filterImportAuditResetArmedChecked`
  - controls/keys:
    - `co_filter_import_audit_safe_reset_controls`
    - `co_filter_import_audit_reset_arm`
    - `co_filter_import_audit_reset_restore_scope`
    - `co_filter_import_audit_reset_pin_context`
    - `co_filter_import_audit_reset_operator_context`
    - `co_filter_import_audit_reset_hint`
- guard/status:
  - reset blocked when not armed (`reset blocked: arm reset first`)
  - explicit status on scoped/operator resets

M17.44 outcome (2026-02-23):

- quick-apply telemetry capture/export hooks added:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - telemetry constants/helpers:
    - `FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT`
    - `normalizeFilterImportAuditQuickApplyTelemetryEntry`
    - `buildFilterImportAuditQuickApplyTelemetryBundle`
    - `serializeFilterImportAuditQuickApplyTelemetryBundle`
  - quick telemetry actions/keys:
    - `copyFilterImportAuditQuickApplyTelemetryJson`
    - `exportFilterImportAuditQuickApplyTelemetryJson`
    - `clearFilterImportAuditQuickApplyTelemetry`
    - `co_filter_import_audit_quick_telemetry_controls`
    - `co_filter_import_audit_quick_telemetry_copy`
    - `co_filter_import_audit_quick_telemetry_export`
    - `co_filter_import_audit_quick_telemetry_clear`
    - `co_filter_import_audit_quick_telemetry_summary`
- quick apply execution now emits telemetry entries:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - telemetry includes option/scope/apply result/sync flags/preset context
- guided reset safety hints improved:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - constants/hints:
    - `FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS`
    - `filterImportAuditResetGuidedHint`
    - `co_filter_import_audit_reset_guided_hint`
  - reset arm now includes timeout expiry status (`reset arm expired: re-arm to execute reset`)


M14.6 outcome (2026-02-28):

- strict Linux+NVIDIA PO-SBR runtime pilot executed and archived
- executed report: `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json`
- closure readiness: `/home/seongcheoljeong/workspace/myproject/docs/reports/m14_6_closure_readiness_linux.json` (`ready=true`)

M17.56 outcome (2026-02-28):

- quick telemetry import filter-bundle parser now supports explicit `import_mode` (`compat|strict`)
- strict mode requires wrapped payload (`filter_bundle`) and explicit `kind/schema_version`
- compat mode keeps legacy bare-object payload acceptance for transition safety
- mode selector + hint wiring added in Graph Lab transfer controls
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/191_web_e2e_graph_audit_quick_telemetry_import_filter_bundle_mode_toggle.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_import_filter_bundle_mode.py`

M17.57 outcome (2026-02-28):

- strict-mode rollout helper added to detect legacy bare-object payload and generate strict wrapped auto-wrap preview
- one-click helper action added (`Wrap Legacy -> Strict`) to replace import text with wrapped payload (`kind/schema/filter_bundle`)
- rollout hints now report migration status (`mode_not_strict`, `already_wrapped`, parse/root issues) for operator guidance
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/192_web_e2e_graph_audit_quick_telemetry_strict_rollout_helper.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_import_filter_bundle_rollout_helper.py`

M17.58 outcome (2026-02-28):

- strict-adoption readiness gate added with signal counters:
  - `attempt_count`, `success_count`, `legacy_wrap_use_count`, `legacy_parse_block_count`
- default-switch checklist summary (`READY|HOLD`) added with pass-count visibility
- gate reset control added for fresh rollout measurement windows
- import/wrap actions now update strict-adoption signals for rollout evidence
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/193_web_e2e_graph_audit_quick_telemetry_strict_adoption_gate.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_adoption_gate.py`

M17.59 outcome (2026-02-28):

- strict-default cutover helper controls added:
  - one-click `Apply Strict Default` action (`mode=strict`)
  - one-click `Switch to Compat Fallback` action (`mode=compat`)
- cutover hint/reminder/status surface added next to strict-adoption gate summary
- cutover status reset integrated with adoption-gate reset and transfer reset flows
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/194_web_e2e_graph_audit_quick_telemetry_strict_default_cutover_helper.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_cutover_helper.py`

M17.60 outcome (2026-02-28):

- strict-cutover timeline ledger added:
  - apply/fallback helper actions now append timeline events with checklist snapshot (`READY|HOLD`, pass count, strict signal counters)
  - timeline hint/preview surface added in transfer panel for rapid operator audit
- timeline export controls added:
  - one-click `Export Cutover Timeline` / `Copy Cutover Timeline` / `Reset Cutover Timeline`
  - status trail messages added for event logging/export/copy/reset outcomes
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/195_web_e2e_graph_audit_quick_telemetry_strict_cutover_timeline_ledger.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_cutover_timeline.py`

M17.61 outcome (2026-02-28):

- strict-cutover rollback drill helper added:
  - failure-tagged rollback presets (`parse_error`, `invalid_payload`, `no_scope`) now switch to compat fallback with one click
  - rollback drill checklist added (`mode_compat`, `failure_only`, `reason_query`, `failure_rows`) with `READY|HOLD` summary
- rollback drill status trail wired with cutover helper actions for operator rehearsal feedback
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/196_web_e2e_graph_audit_quick_telemetry_strict_rollback_drill_helper.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_drill_helper.py`

M17.62 outcome (2026-02-28):

- strict-rollback drill package export added:
  - package includes preset snapshot (`preset_id`, mode, reason/filter bundle snapshot)
  - package includes checklist report payload (`READY|HOLD`, pass/item counts, item rows)
  - package includes cutover timeline summary + event entries
- checklist report handoff controls added:
  - one-click `Copy Checklist Report` with report preview block
  - package export/copy status trail added for operator feedback
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/197_web_e2e_graph_audit_quick_telemetry_strict_rollback_drill_package.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_drill_package.py`

M17.63 outcome (2026-02-28):

- strict-rollback package replay helper added:
  - rollback package JSON parser with schema/kind validation and import preview surface
  - checklist delta guard added (`status/pass/item/fail/item-ok-diff`) before replay
  - delta override confirm checkbox blocks replay when drift exists until explicit operator confirmation
- replay action now applies imported snapshot/filter state and rehydrates cutover timeline entries for operator drill replay
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/198_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_replay_helper.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_replay_helper.py`

M17.64 outcome (2026-02-28):

- strict-rollback package provenance guard added:
  - export payload now includes `provenance.source_stamp` + checksum fields/hints
  - replay parser now normalizes provenance guard state (`source_match`, `checksum_match`, missing-field detection)
- replay guard behavior strengthened:
  - provenance issue is treated as replay guard condition alongside checklist delta guard
  - confirmation copy updated to reflect combined guard (`delta/provenance`)
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/199_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_provenance_guard.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_provenance_guard.py`

M17.65 outcome (2026-02-28):

- strict rollback package trust policy added:
  - policy modes added (`strict_reject`, `compat_confirm`)
  - `strict_reject` blocks normal replay when provenance guard fails
- operator override replay/logging added:
  - one-click `Override Reject + Replay` action for strict policy bypass
  - override events logged with policy/provenance metadata and export/copy/reset controls
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/200_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_policy.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_policy.py`

M17.66 outcome (2026-02-28):

- strict rollback trust-audit bundle export added:
  - dedicated trust-audit package now includes trust policy, normalized override log entries, and provenance snapshot fields
  - provenance snapshot now captures parse state/error + package metadata (`kind`, `schema_version`, preset, import mode, timeline entry count)
- trust-audit handoff controls added:
  - one-click `Copy Trust Audit Bundle` / `Export Trust Audit Bundle` actions with preview + status trail
  - trust-audit status reset wired on rollback replay/reset paths to avoid stale operator messages
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/201_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle.py`

M17.67 outcome (2026-02-28):

- strict rollback trust-audit handoff parser added:
  - strict parser validates trust-audit kind/schema before import preview
  - parser now enforces required trust-audit sections (`override_log.entries[]`, `provenance_snapshot`)
- import preview guardrails added:
  - transfer panel now shows trust-audit schema hint + invalid guidance strings for kind/schema/structure errors
  - handoff import preview line summarizes parsed policy/override-count/provenance snapshot metadata
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/202_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_handoff_parser.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_handoff_parser.py`

M17.68 outcome (2026-02-28):

- strict rollback trust-audit apply helper added:
  - one-click apply action now hydrates trust policy mode from parsed handoff payload
  - apply action now hydrates override log rows from handoff `override_log.entries` and clears override-reason draft text
- apply status wiring added:
  - explicit apply status paths for empty payload / invalid payload / successful hydrate
  - import textarea edit now clears stale trust-audit apply/export status
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/203_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_helper.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_helper.py`

M17.69 outcome (2026-02-28):

- strict rollback trust-audit apply safety gate added:
  - apply safety memo now compares incoming trust policy + override log against live state to detect replacement risk
  - `Apply Trust Audit Bundle` now blocks with explicit status until replace-confirm is checked when risk exists
- safety hint/confirm controls added:
  - apply-safety hint surfaces risk breakdown (`policy change`, `override log replacement`) in transfer panel
  - replace-confirm checkbox is auto-cleared when risk is removed (payload/state change)
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/204_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_gate.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_gate.py`

M17.70 outcome (2026-02-28):

- trust-audit apply confirm auto-disarm added:
  - apply confirm arm now tracks `armed_at`/tick timer with bounded safety window (`20s`)
  - armed confirm auto-resets after timer expiry with explicit status message
- operator countdown hint added:
  - transfer panel now shows live confirm countdown hint (`armed Xs left`, auto-disarm warning near expiry)
  - timer state is cleared on payload/reset/apply flows where confirm is disarmed
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/205_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_auto_disarm.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_auto_disarm.py`

M17.71 outcome (2026-02-28):

- trust-audit apply dry-run diff summary added:
  - incoming handoff payload is now compared against live trust policy + override log snapshot before apply
  - dry-run summary tracks policy-change flag plus override-log diff counts (`added`, `removed`, `changed`, `unchanged`)
- dry-run operator surfaces added:
  - one-line dry-run hint added near apply safety controls
  - multiline dry-run preview block added (`policy`, `override_count`, `override_diff`, latest live/incoming override rows)
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/206_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_summary.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_summary.py`

M17.72 outcome (2026-02-28):

- trust-audit apply dry-run handoff package export/copy added:
  - dedicated handoff package schema/kind helpers serialize dry-run summary + apply-safety snapshot + trust-audit bundle snapshot
  - handoff package is now available for operator copy/export as JSON payload
- dry-run handoff operator surfaces added:
  - one-line handoff hint added near dry-run preview/apply controls
  - multiline handoff preview block added (`kind/schema`, summary diff, safety flags, import preview)
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/207_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package.py`

M17.73 outcome (2026-02-28):

- trust-audit apply dry-run handoff package parser added:
  - strict parser validates handoff package kind/schema and required sections (`dry_run_summary`, `apply_safety`, `trust_audit_bundle_snapshot`)
  - parser guidance now returns actionable hints for kind/schema/structure errors
- dry-run handoff import preview surfaces added:
  - parser-aware import preview line summarizes parsed dry-run policy/diff/safety and bundle metadata
  - dedicated import textarea + schema-hint block added near dry-run handoff copy/export controls
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/208_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_parser.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_parser.py`

M17.74 outcome (2026-02-28):

- dry-run handoff apply helper added:
  - one-click apply action hydrates imported dry-run handoff snapshot state from parsed payload
  - hydrated snapshot captures imported package details plus `hydrated_at_iso` for operator traceability
- hydrated status/preview surfaces added:
  - apply helper now emits explicit status paths for empty payload / parse error / invalid payload / successful hydrate
  - dedicated hydrated hint + multiline preview block plus reset action added near dry-run handoff import controls
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/209_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_helper.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_helper.py`

M17.75 outcome (2026-02-28):

- dry-run handoff hydrate safety gate added:
  - apply helper now compares incoming handoff payload against existing hydrated snapshot to detect replacement risk
  - hydrate action now blocks with explicit status until replace-confirm is checked when overwrite risk exists
- hydrate safety hint/confirm controls added:
  - safety hint line summarizes replacement-risk state near dry-run handoff import/apply controls
  - replace-confirm checkbox is auto-cleared when risk is removed (payload/hydrated-state reset)
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/210_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_gate.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_gate.py`

M17.76 outcome (2026-02-28):

- dry-run handoff hydrate safety auto-disarm added:
  - hydrate replace-confirm now arms a bounded safety timer (`20s`) and auto-disarms when timer expires
  - hydrate apply/reset flows now clear armed timer state to avoid stale confirm carry-over
- hydrate safety countdown/operator hint surfaces added:
  - countdown hint line now shows remaining confirm window (`armed`, `expired`, `not armed`) near hydrate controls
  - auto-disarm and arm/disarm status strings now provide explicit operator guidance for re-check behavior
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/211_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_auto_disarm.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_auto_disarm.py`

M17.77 outcome (2026-02-28):

- dry-run handoff hydrate confirm activity trail added:
  - bounded activity trail now records confirm arm/disarm events across manual toggles, auto-disarm timeout, and flow-driven disarm paths
  - activity row retention is capped by a dedicated limit constant to keep UI timeline bounded
- operator activity hint/preview surfaces added:
  - activity hint line now summarizes trail usage and latest event timestamp near hydrate confirm controls
  - multiline preview now lists newest-first confirm activity rows (`time | event | detail`) for local operator audit
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/212_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_trail.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_trail.py`

M17.78 outcome (2026-02-28):

- dry-run handoff hydrate confirm activity controls added:
  - confirm activity trail now supports explicit copy/export JSON actions for operator handoff
  - confirm activity trail now supports explicit reset action to clear stale timeline state between hydration attempts
- activity bundle contract added:
  - export/copy now emits bounded schema/kind-tagged activity payload with normalized event rows (`id`, `timestamp`, `event_id`, `detail`)
  - reset paths in rollback/trust-audit reset workflows now clear activity trail to avoid stale carry-over
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/213_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_controls.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_controls.py`

M17.79 outcome (2026-02-28):

- dry-run handoff hydrate confirm activity replay parser added:
  - strict parser now validates imported confirm-activity bundle kind/schema and required `entries` array
  - parser guidance now surfaces actionable hints for kind/schema/entries failures
- activity replay preview/replay controls added:
  - activity import preview now summarizes kind/schema, event count, latest event, and exported timestamp
  - replay action now hydrates live confirm-activity trail from imported bundle with explicit status paths (`empty/error/invalid/replayed`)
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/214_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay.py`

M17.80 outcome (2026-02-28):

- dry-run handoff hydrate confirm activity replay safety gate added:
  - replay flow now detects replacement risk when imported activity differs from existing trail and requires explicit confirm before overwrite
  - replay action now blocks with explicit status until replacement confirm is armed when risk exists
- replay safety hint/confirm controls added:
  - replay safety hint line now summarizes replacement-risk state near activity replay import controls
  - replay confirm checkbox auto-clears when replacement-risk condition is removed
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/215_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_gate.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_gate.py`

M17.81 outcome (2026-02-28):

- dry-run handoff hydrate confirm activity replay auto-disarm added:
  - replay replace-confirm now arms bounded timer state (`20s`) and auto-disarms when the replacement-confirm window expires
  - replay success/reset/cutover/fallback flows now clear replay timer state to avoid stale confirm carry-over
- replay countdown/operator hint surfaces added:
  - replay countdown hint now reflects parse/confirm states and remaining arm window (`not armed`, `armed`, `auto-disarm soon`)
  - arm/disarm/auto-disarm statuses now provide explicit re-check guidance for destructive replay overwrite
- implementation files:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`
  - `/home/seongcheoljeong/workspace/myproject/docs/216_web_e2e_graph_audit_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_auto_disarm.md`
  - `/home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_auto_disarm.py`
