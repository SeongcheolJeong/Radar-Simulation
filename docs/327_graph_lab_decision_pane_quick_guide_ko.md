# Decision Pane 빠른 읽기 가이드

## 목적

이 문서는 다음 상황에서 사용합니다.

- Graph Lab은 이미 열려 있고 오른쪽 `Decision Pane`만 빨리 읽고 싶을 때
- compare, gate, session, export 버튼이 한꺼번에 많아서 어디부터 봐야 할지 모를 때
- `Policy Gate`나 `Export Brief`를 누르기 전에 무엇을 확인해야 하는지 알고 싶을 때

전체 화면 흐름은 [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)을 보면 됩니다.

## 위치

`Decision Pane`은 오른쪽 패널에서 `Artifact Inspector` 위에 있습니다.

안 보이면:

1. `Load #1`
2. 최소 한 번 `Run Graph (API)` 실행
3. 오른쪽 패널을 스크롤해서 compare/gate 영역 찾기

예시:

![Decision Pane](reports/graph_lab_playwright_snapshots/latest/decision_pane.png)

번호 마커가 들어간 예시:

![Decision Pane annotated](reports/graph_lab_playwright_snapshots/latest/decision_pane_annotated.png)

## 읽는 순서

다음 순서로 읽으면 됩니다.

1. compare reference 상태
2. `Track Compare Workflow`
3. `Preset Pair Compare`
4. compare history와 quick action
5. `Policy Gate`
6. session/export 버튼
7. `Inspector State Mirror`

이 순서가 좋은 이유:

- compare pair가 정리되기 전에 export하는 실수를 줄여 줍니다
- inspector 상태와 실제 compare 상태를 섞지 않게 해 줍니다

## 각 영역 의미

### 1. Compare Reference State

현재 run에 compare 상대가 있는지 먼저 보는 영역입니다.

주요 신호:

- compare run이 로드되었는가
- current run이 compare로 고정되었는가
- compare가 clear되었는가

pane가 복잡해 보여도 여기부터 보면 됩니다.

### 2. `Track Compare Workflow`

현재 pair를 가장 빠르게 요약해 주는 영역입니다.

여기서 확인하는 질문:

- current track이 무엇인가
- compare track이 무엇인가
- 선택한 pair가 말이 되는가
- 다음 액션이 무엇인가

딱 한 줄 요약만 필요하면 여기부터 봅니다.

### 3. `Preset Pair Compare`

수동 전환 대신 재현 가능한 pair를 실행할 때 씁니다.

대표 사용:

- `Low -> Current`
- `Low -> Sionna`
- `Low -> PO-SBR`
- custom `baseline_preset -> target_preset`

정상 신호:

- forecast가 말이 된다
- pair runner가 blocked 없이 끝난다

### 4. Compare Session History

최소 한 번 compare를 만든 뒤부터 의미가 있습니다.

주요 용도:

- 예전 pair 재실행
- 중요한 pair pin
- saved pair 이름 변경
- retention 상태 확인
- compare history export/import

첫 run에서는 여기부터 볼 필요가 없습니다.

### 5. `Policy Gate`

current와 compare evidence가 둘 다 있을 때만 눌러야 합니다.

정상 신호:

- current run 완료
- compare run 완료
- compare assessment가 읽힌다

보통 비정상인 이유:

- compare reference가 없음
- low path가 blocked
- current run 실패 상태에서 gate를 시도함

### 6. Session And Export

결과를 기록하고 전달용으로 묶는 영역입니다.

대표 액션:

- `Run Session`
- `Export Session`
- `Export Gate`
- `Export Brief`

compare/gate 상태가 읽힌 뒤에만 쓰는 것이 맞습니다.

### 7. `Inspector State Mirror`

이것은 시뮬레이션 정답 자체가 아닙니다.

`Artifact Inspector`의 상태를 위에서 바로 제어/확인하는 영역입니다.

할 수 있는 것:

- inspector evidence 접기/펼치기
- inspector layout reset
- audit maintenance action 적용
- 아래로 스크롤하지 않고 audit/maintenance 상태 읽기

## 빠른 정상 확인법

`Policy Gate`나 `Export Brief`를 누르기 전에 아래 4개만 먼저 확인하면 됩니다.

1. `Graph Run Result`가 `status: completed`
2. compare reference가 기대대로 존재
3. `Track Compare Workflow`가 읽힌다
4. `Artifact Inspector`에 compare evidence가 있다

이 4개가 맞으면 decision path는 대체로 준비된 상태입니다.

## 자주 쓰는 시나리오

### 시나리오 A: 가장 빠른 low-vs-current compare

1. low fidelity 실행
2. `Use Current as Compare`
3. target runtime으로 전환
4. `Run Graph (API)` 다시 실행
5. 다음 순서로 읽기
   - compare reference 상태
   - `Track Compare Workflow`
   - compare assessment
6. 그 다음 `Policy Gate`

### 시나리오 B: 가장 빠른 자동 pair 생성

1. target runtime 설정
2. `Run Low -> Current Compare`
3. 다음 읽기
   - pair runner 결과
   - selected pair forecast
   - compare assessment

기대 결과:

- low baseline이 자동 생성됨
- target run이 자동 생성됨
- 수동 pin 없이 compare state가 채워짐

### 시나리오 C: handoff용 brief export

1. pair가 읽히는지 확인
2. 필요하면 `Policy Gate`
3. `Export Brief`
4. brief에 아래가 반영됐는지 확인
   - current vs compare 상태
   - compare assessment
   - inspector mirror 상태

brief가 이상하면 export를 반복하지 말고 compare 상태를 먼저 고칩니다.

### 시나리오 D: Decision Pane이 너무 복잡해 보일 때

다음 순서만 보면 됩니다.

1. compare reference 상태
2. `Track Compare Workflow`
3. `Policy Gate`
4. export 버튼

history와 inspector mirror는 main pair가 정리된 뒤에 봅니다.

## 버튼 그룹 요약

| 버튼 또는 영역 | 언제 쓰는가 | 결과 |
| --- | --- | --- |
| `Load Compare` | 예전 `graph_run_id`를 알고 있을 때 | compare reference 로드 |
| `Use Current as Compare` | current run을 baseline으로 삼고 싶을 때 | current run을 compare로 고정 |
| `Run Preset Pair Compare` | 재현 가능한 pair가 필요할 때 | baseline 후 target 실행 |
| `Run Low -> Current Compare` | 가장 짧은 auto compare가 필요할 때 | low baseline 자동 생성 |
| `Policy Gate` | pair가 decision-ready일 때 | 현재 gate 결과 계산 |
| `Run Session` | session record가 필요할 때 | regression/decision session 기록 |
| `Export Brief` | 전달용 summary가 필요할 때 | markdown brief export |
| `Inspector State Mirror` controls | inspector 상태를 위에서 조정하고 싶을 때 | decision pane에서 inspector layout/audit 상태 제어 |

## 과하게 해석하지 말아야 할 것

다음은 그 자체로 simulation failure를 뜻하지 않습니다.

- compare history retention metadata
- inspector audit state
- maintenance marker state
- saved/pinned pair metadata

이것들은 operator workflow 상태 설명이지, backend correctness 직접 신호가 아닙니다.

## 실전 판단 규칙

다음 규칙으로 보면 됩니다.

- run이 실패했으면 `Graph Run Result`를 먼저 디버깅
- run은 통과했는데 compare가 없으면 compare 상태를 먼저 복구
- compare가 읽히면 `Policy Gate`
- gate/export text가 말이 되면 brief export

## 관련 문서

- [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)
- [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)
- [Graph Lab 실패 읽기 가이드](325_graph_lab_failure_reading_guide_ko.md)
- [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)
- [Graph Lab 실사용 체크리스트](307_graph_lab_live_checklist_ko.md)
