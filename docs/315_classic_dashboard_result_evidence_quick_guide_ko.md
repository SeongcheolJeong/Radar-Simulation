# Classic Dashboard Result / Evidence Quick Guide

## 목적

classic dashboard를 이미 띄운 상태에서, 결과 구역을 어떤 순서로 읽어야 하는지 빠르게 확인할 때 이 문서를 사용합니다.

다음 액션 뒤에 보는 문서입니다.

- `Refresh Outputs`
- `Run Scene on API`
- `Compare`
- `Policy Verdict`
- `Run Regression Session`

버튼 의미를 먼저 보고 싶으면 [Classic Dashboard Button Scenario Guide](313_classic_dashboard_button_scenario_guide_ko.md)를 보십시오.

가장 짧은 클릭 순서가 필요하면 [Classic Dashboard Live Checklist](311_classic_dashboard_live_checklist_ko.md)를 보십시오.

## 화면 기준 이미지

전체 화면:

![Classic dashboard full](reports/classic_dashboard_snapshots/latest/dashboard_full.png)

번호가 들어간 전체 화면:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

메인 결과 영역:

![Classic dashboard main](reports/classic_dashboard_snapshots/latest/dashboard_main.png)

## 이 순서로 읽으십시오

1. header의 `runtime badge`
2. 왼쪽 sidebar의 `api run status`
3. `scene viewer`
4. `radar map area`
5. `metrics panel`
6. `detection table`
7. `compare status`와 `compare result box`
8. `Regression Gate`, `Decision Audit`, `Evidence Drill-Down`
9. export path box들

이 순서는 화면만 로드된 상태인지, backend run이 실제로 끝났는지, compare/regression evidence가 있는지 구분하기 위한 순서입니다.

## 각 영역 의미

### 1. Runtime Badge 와 API Run Status

볼 곳:

- header `runtime: ...`
- 왼쪽 sidebar `api run status`

정상 신호:

- refresh/run 이후 runtime이 계속 `unknown`으로 남지 않음
- `api run status`가 idle에서 완료/ready 계열 상태로 바뀜

주요 비정상 원인:

- API server 접속 실패
- scene path 또는 profile 오류
- backend run이 output 생성 전에 실패

## 2. Scene Viewer

상단의 시각화 영역입니다.

여기서 확인할 것:

- scene summary가 실제로 로드됐는가?
- first-chirp path view가 비어 있지 않은가?

정상 신호:

- scene 이미지가 보임
- 다른 summary/run을 읽으면 바뀜

## 3. Radar Map Area

메인 map 시각화 영역입니다.

여기서 확인할 것:

- RD/RA output이 생성됐는가?
- stale output이 아니라 현재 output을 보고 있는가?

정상 신호:

- map pane이 채워짐
- map과 metrics/detection이 같이 보임

## 4. Metrics Panel

숫자 요약 영역입니다.

여기서 확인할 것:

- run이 numeric summary를 만들었는가?
- headline 값이 존재하는가?

정상 신호:

- 숫자 값이 여러 개 보임
- 값이 전부 비어 있지 않음

## 5. Detection Table

가장 빠른 output 존재 확인 구역입니다.

여기서 확인할 것:

- detection/path row가 생성됐는가?
- row가 현재 scene/run과 대략 맞는가?

정상 신호:

- table row가 보임
- refresh/run 후 입력이 바뀌면 row도 바뀜

## 6. Compare Status 와 Compare Result Box

볼 곳:

- `compare status`
- `compare result box`

언제 보나:

- `Compare`
- `Policy Verdict`

정상 신호:

- status가 idle에서 벗어남
- result box가 `-`가 아니라 compare/policy 내용으로 채워짐

주요 비정상 원인:

- `reference run_id` 또는 `candidate run_id` 누락
- baseline/reference/candidate가 서로 stale하거나 다른 run을 가리킴
- backend run 완료 전에 compare를 실행함

## 7. Regression Gate

볼 곳:

- `Regression Gate` badge
- session/export count
- latest session/export line

언제 보나:

- `Run Regression Session`
- `Refresh History`
- `Export Session`

정상 신호:

- badge가 `NO DATA`에서 벗어남
- regression/export 후 count가 증가
- latest line이 최근 activity를 가리킴

## 8. Decision Audit

볼 곳:

- `Decision Audit` badge
- summary/trend/rule histogram/hot candidate line

여기서 확인할 것:

- 현재 decision outcome이 어떤 rule/trend에 의해 만들어졌는가?
- 지금 가장 문제인 candidate가 누구인가?

정상 신호:

- compare/regression 이후 audit line이 채워짐
- trend/histogram이 `-`가 아님

## 9. Evidence Drill-Down

볼 곳:

- candidate selector
- gate failure rule selector
- `Use Candidate`
- `Open Policy Eval`
- detail box

여기서 확인할 것:

- 어떤 candidate row가 실패/드리프트했는가?
- 어떤 policy rule이 원인인가?
- 현재 candidate를 compare panel로 pivot할 수 있는가?

정상 신호:

- session/candidate/policy line이 채워짐
- detail box가 `-`가 아니라 구조화된 evidence를 보여줌

## 10. Export Evidence Paths

볼 곳:

- `review bundle status`
- `review bundle path box`
- `decision report status`
- `decision report file box`
- `regression downloads`

언제 보나:

- `Export Session`
- `Review Bundle + Copy Path`
- `Export Decision Report (.md)`

정상 신호:

- path 또는 file location이 보임
- status가 idle에서 벗어남

## 시나리오별 빠른 읽기

### `Refresh Outputs` 직후

이 순서로 봅니다.

1. runtime badge
2. scene viewer
3. radar map area
4. metrics panel
5. detection table

### `Run Scene on API` 직후

이 순서로 봅니다.

1. `api run status`
2. runtime badge
3. map/metrics/table
4. 화면이 stale해 보이면 `Refresh Outputs`

### `Compare` / `Policy Verdict` 직후

이 순서로 봅니다.

1. `compare status`
2. `compare result box`
3. `Decision Audit`
4. `Evidence Drill-Down`

### `Run Regression Session` 직후

이 순서로 봅니다.

1. `regression status`
2. `Regression Gate`
3. `Decision Audit`
4. `regression downloads`

### Export 직후

이 순서로 봅니다.

1. `review bundle status`
2. `review bundle path box`
3. `decision report status`
4. `decision report file box`

## 실패 시 가장 빠른 읽는 순서

dashboard가 이상해 보이면 이 순서로 읽으십시오.

1. header runtime badge
2. `api run status`
3. `compare status` 또는 `regression status`
4. `compare result box`
5. export path box
6. 그 다음 [Classic Dashboard Live Checklist](311_classic_dashboard_live_checklist_ko.md)의 해당 시퀀스를 다시 따라갑니다

## 관련 문서

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX Manual](309_classic_dashboard_ux_manual_ko.md)
- [Classic Dashboard Button Scenario Guide](313_classic_dashboard_button_scenario_guide_ko.md)
- [Classic Dashboard Live Checklist](311_classic_dashboard_live_checklist_ko.md)
- [Generated Reports Index](reports/README.md)
