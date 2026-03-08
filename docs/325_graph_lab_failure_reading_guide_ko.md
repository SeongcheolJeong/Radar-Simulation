# Graph Lab 실패 읽기 가이드

## 목적

Graph Lab을 열어 둔 상태에서 run, compare, gate, export 흐름이 실패했거나 blocked처럼 보일 때 이 문서를 사용합니다.

다음 액션 뒤에 봅니다.

- `Run Graph (API)`
- `Retry Last Run`
- `Run Low -> Current Compare`
- `Run Preset Pair Compare`
- `Policy Gate`
- `Run Session`
- `Export Brief`

전체 화면 설명이 필요하면 [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)을 보십시오.

가장 짧은 클릭 순서가 먼저 필요하면 [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md)를 보십시오.

## 화면 기준

번호가 들어간 전체 화면:

![Graph Lab annotated](reports/graph_lab_playwright_snapshots/latest/page_full_annotated.png)

번호가 들어간 Decision Pane:

![Decision Pane annotated](reports/graph_lab_playwright_snapshots/latest/decision_pane_annotated.png)

번호가 들어간 Artifact Inspector:

![Artifact Inspector annotated](reports/graph_lab_playwright_snapshots/latest/artifact_inspector_annotated.png)

run failed 예시:

![Graph Lab run failed example](reports/graph_lab_playwright_snapshots/latest/graph_lab_run_failed_example.png)

## 실패는 이 순서로 읽으십시오

1. 상단 status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. `Decision Pane`
5. `Artifact Inspector`

artifact가 없다는 사실부터 시작하지 마십시오. 먼저 run state와 runtime diagnostics를 읽으십시오.

## 실패 사례 1: `Run Graph (API)`가 실패했다

이 순서로 읽습니다.

1. 상단 status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. 그 다음 왼쪽 패널의 runtime preset/backend/license field

주요 원인:

- required runtime module이 없음
- license tier 또는 `.lic` path가 잘못됨
- provider 전용 runtime input이 비어 있음
- 선택한 backend에 비해 graph contract가 충분하지 않음

가장 빠른 다음 액션:

- `Validate Graph Contract` 재실행
- runtime preset/backend/provider/license field 재확인
- 설정 자체가 맞을 때만 `Retry Last Run` 사용

## 실패 사례 2: Compare 흐름이 blocked이거나 비어 있다

이 순서로 읽습니다.

1. `Decision Pane`
2. `Track Compare Workflow`
3. `Preset Pair Compare`
4. `Graph Run Result`
5. `Artifact Inspector`

주요 원인:

- 유효한 compare reference가 로드되지 않음
- baseline run이 completed되지 않음
- low-fidelity baseline 생성이 실패함
- compare state가 current run과 stale함

가장 빠른 다음 액션:

- completed run 뒤에 `Use Current as Compare`
- 또는 `Run Low -> Current Compare` 재실행
- current와 compare artifact가 둘 다 존재하는지 확인

## 실패 사례 3: `Policy Gate`가 쓸 만한 결정을 만들지 못한다

이 순서로 읽습니다.

1. `Decision Pane`
2. compare assessment summary
3. selected pair forecast
4. `Artifact Inspector`

주요 원인:

- compare evidence가 불완전함
- current-vs-compare pair가 의도한 pair가 아님
- pair는 만들어졌지만 의미 있는 compare evidence가 로드되지 않음

가장 빠른 다음 액션:

- selected compare pair부터 다시 확인
- 필요하면 pair 재생성
- 그 다음에만 `Policy Gate` 재실행

## 실패 사례 4: Export 또는 Session 흐름이 비어 있다

이 순서로 읽습니다.

1. `Decision Pane`
2. session/export 영역
3. `Graph Run Result`
4. `Artifact Inspector`

주요 원인:

- session/export 전에 유효한 run pair가 없었음
- compare evidence가 생기기 전에 gate/session/export를 시도함
- compare history selection이 stale함

가장 빠른 다음 액션:

- 유효한 current-vs-compare pair 재구성
- `Policy Gate` 재실행
- 그 다음 `Run Session` 또는 `Export Brief` 재실행

## 실패 사례 5: Run은 녹색인데 evidence가 이상해 보인다

이 순서로 읽습니다.

1. `Runtime Diagnostics`
2. `Artifact Inspector`
3. `Decision Pane`

주요 원인:

- backend/provider state가 의도와 다름
- current artifact와 compare artifact가 서로 다른 context에서 왔음
- baseline과 target 사이에 runtime path가 바뀜

가장 빠른 다음 액션:

- planned vs observed runtime diagnostics 비교
- inspector에서 current/compare artifact row 확인
- runtime path가 예상과 다르면 pair 재생성

## 빠른 판단표

| 무엇이 실패했나 | 먼저 읽을 곳 | 보통 잘못된 것 | 다음 액션 |
| --- | --- | --- | --- |
| `Run Graph (API)` | `Graph Run Result` | runtime/license/provider/backend 문제 | contract 검증 후 재실행 |
| low-vs-high compare | `Decision Pane` | compare reference 누락 또는 low path blocked | compare pair 재생성 |
| `Policy Gate` | compare assessment | 불완전하거나 잘못된 pair | compare 후 gate 재실행 |
| `Run Session` / `Export Brief` | session/export 영역 | 아직 유효한 compare evidence 없음 | pair 생성, gate 후 export |
| run은 성공했는데 evidence 이상 | `Runtime Diagnostics` | wrong backend/provider/runtime source | runtime 정렬 후 재실행 |

## 관련 문서

- [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)
- [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)
- [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)
- [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md)
- [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
