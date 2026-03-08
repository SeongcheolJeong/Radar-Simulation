# Graph Lab 실사용 체크리스트

## 목적

이 문서는 Graph Lab 화면을 열어 둔 상태에서 바로 따라가는 체크리스트입니다.

전체 설명 문서가 아니라, 다음을 가장 짧게 확인하기 위한 문서입니다.

- 첫 성공 run
- low-vs-high compare
- artifact 확인
- brief export

전체 설명은 [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)을 보면 됩니다.

## Graph Lab 열기

실행:

```bash
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

브라우저:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

화면 참고:

![Graph Lab annotated](reports/graph_lab_playwright_snapshots/latest/page_full_annotated.png)

## 체크리스트 A: 첫 성공 Run

### A1. Known-Good Graph 로드

클릭:

1. `Refresh Templates`
2. `Load #1`

기대 결과:

- canvas에 4개 node가 보임
- validation 뒤에 오른쪽 패널에 `valid: true`

### A2. 실행 전 검증

클릭:

1. `Validate Graph Contract`

기대 결과:

- `Validation Result`
- `valid: true`
- `nodes: 4, edges: 3`

### A3. 빠른 baseline runtime 설정

클릭:

1. `Low Fidelity: RadarSimPy + FFD`

확인:

- `Runtime Backend = radarsimpy_rt`
- runtime diagnostics가 채워짐

### A4. Graph 실행

클릭:

1. `Run Graph (API)`

기대 결과:

- 상단 status에 `graph run completed`
- 오른쪽 `Graph Run Result`에 `status: completed`
- 새 `graph_run_id`가 보임

실패하면:

- [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)
- 그 안의 `왜 run이 실패했는지 알고 싶다` 시나리오로 이동

## 체크리스트 B: Artifact 존재 확인

오른쪽 패널의 `Artifact Inspector`로 스크롤합니다.

화면 참고:

![Artifact Inspector annotated](reports/graph_lab_playwright_snapshots/latest/artifact_inspector_annotated.png)

다음 순서로 확인:

1. current artifact row 존재
2. `artifacts:` 존재
3. 아래 파일이 보임
   - `path_list.json`
   - `adc_cube.npz`
   - `radar_map.npz`
   - `graph_run_summary.json`

이 패널만 짧게 보고 싶으면 [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)를 보면 됩니다.

## 체크리스트 C: Low-vs-High Compare 만들기

### C1. 현재 Low Run을 Compare로 저장

클릭:

1. `Use Current as Compare`

기대 결과:

- compare reference가 설정됨

### C2. High Fidelity로 전환

다음 중 하나 클릭:

1. `High Fidelity: PO-SBR`
2. `High Fidelity: Sionna-style RT`

특별히 Sionna-style 경로가 필요하지 않으면 `PO-SBR`을 사용하면 됩니다.

### C3. 다시 실행

클릭:

1. `Run Graph (API)`

기대 결과:

- current run 완료
- 오른쪽 패널에 compare evidence 표시

## 체크리스트 D: 가장 빠른 Auto Compare

화면 참고:

![Decision Pane annotated](reports/graph_lab_playwright_snapshots/latest/decision_pane_annotated.png)

클릭:

1. 왼쪽 패널에서 target runtime 설정
2. `Run Low -> Current Compare`

기대 결과:

- low baseline 자동 생성
- target run 자동 생성
- compare state 채워짐

## 체크리스트 E: 판단 후 Export

다음 순서로 클릭:

1. `Policy Gate`
2. `Run Session`
3. `Export Brief`

기대 결과:

- decision/gate 상태가 보임
- brief export 생성

## 실패 시 읽는 순서

빨간 상태가 보이면 다음 순서로 읽습니다.

1. 상단 status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. `Artifact Inspector`

artifact가 없는 것부터 보지 말고, 먼저 run error를 읽는 것이 맞습니다.

## 관련 문서

- [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)
- [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)
- [Artifact Inspector 빠른 읽기 가이드](305_artifact_inspector_quick_guide_ko.md)
