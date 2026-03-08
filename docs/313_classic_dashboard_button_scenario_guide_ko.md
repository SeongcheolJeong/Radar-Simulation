# Classic Dashboard 버튼 시나리오 가이드

## 목적

이 문서는 classic dashboard 버튼을 `하려는 일` 기준으로 설명합니다.

다음 상황에서 사용하면 됩니다.

- 왼쪽 sidebar control이 많아서 무엇부터 눌러야 할지 모를 때
- 특정 작업의 가장 짧은 클릭 순서가 필요할 때
- 전체 UX manual을 먼저 읽고 싶지 않을 때

전체 화면 설명은 [Classic Dashboard UX 사용 매뉴얼](309_classic_dashboard_ux_manual_ko.md)을 보면 됩니다.

## 화면 참고

전체 화면:

![Classic dashboard full](reports/classic_dashboard_snapshots/latest/dashboard_full.png)

번호 마커가 들어간 전체 화면:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

번호 마커가 들어간 controls:

![Classic dashboard controls annotated](reports/classic_dashboard_snapshots/latest/dashboard_controls_annotated.png)

## 시나리오 1: 화면에 데이터만 먼저 보이고 싶다

언제:

- 페이지는 열렸는데 패널이 비어 보일 때

위치:

- 왼쪽 sidebar 상단

버튼:

1. `Refresh Outputs`

기대 결과:

- scene viewer가 채워짐
- radar map panel이 채워짐
- metrics 값이 보임
- detection table row가 보임

## 시나리오 2: Dashboard에서 Backend Run을 직접 시작하고 싶다

언제:

- dashboard가 API를 직접 호출해야 할 때

위치:

- 왼쪽 sidebar `Run via API`

버튼과 필드:

1. `API base URL` 확인
2. `Scene JSON path` 확인
3. `Profile` 확인
4. `Run Scene on API` 클릭

기대 결과:

- API run status가 idle에서 바뀜
- backend run이 제출됨
- 완료 후 필요하면 output refresh 가능

## 시나리오 3: 두 Run을 비교하고 싶다

언제:

- reference/candidate run ID를 이미 알고 있을 때

위치:

- 왼쪽 sidebar `Compare Runs (API)`

버튼과 필드:

1. `Baseline ID` 입력
2. `Reference run_id` 입력
3. `Candidate run_id` 입력
4. `Compare` 클릭
5. `Policy Verdict` 클릭

기대 결과:

- compare status 갱신
- policy 결과 계산

## 시나리오 4: 현재 기준 Run을 Baseline으로 고정하고 싶다

언제:

- compare나 policy 판단 전에 baseline을 고정할 때

위치:

- 왼쪽 sidebar `Compare Runs (API)`

버튼:

1. `Baseline ID` 입력
2. `Reference run_id` 입력
3. `Pin Baseline` 클릭

기대 결과:

- baseline pinning 성공
- compare/policy에 쓸 baseline 상태 준비

## 시나리오 5: Regression Session을 실행하고 싶다

언제:

- 여러 candidate run을 한 번에 평가할 때

위치:

- 왼쪽 sidebar regression section

버튼과 필드:

1. `Regression Session ID` 입력
2. `Candidate run_ids` 입력
3. `Run Regression Session` 클릭
4. `Refresh History` 클릭

기대 결과:

- session history가 채워짐
- session을 선택할 수 있음

## 시나리오 6: Session 또는 Review Package를 Export하고 싶다

언제:

- regression session이 이미 있을 때

위치:

- 왼쪽 sidebar regression/export section

버튼:

1. `Export Session`
2. `Review Bundle + Copy Path`
3. `Export Decision Report (.md)`

기대 결과:

- export status line 갱신
- 요청 시 review bundle path 표시
- markdown decision report 생성

## 시나리오 7: Verdict 전에 Policy를 조정하고 싶다

언제:

- 기본 threshold만으로는 부족할 때

위치:

- 왼쪽 sidebar `Policy Tuning`

버튼과 필드:

1. policy preset 선택
2. 필요하면 parity / fail-count / shape threshold 조정
3. 그 다음 `Policy Verdict` 클릭

기대 결과:

- 현재 tuning 값으로 verdict 계산

## 시나리오 8: ID를 다시 입력하지 말고 History를 재사용하고 싶다

언제:

- 이전 session/export가 이미 있을 때

위치:

- 왼쪽 sidebar regression history section

버튼과 필드:

1. `Refresh History`
2. `Session History` 선택
3. `Export History` 선택
4. `Export Session` 또는 `Review Bundle + Copy Path` 사용

기대 결과:

- 모든 것을 다시 입력하지 않고 old session/export 상태 재사용

## 시나리오 9: 실패를 빠르게 읽고 싶다

다음 순서로 읽습니다.

1. API health
2. API run status
3. compare status
4. regression/export status
5. 그 다음 visual panel

자주 보는 의미:

| 보이는 상태 | 의미 | 다음 조치 |
| --- | --- | --- |
| API health가 안 됨 | backend가 내려갔거나 URL이 틀림 | API base URL 수정 또는 launcher 재시작 |
| `Run Scene on API` 실패 | scene/profile/backend path 문제 | scene path 확인 후 backend validator 재실행 |
| compare 실패 | run ID 또는 baseline 상태 문제 | reference/candidate ID 재확인, 필요하면 baseline 다시 pin |
| export/review bundle 실패 | session/export 상태가 불완전 | history refresh 후 유효한 session 선택 |

## 빠른 선택 표

| 하고 싶은 일 | 이동할 곳 | 가장 먼저 누를 버튼 |
| --- | --- | --- |
| 화면 채우기 | 왼쪽 위 | `Refresh Outputs` |
| backend run 실행 | `Run via API` | `Run Scene on API` |
| 두 run 비교 | `Compare Runs (API)` | `Compare` |
| decision outcome 계산 | `Compare Runs (API)` | `Policy Verdict` |
| baseline 저장 | `Compare Runs (API)` | `Pin Baseline` |
| regression session 실행 | regression section | `Run Regression Session` |
| session/export history 갱신 | regression section | `Refresh History` |
| session export | regression/export section | `Export Session` |
| handoff bundle 생성 | regression/export section | `Review Bundle + Copy Path` |
| markdown decision output export | regression/export section | `Export Decision Report (.md)` |

## 관련 문서

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX 사용 매뉴얼](309_classic_dashboard_ux_manual_ko.md)
- [Classic Dashboard 실사용 체크리스트](311_classic_dashboard_live_checklist_ko.md)
- [Generated Reports Index](reports/README.md)
