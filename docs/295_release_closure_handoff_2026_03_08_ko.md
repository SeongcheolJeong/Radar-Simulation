# Release Closure Handoff

- 일자: 2026년 3월 8일
- 상태: 현재 기본 release-candidate closure는 green입니다
- 범위: frontend/operator workflow, trial RadarSimPy parity, PO-SBR high-fidelity closure, paid RadarSimPy production closure
- 상세 snapshot: [Release-Candidate Snapshot (Korean)](292_release_candidate_snapshot_2026_03_08_ko.md)
- HF-1 규칙: [HF-1 Release Requirement Decision](293_hf1_release_requirement_decision_2026_03_08.md)
- 바로 사용할 handoff 템플릿: [Release Announcement Templates](282_release_announcement_templates_2026_03_05.md)
- final announcement: [Release Closure Final Announcement (Korean)](297_release_closure_final_announcement_2026_03_08_ko.md)
- freeze 규칙: [Release Closure Freeze Note (Korean)](299_release_closure_freeze_note_2026_03_08_ko.md)

## 현재 컷의 기본 필수 체크

아래가 모두 green일 때만 현재 컷을 release-ready로 봅니다.

1. `FE-1` Graph Lab browser/operator flow
2. `FE-2` frontend runtime payload -> provider info contract
3. `RS-1` trial RadarSimPy layered parity
4. `HF-2` PO-SBR parity/readiness path
5. `RS-2` paid RadarSimPy production closure

## 현재 컷에서 optional인 체크

- `HF-1` Sionna-style RT parity는 현재 기본 컷에서는 optional입니다.
- Sionna-style RT가 실제 release story에 포함될 때만 required로 올립니다.

## 현재 Green Evidence

- [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
  - `pass=true`
- [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)
  - browser/operator path current
- [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
  - `pass=true`
- [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
  - `production_gate_status=ready`
- [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)
  - `overall_status=ready`

## Handoff Bundle

handoff 시에는 아래를 같이 보냅니다.

1. 이 one-page handoff 문서
2. [Release-Candidate Snapshot (Korean)](292_release_candidate_snapshot_2026_03_08_ko.md)
3. [Generated Reports Index](reports/README.md)
4. [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)

이 조합이면 짧은 결정 요약, 상세 설명, evidence routing, machine-readable status를 같이 전달할 수 있습니다.

## 갱신 명령

기본 closure evidence를 handoff 전에 갱신해야 하면 아래를 실행합니다.

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

## Handoff 전에 재검토해야 하는 조건

- canonical subset이 `pass=true`가 아님
- paid RadarSimPy production gate 또는 readiness checkpoint가 `ready`가 아님
- PO-SBR parity가 `pass=true`가 아님
- frontend Playwright/operator evidence가 stale 또는 fail 상태
- 이번 release story에 Sionna-style RT가 포함되어 `HF-1` 재판단이 필요함
