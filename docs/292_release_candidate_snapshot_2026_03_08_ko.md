# Release-Candidate Snapshot

- 일자: 2026년 3월 8일
- 범위: frontend/operator workflow, trial RadarSimPy parity, PO-SBR parity/readiness, paid RadarSimPy production closure
- 영문 snapshot: [Release-Candidate Snapshot](291_release_candidate_snapshot_2026_03_08.md)
- one-page handoff: [Release Closure Handoff (Korean)](295_release_closure_handoff_2026_03_08_ko.md)
- 영문 canonical pack: [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md)
- 국문 canonical pack: [정식 검증 시나리오 팩](290_canonical_validation_scenario_pack_ko.md)
- HF-1 결정 문서: [HF-1 Release Requirement Decision](293_hf1_release_requirement_decision_2026_03_08.md)

## 현재 결정

- default release-candidate subset:
  - `FE-1`
  - `FE-2`
  - `RS-1`
  - `HF-2`
  - `RS-2`
- `HF-1`은 기본값에서는 아직 optional입니다. 자세한 판단 근거는 [HF-1 Release Requirement Decision](293_hf1_release_requirement_decision_2026_03_08.md)를 기준으로 합니다.
- 다음 컷에서 Sionna-style RT 경로가 실제 release story에 포함될 때만 `HF-1`을 추가합니다.

이유:

- 현재 기본 closure path가 이미 end-to-end green입니다.
- 현재 operator/runtime 작업 기준으로는 `HF-2`가 더 우선순위가 높은 high-fidelity closure path입니다.
- `HF-1` stable evidence도 green이지만, 현재 기본 컷에 필수로 묶을 근거는 아직 없습니다.

## 현재 안정 상태

현재 release-candidate subset은 green입니다.

- canonical subset:
  - [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
  - `pass=true`
  - `step_count=8`
  - `pass_count=8`
- paid RadarSimPy production gate:
  - [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
  - `production_gate_status=ready`
- paid RadarSimPy readiness checkpoint:
  - [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)
  - `overall_status=ready`
- PO-SBR parity:
  - [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
  - `pass=true`
- Sionna-style parity:
  - [scene_backend_parity_sionna_rt_latest.json](reports/scene_backend_parity_sionna_rt_latest.json)
  - `pass=true`
- Graph Lab browser/operator flow:
  - [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)

## Stable Evidence Set

현재 release-candidate evidence bundle은 아래 세트를 기준으로 봅니다.

### Frontend / Operator

- [frontend_quickstart_v1.json](reports/frontend_quickstart_v1.json)
- [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)
- [graph_lab_playwright_snapshots/latest/decision_brief.md](/home/seongcheoljeong/workspace/myproject/docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md)
- [graph_lab_playwright_snapshots/latest/page_full.png](/home/seongcheoljeong/workspace/myproject/docs/reports/graph_lab_playwright_snapshots/latest/page_full.png)
- [frontend_runtime_payload_provider_info_optional_latest.json](reports/frontend_runtime_payload_provider_info_optional_latest.json)

### RadarSimPy Trial / Low Fidelity

- [radarsimpy_layered_parity_suite_trial_latest.json](reports/radarsimpy_layered_parity_suite_trial_latest.json)
- [radarsimpy_layered_parity_trial_latest.json](reports/radarsimpy_layered_parity_trial_latest.json)

### High Fidelity

- [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
- [scene_backend_parity_sionna_rt_latest.json](reports/scene_backend_parity_sionna_rt_latest.json)
- 최신 `po_sbr_post_change_gate_*.json`
- [po_sbr_progress_snapshot_release_candidate_latest.json](reports/po_sbr_progress_snapshot_release_candidate_latest.json)

### Paid RadarSimPy Production

- [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
- [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)
- [radarsimpy_simulator_reference_parity_paid_6m.json](reports/radarsimpy_simulator_reference_parity_paid_6m.json)
- [frontend_runtime_payload_provider_info_paid_6m.json](reports/frontend_runtime_payload_provider_info_paid_6m.json)

## 이 Snapshot 갱신 방법

실행:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

release story에 Sionna-style RT path도 포함된다면:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --with-sionna \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

## Pass 해석 규칙

아래 조건을 만족하면 healthy로 봅니다.

- canonical subset이 계속 `pass=true`
- paid RadarSimPy production gate가 계속 `ready`
- paid readiness checkpoint가 계속 `ready`
- PO-SBR parity가 계속 `pass=true`
- frontend Playwright/operator evidence가 최신 상태

위 조건 중 하나라도 red로 바뀌거나 stale이면 release-ready가 아니라고 봅니다.

## 남은 Release-Freeze 작업

1. 다음 컷에서 `HF-1`을 기본 필수로 올릴지 결정
2. validation을 열어주지 않는 workflow micro-feature 추가는 지양
3. ad-hoc report를 늘리지 말고 같은 stable evidence set만 계속 갱신

## 권장 Handoff 규칙

handoff 시에는 아래 3개를 같이 보냅니다.

1. [Release Closure Handoff (Korean)](295_release_closure_handoff_2026_03_08_ko.md)
2. 이 snapshot 문서
3. [Generated Reports Index](reports/README.md)
4. [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)

이 조합이면 설명, evidence routing, machine-readable status를 한 번에 전달할 수 있습니다.
