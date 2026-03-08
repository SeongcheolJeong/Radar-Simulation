# Classic Dashboard 실사용 체크리스트

## 목적

이 문서는 classic dashboard를 열어 둔 상태에서 바로 따라가는 체크리스트입니다.

가장 짧게 확인하려는 대상:

- 첫 성공 refresh
- API를 통한 run
- compare와 policy verdict
- regression export 경로

더 자세한 설명은 [Classic Dashboard UX 사용 매뉴얼](309_classic_dashboard_ux_manual_ko.md)을 보면 됩니다.

## Dashboard 열기

실행:

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

브라우저:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

화면 참고:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

## 체크리스트 A: 첫 성공 Refresh

### A1. 입력값 확인

확인:

- `Summary JSON path`
- `API base URL`
- `Scene JSON path`

기대 결과:

- 세 입력값이 채워져 있음

### A2. Outputs 갱신

클릭:

1. `Refresh Outputs`

기대 결과:

- scene viewer가 채워짐
- radar map panel이 채워짐
- metrics 값이 보임
- detection table에 row가 보임

### A3. 빠른 정상 확인

확인:

- API health가 `200`
- dashboard status line이 빨간 상태가 아님
- 명백한 empty-state error block이 없음

## 체크리스트 B: API로 Scene 실행

control 참고:

![Classic dashboard controls annotated](reports/classic_dashboard_snapshots/latest/dashboard_controls_annotated.png)

클릭:

1. `Run Scene on API`

기대 결과:

- API run status가 idle에서 바뀜
- backend run이 제출됨
- 필요하면 `Refresh Outputs` 후 갱신 상태가 반영됨

실패하면:

1. API base URL 확인
2. scene JSON path 확인
3. `scripts/validate_web_e2e_orchestrator_api.py` 재실행

## 체크리스트 C: 두 Run 비교

입력:

1. `Baseline ID`
2. `Reference run_id`
3. `Candidate run_id`

클릭:

1. `Compare`
2. `Policy Verdict`

기대 결과:

- compare status 갱신
- policy 결과 계산

## 체크리스트 D: Regression Session 실행

입력:

1. `Regression Session ID`
2. `Candidate run_ids`

클릭:

1. `Run Regression Session`
2. `Refresh History`

기대 결과:

- session history가 채워짐
- export history도 갱신/선택 가능

## 체크리스트 E: Export

필요한 것을 클릭:

1. `Export Session`
2. `Review Bundle + Copy Path`
3. `Export Decision Report (.md)`

기대 결과:

- export path 또는 export status가 보임
- review bundle path 사용 가능
- markdown decision report 생성

## 실패 시 읽는 순서

dashboard 경로가 이상해 보이면 다음 순서로 봅니다.

1. API health
2. API run status
3. compare / regression status box
4. output panel

시각 패널부터 보지 말고, 먼저 API 경로가 정상인지 읽는 것이 맞습니다.

## 관련 문서

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX 사용 매뉴얼](309_classic_dashboard_ux_manual_ko.md)
- [Generated Reports Index](reports/README.md)
