# Graph Lab 버튼 시나리오 가이드

## 목적

이 문서는 Graph Lab 버튼을 `화면`이 아니라 `하려는 일` 기준으로 설명합니다.

다음 상황에서 이 문서를 사용하면 됩니다.

- 버튼이 너무 많아서 무엇부터 눌러야 할지 모르겠을 때
- 특정 목적에 맞는 짧은 클릭 순서가 필요할 때
- 전체 UX manual보다 더 바로 쓰는 버튼 설명이 필요할 때

전체 화면 설명은 [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)을 사용하면 됩니다.

run 또는 compare 흐름이 실패했다면 [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md)를 보십시오.

## 화면 참고

전체 화면:

![Graph Lab 전체 화면](reports/graph_lab_playwright_snapshots/latest/page_full.png)

Decision 영역:

![Decision Pane](reports/graph_lab_playwright_snapshots/latest/decision_pane.png)

Artifact 영역:

![Artifact Inspector](reports/graph_lab_playwright_snapshots/latest/artifact_inspector.png)

오른쪽 패널만 빠르게 읽고 싶으면 [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)를 보면 됩니다.

## 시나리오 1: canvas에 graph만 먼저 보고 싶다

언제:

- canvas가 비어 있고 known-good template를 보고 싶을 때

위치:

- 왼쪽 패널

버튼:

1. `Refresh Templates`
   - backend에서 template 목록을 다시 읽음
2. `Load #1`
   - 첫 번째 template를 canvas에 로드

기대 결과:

- canvas에 4개 node가 보임
  - `SceneSource`
  - `Propagation`
  - `SynthFMCW`
  - `RadarMap`

## 시나리오 2: backend 실행 전에 graph가 유효한지 확인하고 싶다

위치:

- 왼쪽 패널

버튼:

1. `Load #1`
2. `Validate Graph Contract`

기대 결과:

- 오른쪽 `Validation Result`
- `valid: true`
- node/edge count 표시

## 시나리오 3: 가장 단순한 성공 run을 하고 싶다

언제:

- frontend/backend sanity check를 처음 할 때

버튼과 필드:

1. `Load #1`
2. `Low Fidelity: RadarSimPy + FFD`
3. 확인:
   - `Runtime Backend = radarsimpy_rt`
4. `Run Graph (API)`

기대 결과:

- 상단 상태에 `graph run completed`
- 오른쪽 `Graph Run Result`
- `status: completed`
- artifact path 표시

## 시나리오 4: 왜 run이 실패했는지 알고 싶다

읽는 위치:

- 상단 상태 바
- 오른쪽 `Graph Run Result`
- 왼쪽 `Runtime Diagnostics`

관련 버튼:

| 버튼 | 언제 쓰는가 |
| --- | --- |
| `Retry Last Run` | 설정은 그대로고 한 번 더 실행할 때 |
| `Poll Last Run` | async 상태만 다시 읽고 싶을 때 |
| `Cancel Last Run` | 긴 run을 중단할 때 |

자주 보는 실패 의미:

| 보이는 메시지 | 의미 | 다음 조치 |
| --- | --- | --- |
| `required runtime modules unavailable` | backend module이 없음 | runtime 설치 또는 노출 |
| license 관련 오류 | runtime access가 막힘 | `License Tier`, `License File` 확인 |
| validation 문제 | graph contract가 맞지 않음 | `Validate Graph Contract` 먼저 실행 |
| provider/path 오류 | backend 입력이 미완성 | advanced runtime 입력 보완 |

## 시나리오 5: low fidelity와 high fidelity를 비교하고 싶다

위치:

- 왼쪽 runtime preset
- 오른쪽 `Decision Pane`

버튼:

1. `Load #1`
2. `Low Fidelity: RadarSimPy + FFD`
3. `Run Graph (API)`
4. `Use Current as Compare`
5. 다음 중 하나 선택
   - `High Fidelity: PO-SBR`
   - `High Fidelity: Sionna-style RT`
6. `Run Graph (API)` 다시 실행

그 다음 읽을 것:

- `Track Compare Workflow`
- `Preset Pair Compare`
- `Artifact Inspector`

## 시나리오 6: 가장 빠르게 auto compare를 만들고 싶다

위치:

- 오른쪽 `Decision Pane`

버튼:

1. 왼쪽에서 target runtime 설정
2. `Run Low -> Current Compare`

기대 결과:

- low baseline 자동 생성
- current config 자동 실행
- compare state 채워짐

## 시나리오 7: preset 대 preset으로 비교하고 싶다

위치:

- 오른쪽 `Preset Pair Compare`

버튼과 필드:

1. `baseline_preset` 선택
2. `target_preset` 선택
3. optional shortcut
   - `Low -> Current`
   - `Low -> Sionna`
   - `Low -> PO-SBR`
4. `Run Preset Pair Compare`

## 시나리오 8: 생성된 artifact를 보고 싶다

위치:

- 오른쪽 패널 아래쪽 `Artifact Inspector`

읽는 항목:

- `artifacts:`
- `node trace:`
- `visuals:`

주요 버튼:

| 버튼 | 의미 |
| --- | --- |
| `Collapse Inspector Evidence` | inspector 상세 접기 |
| `Expand Inspector Evidence` | inspector 상세 펼치기 |
| `Reset Inspector Layout` | inspector layout 초기화 |
| `Apply Recommended Audit Action` | audit cleanup 적용 |

## 시나리오 9: decision을 내리고 export하고 싶다

위치:

- 오른쪽 `Decision Pane`

버튼:

1. `Policy Gate`
2. `Run Session`
3. `Export Gate`
4. `Export Session`
5. `Export Brief`

## 시나리오 10: 예전에 만든 compare 결과를 다시 쓰고 싶다

위치:

- 오른쪽 `Compare Session History`
- 오른쪽 `Pinned Pair Quick Actions`

버튼:

| 버튼 | 의미 |
| --- | --- |
| `Use Latest History Pair` | 최신 replayable pair를 selector에 복원 |
| `Run Latest History Pair` | 최신 replayable pair 재실행 |
| `Use Selected History Pair` | 선택된 pair를 selector에 복원 |
| `Run Selected History Pair` | 선택된 pair 재실행 |
| `Save Selected Label` | 선택 pair 이름 저장 |
| `Pin Selected History Pair` | 선택 pair pin |
| `Delete Selected History Pair` | 선택 pair 삭제 |
| `Export History` | compare-history bundle export |
| `Import History` | compare-history bundle import |
| `Clear All History` | retained compare-history state 삭제 |

## 빠른 선택 표

| 하고 싶은 일 | 이동할 곳 | 가장 먼저 누를 버튼 |
| --- | --- | --- |
| graph 보기 | 왼쪽 `Template` | `Load #1` |
| graph 검증 | 왼쪽 패널 | `Validate Graph Contract` |
| backend 실행 | 왼쪽 runtime + run 영역 | `Low Fidelity: RadarSimPy + FFD` |
| 실패 run 재시도 | 왼쪽 run 영역 | `Retry Last Run` |
| 두 track 비교 | 오른쪽 `Decision Pane` | `Use Current as Compare` |
| auto compare 생성 | 오른쪽 `Decision Pane` | `Run Low -> Current Compare` |
| 파일/evidence 확인 | 오른쪽 아래 | `Artifact Inspector` |
| decision 실행 | 오른쪽 `Decision Pane` | `Policy Gate` |
| 전달용 brief export | 오른쪽 `Decision Pane` | `Export Brief` |

## 관련 문서

- [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)
- [Graph Lab UX Manual](300_graph_lab_ux_manual.md)
- [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Generated Reports Index](reports/README.md)
