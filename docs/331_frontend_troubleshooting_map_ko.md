# Frontend 트러블슈팅 맵

## 목적

이 페이지는 frontend 흐름이 이상해 보이거나, blocked 상태이거나, stale해 보이거나, 실패했을 때 어느 트러블슈팅 문서부터 열어야 하는지 가장 짧게 안내하는 문서입니다.

`Graph Lab`과 `classic dashboard` 양쪽을 한 장에서 다룹니다.

## 먼저 UI를 구분하기

| 문제가 있는 UI | 먼저 열 문서 | 그 다음 문서 |
| --- | --- | --- |
| `Graph Lab` | [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md) | [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md) |
| `classic dashboard` | [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md) | [Classic Dashboard 실사용 체크리스트](311_classic_dashboard_live_checklist_ko.md) |
| 어느 UI부터 봐야 할지 모르겠다 | [Frontend 문서 맵](329_frontend_doc_map_ko.md) | 선택한 UI의 failure guide |

## 증상 기준으로 시작하기

| 보이는 증상 | 먼저 열 문서 | 그 다음 확인 |
| --- | --- | --- |
| Graph Lab `Run Graph (API)` 실패 | [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md) | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) |
| Graph Lab compare/gate/export 흐름 blocked | [Decision Pane 빠른 읽기 가이드](327_graph_lab_decision_pane_quick_guide_ko.md) | [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md) |
| Graph Lab artifact가 없거나 이상해 보임 | [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md) | [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md) |
| classic dashboard run이 stale하거나 비어 보임 | [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md) | [Frontend Dashboard Usage](116_frontend_dashboard_usage.md) |
| classic dashboard status line이 이해되지 않음 | [Classic Dashboard 상태 필드 가이드](319_classic_dashboard_status_field_guide_ko.md) | [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md) |
| classic dashboard result panel은 채워졌는데 신뢰가 안 감 | [Classic Dashboard 결과/증거 빠른 읽기 가이드](315_classic_dashboard_result_evidence_quick_guide_ko.md) | [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md) |
| high-fidelity path 선택 자체가 문제일 수 있음 | [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json) | [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md) |

## 가장 빠른 진단 규칙

다음 규칙으로 보면 됩니다.

1. 먼저 UI를 구분한다
2. 해당 UI의 failure guide를 먼저 읽는다
3. 그 다음 같은 UI의 shortest checklist를 본다
4. 그 후에 field-level 또는 panel-level guide를 연다

이 순서를 지키면 launch 문제, compare 상태 문제, evidence 읽기 문제를 섞지 않게 됩니다.

## UI별 고정 진단 순서

### Graph Lab

1. [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md)
2. [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md)
3. [Decision Pane 빠른 읽기 가이드](327_graph_lab_decision_pane_quick_guide_ko.md)
4. [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)
5. high-fidelity path 선택 문제가 의심되면 [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

### Classic Dashboard

1. [Classic Dashboard 실패 읽기 가이드](317_classic_dashboard_failure_reading_guide_ko.md)
2. [Classic Dashboard 실사용 체크리스트](311_classic_dashboard_live_checklist_ko.md)
3. [Classic Dashboard 상태 필드 가이드](319_classic_dashboard_status_field_guide_ko.md)
4. [Classic Dashboard 결과/증거 빠른 읽기 가이드](315_classic_dashboard_result_evidence_quick_guide_ko.md)

## 처음부터 이렇게 보지 말 것

다음부터 시작하지 마십시오.

- screenshot만 보기
- export path만 보기
- artifact 부재만 보기
- policy verdict만 보기

항상 active UI의 failure guide부터 시작하는 것이 맞습니다.

## 관련 문서
- [Frontend 문서 체인 Freeze Note](337_frontend_doc_chain_freeze_note_2026_03_08_ko.md)

- [Frontend 문서 맵](329_frontend_doc_map_ko.md)
- [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
- [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md)
- [Documentation Index](README.md)
- [Generated Reports Index](reports/README.md)
