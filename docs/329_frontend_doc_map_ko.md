# Frontend 문서 맵

## 목적

이 페이지는 frontend 문서가 필요하지만, `Graph Lab`부터 봐야 하는지 `classic dashboard`부터 봐야 하는지 아직 모를 때 사용하는 상위 routing map입니다.

## 먼저 UI를 고르기

| 원하는 것 | 먼저 볼 문서 | 그 다음 문서 |
| --- | --- | --- |
| runtime 선택, compare, artifact inspection, decision export가 있는 main operator workbench | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) | [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md) |
| 더 가볍고 단순한 demo/presentation dashboard | [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md) | [Classic Dashboard UX 사용 매뉴얼](309_classic_dashboard_ux_manual_ko.md) |
| 일단 frontend를 가장 빨리 띄운 뒤에 UI를 고르고 싶다 | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) | 위 두 문서 맵 중 하나 |
| 두 UI 차이를 한 장에서 먼저 보고 싶다 | 이 페이지 | 선택한 UI의 문서 맵 |

## 하고 싶은 일 기준으로 고르기

| 하고 싶은 일 | 먼저 볼 문서 | 그 다음 문서 |
| --- | --- | --- |
| Graph Lab을 로컬에서 실행 | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) | [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md) |
| classic dashboard를 로컬에서 실행 | [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md) | [Classic Dashboard 실사용 체크리스트](311_classic_dashboard_live_checklist_ko.md) |
| low fidelity vs high fidelity 비교 | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) | [Decision Pane 빠른 읽기 가이드](327_graph_lab_decision_pane_quick_guide_ko.md) |
| generated artifact와 compare evidence 읽기 | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) | [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md) |
| 다른 사람에게 더 단순한 dashboard view를 보여주기 | [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md) | [Classic Dashboard UX 사용 매뉴얼](309_classic_dashboard_ux_manual_ko.md) |
| run 뒤에 dashboard result/status box 읽기 | [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md) | [Classic Dashboard 결과/증거 빠른 읽기 가이드](315_classic_dashboard_result_evidence_quick_guide_ko.md) |
| Graph Lab 실패 진단 | [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md) | [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md) |
| classic dashboard 실패 진단 | [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md) | [Classic Dashboard 실사용 체크리스트](311_classic_dashboard_live_checklist_ko.md) |
| 현재 interactive한 high-fidelity path 확인 | [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json) | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) |
| frontend 문제를 UI별 문서로 들어가기 전에 먼저 분기하고 싶다 | [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md) | 해당 UI의 failure guide |
| 현재 frontend evidence를 UI manual보다 먼저 보고 싶다 | [Frontend Evidence 맵](333_frontend_evidence_map_ko.md) | UI별 report/snapshot |

## 역할 기준으로 고르기

### Frontend Operator

다음 순서로 시작하면 됩니다.

1. [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
2. [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md)
3. [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)

실사용 흐름이 이미 실패한 상태라면 [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)부터 시작하면 됩니다.

runtime 선택, compare decision, handoff brief가 필요할 때 이 경로를 쓰면 됩니다.

### Demo / Presentation 사용자

다음 순서로 시작하면 됩니다.

1. [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md)
2. [Classic Dashboard 실사용 체크리스트](311_classic_dashboard_live_checklist_ko.md)
3. [Classic Dashboard 결과/증거 빠른 읽기 가이드](315_classic_dashboard_result_evidence_quick_guide_ko.md)

가장 짧은 viewer-oriented frontend 경로가 필요할 때 이 경로가 맞습니다.

### Frontend Developer

다음 순서로 시작하면 됩니다.

1. [Documentation Index](README.md)
2. [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
3. [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md)
4. [Generated Reports Index](reports/README.md)

어느 UI surface에 영향이 있는지 먼저 가른 뒤 validator를 고를 때 쓰면 됩니다.

## 가장 짧은 판단 규칙

다음 규칙으로 고르면 됩니다.

- runtime preset, compare history, artifact evidence, decision export가 필요하면 `Graph Lab`
- 더 가벼운 dashboard shell과 단순 review surface가 필요하면 `classic dashboard`
- 그래도 헷갈리면 기능 범위가 더 넓은 `Graph Lab` 문서 맵부터 열면 됩니다

## 관련 문서

- [Frontend Evidence 맵](333_frontend_evidence_map_ko.md)
- [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)
- [Documentation Index](README.md)
- [Generated Reports Index](reports/README.md)
- [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
- [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md)
