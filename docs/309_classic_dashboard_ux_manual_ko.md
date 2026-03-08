# Classic Dashboard UX 사용 매뉴얼

## 목적

이 문서는 `frontend/avx_like_dashboard.html` 사용 방법을 설명합니다.

다음 목적에 맞습니다.

- Graph Lab보다 더 단순한 frontend 경로가 필요할 때
- API 연결된 dashboard를 빠르게 확인하고 싶을 때
- summary, metrics, detection, regression control을 발표/리뷰 용도로 보고 싶을 때

가장 짧은 실행 순서는 [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)를 보면 됩니다.

## Dashboard 실행

실행:

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

브라우저:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

처음 정상 신호:

- dashboard가 열린다
- 왼쪽 control sidebar가 보인다
- scene view, map, metrics, detection table이 렌더링된다

## 화면 구성

전체 화면:

![Classic dashboard full](reports/classic_dashboard_snapshots/latest/dashboard_full.png)

번호 마커가 들어간 전체 화면:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

왼쪽 control sidebar:

![Classic dashboard controls](reports/classic_dashboard_snapshots/latest/dashboard_controls.png)

번호 마커가 들어간 control sidebar:

![Classic dashboard controls annotated](reports/classic_dashboard_snapshots/latest/dashboard_controls_annotated.png)

메인 뷰:

![Classic dashboard main](reports/classic_dashboard_snapshots/latest/dashboard_main.png)

## 주요 영역

1. 왼쪽 sidebar
   - summary path
   - API run control
   - compare control
   - regression session/export control
   - policy tuning
   - radar parameter
2. 상단 scene viewer
   - first-chirp path view
3. radar map 영역
   - visual output pane
4. metrics panel
   - 핵심 수치 요약
5. detection table
   - path/detection row

## 왼쪽 Sidebar 버튼

### Refresh / Input

| 버튼 | 언제 쓰는가 | 결과 |
| --- | --- | --- |
| `Refresh Outputs` | summary JSON이 바뀌었을 때 | 현재 dashboard 데이터 다시 읽기 |
| upload 아이콘 버튼 | 다른 summary JSON을 쓸 때 | 로컬 JSON summary 로드 |

### Run Via API

| 버튼 | 언제 쓰는가 | 결과 |
| --- | --- | --- |
| `Run Scene on API` | dashboard에서 backend run을 직접 시작할 때 | scene/profile을 API로 전송 |

### Compare / Policy

| 버튼 | 언제 쓰는가 | 결과 |
| --- | --- | --- |
| `Pin Baseline` | 현재 run을 baseline으로 고정할 때 | baseline 기록 저장 |
| `Compare` | reference/candidate run ID가 준비됐을 때 | comparison 생성 |
| `Policy Verdict` | compare 결과를 판단할 때 | policy outcome 계산 |

### Regression / Export

| 버튼 | 언제 쓰는가 | 결과 |
| --- | --- | --- |
| `Run Regression Session` | 여러 candidate run ID를 돌릴 때 | regression session 실행 |
| `Refresh History` | session/export 목록이 stale해 보일 때 | history 목록 다시 읽기 |
| `Export Session` | 선택한 regression session을 export할 때 | export artifact 저장 |
| `Review Bundle + Copy Path` | handoff-ready package가 필요할 때 | bundle 생성 후 경로 복사 |
| `Export Decision Report (.md)` | markdown handoff report가 필요할 때 | decision report 저장 |

## 추천 실행 순서

### 순서 1: 빠른 Dashboard Sanity Check

1. launcher 실행
2. dashboard URL 열기
3. `Refresh Outputs` 클릭
4. 다음 확인
   - scene viewer 내용 표시
   - radar map 영역 표시
   - metrics 수치 표시
   - detection table row 표시

### 순서 2: API로 Run 실행

1. `API base URL` 확인
2. `Scene JSON path` 확인
3. `Run Scene on API` 클릭
4. status text 변화 확인
5. 필요하면 `Refresh Outputs` 클릭

### 순서 3: 두 Run 비교

1. `Baseline ID` 입력
2. `Reference run_id` 입력
3. `Candidate run_id` 입력
4. `Compare` 클릭
5. `Policy Verdict` 클릭

### 순서 4: Regression Session과 Export

1. `Regression Session ID` 입력
2. `Candidate run_ids` 입력
3. `Run Regression Session` 클릭
4. `Refresh History` 클릭
5. `Session History`에서 session 선택
6. `Export Session` 클릭
7. 필요하면
   - `Review Bundle + Copy Path`
   - `Export Decision Report (.md)`

## 빠른 정상 확인법

다음이 맞으면 dashboard 경로는 대체로 정상입니다.

- 페이지 로드 성공
- API health `200`
- `Refresh Outputs` 후 화면이 채워짐
- `Run Scene on API` status가 오류 없이 업데이트됨
- metrics와 detection row가 보임

## 제약 사항

- 이 dashboard는 Graph Lab보다 가볍습니다
- graph 편집보다는 summary/review 흐름에 맞춰져 있습니다
- artifact 깊은 확인은 Graph Lab이 더 적합합니다

## 관련 문서

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md)
- [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)
- [Generated Reports Index](reports/README.md)
