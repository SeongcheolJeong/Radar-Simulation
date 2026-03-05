# Release Announcement Templates (2026-03-05)

## Source Docs

- Detailed release notes: `docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md`
- One-page summary (EN): `docs/280_release_one_pager_radarsimpy_2026_03_05.md`
- One-page summary (KO): `docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md`

## Evidence Reports

- Production gate (ready): `docs/reports/radarsimpy_production_release_gate_paid_6m.json`
- Readiness checkpoint (ready): `docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json`
- Simulator parity (pass): `docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json`
- Graph Lab Playwright E2E (pass): `docs/reports/graph_lab_playwright_e2e_latest.json`

## Slack Template (EN)

```text
[Release Update] RadarSimPy Runtime + Frontend Multiplexing (2026-03-05)

Key updates:
- Runtime path now supports multiplexing-aware execution: tdm / bpm / custom
- Graph Lab frontend now exposes BPM/custom controls + presets (TDM, BPM 2TX, Custom)
- Dedicated LGIT output adapter integrated (lgit_customized_output.npz)
- Paid 6-month production validation flow is automated via CI template

Validation status:
- Production gate: ready
- Readiness checkpoint: ready
- Simulator parity: pass
- Graph Lab Playwright E2E: pass

Docs:
- One-pager (EN): docs/280_release_one_pager_radarsimpy_2026_03_05.md
- One-pager (KO): docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md
- Full notes: docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md
```

## Slack Template (KO)

```text
[릴리즈 업데이트] RadarSimPy 런타임 + 프론트엔드 멀티플렉싱 (2026-03-05)

주요 변경:
- 런타임이 멀티플렉싱 인지 실행 지원: tdm / bpm / custom
- Graph Lab 프론트엔드에 BPM/custom 제어 및 프리셋(TDM, BPM 2TX, Custom) 추가
- LGIT 전용 출력 어댑터 통합 (lgit_customized_output.npz)
- 유료 6개월 프로덕션 검증 플로우를 CI 템플릿으로 자동화

검증 상태:
- Production gate: ready
- Readiness checkpoint: ready
- Simulator parity: pass
- Graph Lab Playwright E2E: pass

문서:
- 1페이지 요약(EN): docs/280_release_one_pager_radarsimpy_2026_03_05.md
- 1페이지 요약(KO): docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md
- 상세 노트: docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md
```

## Email Template (EN)

Subject:
`[Release] RadarSimPy Multiplexing Runtime + Frontend Controls (2026-03-05)`

Body:

```text
Hello team,

We completed the March 5 release for RadarSimPy runtime/frontend integration.

Highlights:
1) Runtime multiplexing generalization (tdm, bpm, custom)
2) Graph Lab frontend controls + input validation for BPM/custom flows
3) LGIT adapter integration (lgit_customized_output.npz)
4) Paid production validation CI template

Verification:
- production gate: ready
- readiness checkpoint: ready
- simulator parity: pass
- frontend e2e: pass

Documentation:
- Full notes: docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md
- One-page EN: docs/280_release_one_pager_radarsimpy_2026_03_05.md
- One-page KO: docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md

Best regards,
Radar Simulation Team
```

## Email Template (KO)

제목:
`[릴리즈] RadarSimPy 멀티플렉싱 런타임 + 프론트엔드 제어 (2026-03-05)`

본문:

```text
안녕하세요.

3월 5일자 RadarSimPy 런타임/프론트엔드 통합 릴리즈를 완료했습니다.

핵심 변경:
1) 런타임 멀티플렉싱 일반화 (tdm, bpm, custom)
2) Graph Lab 프론트엔드 BPM/custom 제어 및 입력 검증 강화
3) LGIT 어댑터 통합 (lgit_customized_output.npz)
4) 유료 프로덕션 검증 CI 템플릿 추가

검증 결과:
- production gate: ready
- readiness checkpoint: ready
- simulator parity: pass
- frontend e2e: pass

문서:
- 상세 노트: docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md
- 1페이지 요약(EN): docs/280_release_one_pager_radarsimpy_2026_03_05.md
- 1페이지 요약(KO): docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md

감사합니다.
Radar Simulation Team
```

