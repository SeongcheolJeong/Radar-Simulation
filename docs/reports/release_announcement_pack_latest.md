# Release Announcement Pack

- release_date: 2026-03-05
- overall_ready: True
- branch: main
- head_commit: d4c8497

## Status

- production_gate_ready: True
- readiness_ready: True
- parity_pass: True
- frontend_e2e_pass: True
- retention_audit_apply: True
- retention_audit_deleted_count: 89
- retention_audit_failed_delete_count: 0
- retention_audit_prunable_count: 89

## Slack EN

```text
[Release Update] RadarSimPy Runtime + Frontend Multiplexing (2026-03-05)

Key updates:
- Runtime path supports multiplexing-aware execution: tdm / bpm / custom
- Graph Lab frontend exposes BPM/custom controls + presets
- Dedicated LGIT output adapter integrated (lgit_customized_output.npz)
- Paid production validation flow available via CI template

Validation status:
- Production gate: ready
- Readiness checkpoint: ready
- Simulator parity: pass
- Graph Lab Playwright E2E: pass
- Report retention audit: apply=True deleted=89 failed=0

Commit: d4c8497
One-pager EN: docs/280_release_one_pager_radarsimpy_2026_03_05.md
One-pager KO: docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md
Details: docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md
```

## Slack KO

```text
[릴리즈 업데이트] RadarSimPy 런타임 + 프론트엔드 멀티플렉싱 (2026-03-05)

주요 변경:
- 런타임 멀티플렉싱 인지 실행 지원: tdm / bpm / custom
- Graph Lab BPM/custom 제어 및 프리셋 노출
- LGIT 전용 출력 어댑터 통합 (lgit_customized_output.npz)
- 유료 프로덕션 검증 플로우 CI 템플릿 제공

검증 상태:
- Production gate: ready
- Readiness checkpoint: ready
- Simulator parity: pass
- Graph Lab Playwright E2E: pass
- 리포트 보존 감사: apply=True deleted=89 failed=0

커밋: d4c8497
1페이지 요약(EN): docs/280_release_one_pager_radarsimpy_2026_03_05.md
1페이지 요약(KO): docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md
상세: docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md
```

## Email Subject EN

`[Release] RadarSimPy Runtime + Frontend Multiplexing (2026-03-05)`

## Email Subject KO

`[릴리즈] RadarSimPy 런타임 + 프론트엔드 멀티플렉싱 (2026-03-05)`
