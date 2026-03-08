# 프로젝트 구조 및 사용자 매뉴얼

## 목적

이 문서는 이 저장소의 상세 사용자 매뉴얼입니다.

다음 목적에 사용합니다.

- 프로젝트 디렉터리 구조 이해
- 로컬 개발 환경 설치
- 백엔드와 프론트엔드 실행
- 목적에 맞는 런타임 트랙 선택
- 산출물, 리포트, 트러블슈팅 경로 확인

루트 [README.md](../README.md)는 GitHub 첫 화면용 영문 요약 문서로 유지하고, [README_ko.md](../README_ko.md)는 한국어 entry page로 사용합니다. 이 문서는 실제 사용자용 상세 안내서입니다.

영문 버전:

- [Project Structure And User Manual](282_project_structure_and_user_manual.md)

문서 허브:

- [Documentation Index](README.md)
- [Generated Reports Index](reports/README.md)

## 1. 이 프로젝트는 무엇인가

이 프로젝트는 AVX 스타일 레이더 시뮬레이션 워크벤치입니다. 기본 파이프라인은 다음과 같습니다.

1. scene 또는 path 생성
2. antenna 및 multiplexing-aware signal synthesis
3. ADC cube 생성
4. radar map 및 리포트 생성
5. frontend 기반 비교 및 검증 워크플로우

아키텍처 참고:

- [Architecture](03_architecture.md)

핵심 출력 계약:

- 입력: scene/runtime config
- 출력:
  - `path_list.json`
  - `adc_cube.npz`
  - `radar_map.npz`
  - optional `lgit_customized_output.npz`

## 2. 누가 어떤 entry point를 써야 하는가

### 처음 쓰는 사용자

먼저 읽을 문서:

- [README.md](../README.md)
- 이 문서

### 프론트엔드 오퍼레이터

먼저 볼 것:

- `scripts/run_graph_lab_local.sh`
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)

### 백엔드 / 검증 개발자

먼저 볼 것:

- `src/avxsim`
- `scripts/validate_*`
- `scripts/run_*`

### 유료 RadarSimPy 검증 오퍼레이터

먼저 볼 것:

- `scripts/run_radarsimpy_paid_6m_gate_ci.sh`
- `scripts/run_radarsimpy_production_release_gate.py`
- `scripts/run_radarsimpy_readiness_checkpoint.py`

## 3. 저장소 구조

### 최상위 구조

```text
README.md
configs/
data/
docs/
external/
frontend/
scripts/
src/
tests/
```

### `src/avxsim`

핵심 Python 패키지입니다.

중요 파일:

- `scene_pipeline.py`
  - scene에서 artifact까지 이어지는 상위 오케스트레이션
- `runtime_providers/`
  - 런타임/백엔드 provider
  - `radarsimpy_rt_provider.py`
  - `mitsuba_rt_provider.py`
  - `po_sbr_rt_provider.py`
- `synth.py`
  - FMCW/TDM synthesis 로직
- `antenna.py`
  - antenna gain 처리
- `ffd.py`
  - FFD 파싱 및 interpolation
- `adc_pack_builder.py`
  - ADC / radar map 패키징
- `lgit_output_adapter.py`
  - LGIT 형식 출력 adapter
- `web_e2e_api.py`
  - frontend가 사용하는 backend API

### `frontend`

브라우저 UI 영역입니다.

주요 파일:

- `frontend/graph_lab_reactflow.html`
  - 메인 오퍼레이터 UI shell
- `frontend/graph_lab/`
  - Graph Lab 모듈들
- `frontend/avx_like_dashboard.html`
  - 더 단순한 demo/dashboard 화면

### `scripts`

실행 가능한 entry point가 모여 있습니다.

대표 분류:

- launcher
  - `run_graph_lab_local.sh`
  - `run_web_e2e_dashboard_local.sh`
- validator
  - `validate_web_e2e_orchestrator_api.py`
  - `validate_graph_lab_playwright_e2e.py`
- backend gate
  - `run_radarsimpy_paid_6m_gate_ci.sh`
  - `run_po_sbr_post_change_gate.py`
- report/build helper
  - `build_frontend_demo_example.py`
  - `build_release_announcement_pack.py`

### `docs`

프로젝트 문서 영역입니다.

시작점으로 좋은 문서:

- [Architecture](03_architecture.md)
- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Compare History Bundle Schema Migration](281_compare_history_bundle_schema_migration.md)

### `data`

샘플 및 생성 산출물 영역입니다.

대표 위치:

- `data/demo/`
  - frontend demo fixture
- `data/web_e2e/`
  - API가 생성한 run/comparison/session 기록
- `data/runtime_*`
  - runtime 관련 샘플 자산

### `external`

선택적으로 사용하는 third-party runtime, mirror, reference 저장소입니다.

예:

- `external/radarsimpy*`
- `external/sionna`
- `external/PO-SBR-Python`
- `external/rtxpy-mod`
- `external/HybridDynamicRT`

기본 사용에는 전부 필요하지 않습니다.

## 4. 설치 방법

분리된 설치 가이드:

- [Documentation Index](README.md)
- [Install Onboarding Map](288_install_onboarding_map.md)
- [Install Guide: Base Environment](284_install_base_environment.md)
- [Install Guide: RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Install Guide: Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md)
- [Install Guide: PO-SBR Runtime](287_install_po_sbr_runtime.md)

### 4.1 기본 설치

로컬 demo/frontend 사용 기준 최소 권장 환경:

```bash
cd /path/to/myproject
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy matplotlib
```

이 정도로 시작 가능한 이유:

- demo 생성에 `numpy` 사용
- demo 시각화에 `matplotlib` 사용
- Graph Lab은 정적 HTML + JS 기반이라 Node 빌드가 필수는 아님

### 4.2 선택적 브라우저 E2E 검증

브라우저 자동 검증까지 하려면:

```bash
python -m pip install playwright
python -m playwright install chromium
```

### 4.3 선택적 런타임 백엔드

이 저장소는 목적별 runtime track을 지원합니다. 전부 필수는 아닙니다.

#### RadarSimPy

필요한 경우:

- `RadarSimPy + FFD`
- paid/trial RadarSimPy runtime 검증
- low-fidelity reference track

관련 파일:

- `src/avxsim/radarsimpy_api.py`
- `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`

참고:

- 저장소 내 bundled asset 또는 로컬 설치 runtime을 활용할 수 있습니다.
- 유료 workflow는 유효한 `.lic` 파일이 필요합니다.

#### Sionna-style RT

일반적으로 필요한 모듈:

- `mitsuba`
- `drjit`

용도:

- higher-fidelity RT path generation

#### PO-SBR

일반적으로 필요한 모듈:

- `rtxpy`
- `igl`

bootstrap helper:

- `scripts/bootstrap_po_sbr_linux_env.sh`

용도:

- higher-fidelity PO/SBR path generation

### 4.4 현실적인 주의점

현재 이 저장소는 모든 optional backend 조합을 하나로 묶은 루트 `requirements.txt` 또는 `pyproject.toml`을 제공하지 않습니다.

즉:

- 기본 사용은 비교적 간단함
- full runtime parity는 환경 의존적임
- optional backend는 실제 필요한 경우에만 설치하는 것이 맞음

## 5. 실행 방법

### 5.1 Classic Dashboard Demo 실행

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

브라우저 주소:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

이 스크립트가 하는 일:

1. `data/demo/frontend_quickstart_v1` 아래 demo artifact 생성
2. backend API 실행
3. 정적 웹 서버 실행

### 5.2 Graph Lab 실행

```bash
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

브라우저 주소:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

이 스크립트가 하는 일:

1. `8101` 포트에 backend API 실행
2. `8081` 포트에 정적 서버 실행
3. Graph Lab UI 제공

### 5.3 Backend/API 검증 실행

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
```

사용 시점:

- backend contract를 수정했을 때
- 브라우저를 열기 전에 빠르게 sanity check 하고 싶을 때

### 5.4 Graph Lab 브라우저 E2E 실행

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers \
PYTHONPATH=src .venv/bin/python \
scripts/validate_graph_lab_playwright_e2e.py \
  --require-playwright \
  --output-json docs/reports/graph_lab_playwright_e2e_latest.json
```

사용 시점:

- frontend 변경 후 실제 브라우저 동작을 검증할 때

## 6. Graph Lab 사용법

Graph Lab은 메인 오퍼레이터 UI입니다.

### 6.1 핵심 개념

다음 작업을 수행합니다.

- scene/runtime 설정
- 현재 그래프 실행
- low/high fidelity 결과 비교
- artifact와 decision evidence 확인

### 6.2 Purpose Preset

대표 preset:

- `Low Fidelity: RadarSimPy + FFD`
- `High Fidelity: Sionna-style RT`
- `High Fidelity: PO-SBR`

용도:

- `Low Fidelity`
  - 빠른 기준선
  - compare baseline에 적합
- `High Fidelity`
  - ray-tracing 기반 결과를 보고 싶을 때 사용

상세 문서:

- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)

### 6.3 추천 오퍼레이터 흐름

#### low vs high 비교

1. Graph Lab 실행
2. target high-fidelity preset 선택
3. 현재 설정 실행 또는 pair-runner 사용
4. low fidelity 결과와 비교
5. `Artifact Inspector` 확인
6. decision brief 확인 또는 export

#### 가장 빠른 경로

다음 기능을 사용:

- `Run Preset Pair Compare`
- 또는 `Run Low -> Current Compare`

### 6.4 주요 화면

#### Runtime Panel

다음 정보를 보여줍니다.

- 선택한 backend/provider
- FFD field
- runtime diagnostics
- provider별 advanced control

#### Decision Pane

다음 정보를 보여줍니다.

- compare workflow 상태
- compare history
- pinned quick action
- inspector state mirror
- decision summary

#### Artifact Inspector

다음 정보를 보여줍니다.

- live compare evidence
- history expectation snapshot
- compare assessment
- audit / maintenance state

## 7. 산출물과 리포트

### 7.1 주요 산출물

일반적인 출력:

- `path_list.json`
- `adc_cube.npz`
- `radar_map.npz`
- optional `lgit_customized_output.npz`

### 7.2 생성 리포트

주요 위치:

- `docs/reports/`

예:

- `frontend_quickstart_v1.json`
- `graph_lab_playwright_e2e_latest.json`
- RadarSimPy gate 리포트
- release pack 리포트

### 7.3 API run record

주요 위치:

- `data/web_e2e/`

이 영역에는 다음이 저장됩니다.

- run record
- comparison
- regression session
- export 결과

## 8. 고급 / 유료 검증

production 지향 RadarSimPy 검증:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

또는 주요 단계 직접 실행:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_production_release_gate.py --license-file /abs/path/license.lic
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_readiness_checkpoint.py --with-real-runtime --runtime-license-tier production --license-file /abs/path/license.lic
PYTHONPATH=src .venv/bin/python scripts/validate_radarsimpy_simulator_reference_parity_optional.py --require-runtime --output-json docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json
```

사용 시점:

- paid runtime access 확인
- production parity readiness 확인
- release용 보고서 생성

## 9. 트러블슈팅

### API가 시작되지 않음

확인할 것:

- `.venv/bin/python` 존재 여부
- 직접 Python 실행 시 `PYTHONPATH=src` 설정 여부
- `/tmp/web_e2e_api_<port>.log` 로그

### 프론트엔드는 열리는데 action이 blocked 됨

대표 원인:

- 선택한 runtime backend가 설치되지 않음

확인할 것:

- Graph Lab runtime diagnostics
- 선택한 preset에 필요한 모듈 설치 여부

### Playwright E2E가 바로 실패함

확인할 것:

- `playwright` Python package 설치 여부
- `python -m playwright install chromium` 실행 여부

### Dashboard fetch가 브라우저에서 실패함

`file://`로 직접 열지 말고 다음 스크립트를 사용해야 합니다.

- `scripts/run_web_e2e_dashboard_local.sh`
- `scripts/run_graph_lab_local.sh`

즉, 반드시 `http://`로 서빙되는 상태에서 열어야 합니다.

### RadarSimPy production gate가 blocked 됨

확인할 것:

- `.lic` 파일 경로가 유효한지
- paid runtime이 실제로 접근 가능한지
- 필요한 runtime package 또는 bundled asset이 존재하는지

## 10. 문서 구조 권장안

이 저장소 문서를 유지보수할 때는 다음 구조가 맞습니다.

### `README.md`

용도:

- 프로젝트 개요
- quick install
- quick run
- docs index

### `docs/282_project_structure_and_user_manual.md`

용도:

- 영문 상세 매뉴얼

### `docs/283_project_structure_and_user_manual_ko.md`

용도:

- 한국어 상세 매뉴얼
- 실제 사용자 온보딩 문서

### `docs/` 내 개별 상세 문서

용도:

- architecture contract
- runtime provider detail
- frontend workflow detail
- release / gate report

이 구조가 GitHub 가시성, 신규 사용자 온보딩, 장기 유지보수 측면에서 가장 적절합니다.
