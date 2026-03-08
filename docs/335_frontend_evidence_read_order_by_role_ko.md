# 역할별 Frontend Evidence 읽기 순서

## 목적

이 문서는 frontend evidence가 필요하다는 것은 알지만, 자신의 역할 기준으로 어떤 report를 어떤 순서로 먼저 열어야 하는지 가장 짧게 정리한 문서입니다.

이 문서는 UI 기능 설명 문서가 아닙니다. manual을 열기 전에 어떤 evidence 파일부터 봐야 하는지 정리합니다.

## 역할별 시작점

| 역할 | 먼저 열 것 | 그 다음 열 것 |
| --- | --- | --- |
| `Graph Lab`을 쓰는 frontend operator | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` |
| `classic dashboard`를 쓰는 demo/presentation 사용자 | `docs/reports/frontend_quickstart_v1.json` | `docs/reports/classic_dashboard_snapshots/latest/` |
| UI 변경을 검증하는 frontend developer | [Frontend Evidence 맵](333_frontend_evidence_map_ko.md) | 아래 역할별 세부 순서 |
| 현재 frontend 건강 상태를 점검하는 validator | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json` |

## 역할별 읽는 순서

### Frontend Operator

다음 순서로 봅니다.

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`
3. `docs/reports/graph_lab_playwright_snapshots/latest/`
4. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
5. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

이 순서는 다음 질문에 답할 때 맞습니다.

- 현재 browser flow가 통과했는가
- 현재 exported decision이 무엇을 말하는가
- 현재 UI가 어떻게 보였는가
- 지금 interactive high-fidelity path가 무엇인가
- frontend/runtime contract가 drift했는가

이 흐름이 이상하면 다음으로 갑니다.

- [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)
- [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md)

### Demo 또는 Presentation 사용자

다음 순서로 봅니다.

1. `docs/reports/frontend_quickstart_v1.json`
2. `docs/reports/classic_dashboard_snapshots/latest/dashboard_full.png`
3. `docs/reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png`
4. `docs/reports/classic_dashboard_snapshots/latest/dashboard_main_annotated.png`

이 순서는 다음 질문에 맞습니다.

- 가벼운 frontend 경로가 아직 정상적으로 뜨는가
- 다른 사람에게 실제로 어떤 화면이 보이는가
- 화면에서 어떤 결과 구역이 중요한가

이 흐름이 이상하면 다음으로 갑니다.

- [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)
- [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md)

### Frontend Developer

먼저 바꾼 surface를 고릅니다.

`Graph Lab`을 바꿨다면:

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_playwright_snapshots/latest/`
3. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
4. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

`classic dashboard`를 바꿨다면:

1. `docs/reports/frontend_quickstart_v1.json`
2. `docs/reports/classic_dashboard_snapshots/latest/`

shared frontend/backend runtime wiring을 바꿨다면:

1. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`
2. `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json`
3. `docs/reports/graph_lab_playwright_e2e_latest.json`

그 다음 문서:

- [Generated Reports Index](reports/README.md)
- [Frontend Evidence 맵](333_frontend_evidence_map_ko.md)

### Frontend Validator

다음 순서로 봅니다.

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
3. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`
4. `docs/reports/frontend_quickstart_v1.json`
5. `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`

이 순서는 다음 질문에 맞습니다.

- 현재 frontend flow가 green인가
- 현재 high-fidelity release story가 아직 유효한가
- runtime payload/provider contract가 여전히 맞는가
- lightweight dashboard path가 여전히 usable한가

어느 하나라도 깨지면 다음으로 갑니다.

- [Generated Reports Index](reports/README.md)
- [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)

## 가장 짧은 규칙

다음 규칙을 씁니다.

- 먼저 `_latest.json`
- 그 다음 `latest/` snapshot 디렉터리나 exported brief
- explanation이 필요할 때만 UX manual

## 관련 문서

- [Frontend Evidence 맵](333_frontend_evidence_map_ko.md)
- [Frontend 문서 맵](329_frontend_doc_map_ko.md)
- [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)
- [Generated Reports Index](reports/README.md)
