# Frontend Evidence 맵

## 목적

이 페이지는 frontend를 이미 실행했고, 이제 어떤 report와 snapshot부터 열어야 하는지 가장 짧게 알고 싶을 때 쓰는 문서입니다.

`Graph Lab`, `classic dashboard`, timing evidence, exported brief를 한 장에서 정리합니다.

## 먼저 UI를 구분하기

| 증거를 보고 싶은 대상 | 먼저 열 파일/문서 | 그 다음 열 것 |
| --- | --- | --- |
| `Graph Lab` 브라우저 흐름과 현재 UI 상태 | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_playwright_snapshots/latest/` |
| `Graph Lab` export 결과 | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` | `docs/reports/graph_lab_playwright_e2e_latest.json` |
| `Graph Lab`의 interactive high-fidelity path 판단 | `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json` | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) |
| `classic dashboard` quick demo/API path | `docs/reports/frontend_quickstart_v1.json` | [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md) |
| frontend runtime payload/provider contract | `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json` | 유료 runtime이 중요하면 `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json` |

## 질문 기준으로 고르기

| 알고 싶은 것 | 먼저 열 것 | 그 다음 열 것 |
| --- | --- | --- |
| 현재 Graph Lab browser E2E가 통과하는가 | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` |
| 현재 Graph Lab 화면이 어떻게 보였는가 | `docs/reports/graph_lab_playwright_snapshots/latest/page_full.png` | `docs/reports/graph_lab_playwright_snapshots/latest/page_full_annotated.png` |
| 현재 decision/export 결과가 어떻게 생겼는가 | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` | `docs/reports/graph_lab_playwright_snapshots/latest/decision_pane.png` |
| `Sionna-style RT`와 `PO-SBR` 중 무엇이 interactive high-fidelity path인가 | `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json` | `docs/reports/scene_backend_parity_sionna_rt_latest.json`, `docs/reports/scene_backend_parity_po_sbr_rt_latest.json` |
| classic dashboard quick path가 아직 정상인가 | `docs/reports/frontend_quickstart_v1.json` | [Classic Dashboard 결과/증거 빠른 읽기 가이드](315_classic_dashboard_result_evidence_quick_guide_ko.md) |
| frontend/backend runtime payload wiring이 drift했는가 | `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json` | `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json` |

## UI별 읽는 순서

### Graph Lab

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`
3. `docs/reports/graph_lab_playwright_snapshots/latest/`
4. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
5. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

현재 Graph Lab 상태, exported brief, screenshot, high-fidelity timing 판단, contract evidence를 보고 싶을 때 이 순서로 보면 됩니다.

### Classic Dashboard

1. `docs/reports/frontend_quickstart_v1.json`
2. [Classic Dashboard 결과/증거 빠른 읽기 가이드](315_classic_dashboard_result_evidence_quick_guide_ko.md)
3. [Classic Dashboard 상태 필드 가이드](319_classic_dashboard_status_field_guide_ko.md)

가벼운 dashboard summary path만 보면 될 때 이 순서가 맞습니다.

## 가장 짧은 evidence 규칙

다음 규칙으로 보면 됩니다.

- current stable summary가 있으면 먼저 `_latest.json`
- 그 다음 시각 evidence가 필요하면 `latest/` snapshot 디렉터리
- explanation이 필요할 때만 UI manual로 이동

## 관련 문서

- [Frontend 문서 맵](329_frontend_doc_map_ko.md)
- [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)
- [Generated Reports Index](reports/README.md)
- [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
- [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md)
