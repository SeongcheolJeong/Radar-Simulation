# Artifact Inspector 빠른 읽기 가이드

## 목적

이 문서는 다음 상황에서 사용합니다.

- `Run Graph (API)` 뒤에 오른쪽 패널에서 무엇부터 봐야 할지 모를 때
- `Artifact Inspector`에 줄이 많아서 실전 읽는 순서만 알고 싶을 때
- brief export 전에 현재 run이 정상에 가까운지 빠르게 판단하고 싶을 때

전체 frontend 흐름은 [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)을 사용하면 됩니다.

## 위치

`Artifact Inspector`는 오른쪽 패널에서 `Graph Run Result` 아래에 있습니다.

그 위쪽 compare, gate, session, export 버튼만 따로 보고 싶다면 [Decision Pane 빠른 읽기 가이드](327_graph_lab_decision_pane_quick_guide_ko.md)를 사용하면 됩니다.

안 보이면:

1. `Load #1`
2. `Run Graph (API)`
3. 오른쪽 패널 아래로 스크롤

예시:

![Artifact Inspector](reports/graph_lab_playwright_snapshots/latest/artifact_inspector.png)

번호 마커가 들어간 예시:

![Artifact Inspector annotated](reports/graph_lab_playwright_snapshots/latest/artifact_inspector_annotated.png)

## 읽는 순서

다음 순서로 읽으면 됩니다.

1. current artifact 존재 여부
2. compare evidence, compare run이 있을 때만
3. `artifacts:`
4. `node trace:`
5. `visuals:`
6. audit/maintenance 같은 inspector state

이 순서가 좋은 이유:

- 실행 결과와 panel maintenance metadata를 섞지 않게 해 줍니다

## 각 영역 의미

### 1. Current Artifact Presence

현재 run이 실제 output을 만들었는지 확인하는 영역입니다.

정상 신호:

- current artifact row가 보인다
- 예상 파일이 보인다

보통 비정상인 이유:

- run이 output을 쓰기 전에 실패함
- backend path가 바뀌어 기대보다 적은 artifact만 생성됨

### 2. Compare Evidence

compare run이 로드되었을 때 나타납니다.

여기서 확인하는 질문:

- current와 compare가 얼마나 다른가
- shape가 맞는가
- path count 또는 peak bin drift가 있는가
- gate/export로 넘어갈 만큼 pair가 정리됐는가

### 3. `artifacts:`

가장 빠른 파일 확인 지점입니다.

주요 파일:

- `path_list.json`
- `adc_cube.npz`
- `radar_map.npz`
- `graph_run_summary.json`
- optional `lgit_customized_output.npz`

즉, status 줄만 아니라 실제 파일이 생성됐는지 확인할 때 먼저 봅니다.

### 4. `node trace:`

어떤 graph node들이 run에 참여했는지 보여줍니다.

이럴 때 유용합니다.

- graph는 valid한데 결과가 예상과 다를 때
- source에서 map까지 흐름이 맞는지 보고 싶을 때

### 5. `visuals:`

빠른 시각 확인용 참조입니다.

이럴 때 씁니다.

- raw path보다 사람이 바로 눈으로 보고 싶을 때
- 파일을 직접 열기 전에 대략적인 결과를 보고 싶을 때

### 6. Inspector State

여기에는 다음이 포함됩니다.

- layout state
- probe state
- audit state
- maintenance state

이 줄들은 시뮬레이션 자체의 정답 여부를 말하는 것이 아닙니다. panel이 기본 상태인지, customized인지, audit trail이 잘렸는지, maintenance provenance가 남아 있는지를 말합니다.

## 빠른 정상 확인법

성공 run 뒤에는 아래 4개를 먼저 보면 됩니다.

1. `Graph Run Result`가 `status: completed`
2. `Artifact Inspector`에 current artifact row가 보임
3. `artifacts:`에 예상 파일이 있음
4. compare를 올렸다면 compare evidence도 보임

이 4개가 맞으면 frontend/backend 경로는 다음 단계로 넘어갈 수준인 경우가 많습니다.

## 자주 쓰는 시나리오

### 시나리오 A: 가장 단순한 성공 run 확인

1. `Load #1`
2. `Low Fidelity: RadarSimPy + FFD`
3. `Run Graph (API)`
4. 다음 순서로 읽기
   - `Graph Run Result`
   - current artifact presence
   - `artifacts:`

기대 결과:

- `status: completed`
- artifact 파일이 보임

### 시나리오 B: current와 high fidelity 비교

1. low fidelity 실행
2. `Use Current as Compare`
3. `High Fidelity: PO-SBR` 또는 `High Fidelity: Sionna-style RT` 선택
4. `Run Graph (API)` 다시 실행
5. 다음 읽기
   - compare evidence
   - compare assessment
   - artifact delta

기대 결과:

- current와 compare evidence 둘 다 존재
- drift, shape, artifact 차이가 보임

### 시나리오 C: Run Failed

run이 실패했으면 `Artifact Inspector`부터 보지 마십시오.

순서는 이렇게 봐야 합니다.

1. 상단 status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. 그 다음 current artifact가 왜 비어 있는지 확인

이유:

- 실패 run은 artifact가 없거나 일부만 있을 수 있습니다
- root cause는 artifact 부재보다 `Graph Run Result` 쪽에 더 직접적으로 나옵니다

버튼 흐름은 [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)를 보면 됩니다.

## Artifact Inspector 안의 로컬 버튼

| 버튼 | 언제 쓰는가 | 결과 |
| --- | --- | --- |
| `Collapse Inspector Evidence` | panel이 너무 길 때 | 상세 섹션 접기 |
| `Expand Inspector Evidence` | 다시 detail이 필요할 때 | 상세 섹션 펼치기 |
| `Reset Inspector Layout` | fold/layout 상태가 헷갈릴 때 | 기본 layout 복구 |
| `Apply Recommended Audit Action` | audit trail이 잘렸고 panel이 cleanup을 추천할 때 | 추천 audit overflow 정리 |
| `Clear Action Trail` | inspector action history를 비우고 싶을 때 | audit history만 삭제 |
| `Clear Maintenance Marker` | maintenance provenance 확인을 끝냈을 때 | 현재 maintenance marker 제거 |
| `Clear Last Clear Record` | 오래된 clear provenance를 더 보관할 필요가 없을 때 | stored last-clear record 제거 |

## 과하게 해석하지 말아야 할 것

다음은 그 자체로 시뮬레이션 실패를 뜻하지 않습니다.

- `layout:customized`
- `probe:customized`
- `maintenance:marked`
- `maintenance_clear:recorded`

이것들은 operator panel 상태 표시이지, 시뮬레이션 오류 직접 신호가 아닙니다.

## 실전 판단 규칙

다음 규칙으로 보면 됩니다.

- `Graph Run Result`가 빨간색이면 run 원인부터 디버깅
- `Graph Run Result`는 녹색인데 artifact가 없으면 backend path 확인
- artifact가 있고 compare evidence도 말이 되면 `Policy Gate` 또는 `Export Brief`로 이동

## 관련 문서

- [Graph Lab UX 사용 매뉴얼](301_graph_lab_ux_manual_ko.md)
- [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Generated Reports Index](reports/README.md)
