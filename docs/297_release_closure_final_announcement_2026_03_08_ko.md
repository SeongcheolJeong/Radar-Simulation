# Release Closure Final Announcement

- 일자: 2026년 3월 8일
- 대상: 내부 release stakeholder, validator, operator handoff 수신자
- snapshot: [Release-Candidate Snapshot (Korean)](292_release_candidate_snapshot_2026_03_08_ko.md)
- one-page handoff: [Release Closure Handoff (Korean)](295_release_closure_handoff_2026_03_08_ko.md)

## 최종 공지 문안

```text
[Release Closure] 기본 Release-Candidate Cut Green (2026-03-08)

현재 기본 release-candidate cut은 green이며 handoff 가능한 상태입니다.

현재 기본 필수 체크:
1) FE-1 Graph Lab browser/operator flow
2) FE-2 frontend runtime payload -> provider info contract
3) RS-1 trial RadarSimPy layered parity
4) HF-2 PO-SBR parity/readiness path
5) RS-2 paid RadarSimPy production closure

현재 상태:
- canonical subset: pass=true
- PO-SBR parity: pass=true
- paid production gate: ready
- paid readiness checkpoint: ready
- Graph Lab Playwright/operator flow: current

HF-1 규칙:
- HF-1은 현재 기본값에서 optional
- Sionna-style RT가 실제 release story에 포함될 때만 추가

handoff bundle:
1) docs/295_release_closure_handoff_2026_03_08_ko.md
2) docs/292_release_candidate_snapshot_2026_03_08_ko.md
3) docs/reports/README.md
4) docs/reports/canonical_release_candidate_subset_latest.json
```

## 연결된 Evidence

- [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
- [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)
- [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
- [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
- [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)

## 이 문안을 그대로 보내면 안 되는 경우

아래 중 하나라도 해당하면 이 문안을 그대로 보내면 안 됩니다.

- canonical subset이 더 이상 `pass=true`가 아님
- paid production gate 또는 readiness checkpoint가 `ready`가 아님
- PO-SBR parity가 `pass=true`가 아님
- 이번 release story에서 `HF-1`이 required로 바뀜
