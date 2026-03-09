# Graph Lab Low/High Fidelity 실행 흐름

## 목적

이 문서는 아래 preset을 눌렀을 때 실제로 무엇이 실행되는지 이해하려는 경우에 사용합니다.

- `Low Fidelity: RadarSimPy + FFD`
- `High Fidelity: Sionna-style RT`
- `High Fidelity: PO-SBR`

이 문서는 버튼 위치 설명 문서가 아니라, frontend preset에서 backend artifact까지 이어지는 실행 흐름 문서입니다.

## 범위

이 문서는 아래를 설명합니다.

1. low/high preset이 UI에서 어디서 시작되는지
2. 각 preset이 어떤 backend entrypoint로 들어가는지
3. low와 high가 어디서 갈라지는지
4. 어디서 다시 공통 synth/output 파이프라인으로 합쳐지는지
5. 각 단계에서 어떤 파일과 UI 신호를 봐야 하는지

## 가장 짧은 차이

```text
Low fidelity
= RadarSimPy 중심 provider 경로
+ 가능하면 RadarSimPy ADC 사용
+ FFD/Jones/compensation이 있으면 repo synth 사용

High fidelity
= ray/path provider가 먼저 path 생성
+ ADC는 공통 repo synth가 항상 생성
```

preset 정의는 여기서 시작합니다.

- [runtime_purpose_presets.mjs](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs)

backend 실행 entrypoint는 여기 있습니다.

- [scene_pipeline.py](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py)

## 공통 frontend 시작점

세 runtime track은 모두 Graph Lab에서 같은 방식으로 시작합니다.

1. Graph Lab을 엽니다.
2. `Load #1` 클릭
3. 왼쪽 runtime panel에서 preset 선택
4. `Run Graph (API)` 클릭
5. API가 graph-run record를 만들고 preset이 지정한 backend를 시작합니다.

track마다 바뀌는 것은 아래입니다.

- `runtimeBackendType`
- `runtimeProviderSpec`
- `runtimeRequiredModules`
- `runtimeSimulationMode`
- optional advanced runtime input

관련 위치:

- [runtime_purpose_presets.mjs:89](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L89)

## Low Fidelity Sequence

### Preset 구성

`Low Fidelity: RadarSimPy + FFD`를 누르면 Graph Lab은 아래 값을 채웁니다.

- backend: `radarsimpy_rt`
- provider: `avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths`
- required modules: `radarsimpy`
- simulation mode: `radarsimpy_adc`
- device hint: `cpu`

관련 위치:

- [runtime_purpose_presets.mjs:92](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L92)

### Backend 진입

backend는 여기로 들어갑니다.

- [scene_pipeline.py:656](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L656)

이 단계에서 먼저 확정되는 값:

- `tx_pos_m`
- `rx_pos_m`
- `n_chirps`
- `tx_schedule`
- `RadarConfig`

관련 위치:

- [scene_pipeline.py:661](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L661)

### Provider 단계

runtime provider 호출 위치:

- [scene_pipeline.py:686](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L686)

실제 provider:

- [radarsimpy_rt_provider.py:14](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L14)

provider 내부에서 하는 일:

1. runtime input과 optional license override 읽기
2. analytic target을 canonical `paths_by_chirp`로 변환
3. `simulation_mode` 확인
4. 가능하면 RadarSimPy `sim_radar` 호출
5. 최종 반환:
   - 항상 `paths_by_chirp`
   - 경우에 따라 `adc_sctr`

중요 분기:

- `analytic_paths`
  - path만 반환
- `radarsimpy_adc`
  - path + RadarSimPy ADC 시도
- `auto`
  - ADC를 시도하고, 허용되면 analytic fallback

관련 위치:

- [radarsimpy_rt_provider.py:41](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L41)
- [radarsimpy_rt_provider.py:51](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L51)
- [radarsimpy_rt_provider.py:72](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L72)

### Multiplexing 단계

Low fidelity에서는 RadarSimPy runtime multiplexing도 여기서 구성됩니다.

지원되는 mode:

- `tdm`
- `bpm`
- `custom`

관련 위치:

- [radarsimpy_rt_provider.py:170](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L170)
- [radarsimpy_rt_provider.py:176](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L176)
- [radarsimpy_rt_provider.py:249](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/radarsimpy_rt_provider.py#L249)

### ADC 결정 단계

scene pipeline으로 돌아오면 아래 둘 중 하나를 고릅니다.

- RadarSimPy runtime ADC 사용
- 공통 repo synth 사용

결정 지점:

- [scene_pipeline.py:708](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L708)
- [scene_pipeline.py:723](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L723)

runtime ADC를 그대로 쓰는 조건:

- provider가 `adc_sctr`를 돌려줬고
- compensation이 꺼져 있고
- antenna path synth가 필요 없을 때

반대로 아래 중 하나면 runtime ADC를 무시하고 path 기반 synth로 갑니다.

- FFD 사용
- Jones/global Jones 사용
- compensation 사용

### FFD/Jones 단계

FFD와 Jones는 별도 backend가 아니라 공통 synth logic에서 처리됩니다.

관련 위치:

- [scene_pipeline.py:799](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L799)

여기서 해결되는 것:

- `tx_ffd_files`
- `rx_ffd_files`
- antenna mode
- path-based synth 필요 여부

### 공통 Synthesis 단계

repo synth가 필요하면 path list가 여기로 들어갑니다.

- [scene_pipeline.py:843](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L843)

여기서 `synth_fmcw_tdm`이 ADC를 만듭니다.

### Low Fidelity 출력

Low fidelity run은 항상 아래 핵심 파일을 씁니다.

- `path_list.json`
- `adc_cube.npz`

저장 위치:

- [scene_pipeline.py:758](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L758)

이후 downstream 단계에서 보통 아래도 생깁니다.

- `radar_map.npz`
- `graph_run_summary.json`
- optional `lgit_customized_output.npz`

### UI에서 무엇을 봐야 하나

Low fidelity가 정상이라면 보통 아래가 보입니다.

- 상단 status line에 `backend radarsimpy_rt`
- runtime diagnostics에 RadarSimPy provider/module 상태
- `Graph Run Result`가 `status: completed`
- artifact 영역에 `path_list.json`, `adc_cube.npz`, `radar_map.npz`

## High Fidelity Sequence

### 공통 High-Fidelity 구조

두 high-fidelity preset은 공통적으로 아래 흐름을 가집니다.

```text
frontend preset
-> runtime provider가 canonical paths 생성
-> optional compensation
-> 공통 repo synth가 ADC 생성
-> 공통 output contract가 artifact 기록
```

low와 다른 핵심은:

- high-fidelity provider는 최종 ADC를 주는 쪽이 아님
- 먼저 path list를 주고
- ADC는 공통 synth가 만듭니다

## High Fidelity: Sionna-style RT

### Preset 구성

`High Fidelity: Sionna-style RT`를 누르면 아래 값이 채워집니다.

- backend: `sionna_rt`
- provider: `avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba`
- required modules: `mitsuba,drjit`
- simulation mode: `auto`
- device hint: `gpu`
- advanced fields:
  - `ego_origin_m`
  - `chirp_interval_s`
  - `min_range_m`
  - `spheres`

관련 위치:

- [runtime_purpose_presets.mjs:102](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L102)

### Backend 진입

backend는 여기로 들어갑니다.

- [scene_pipeline.py:495](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L495)

여기서 low와 같은 기본 geometry 값이 먼저 정리됩니다.

- `tx_pos_m`
- `rx_pos_m`
- `n_chirps`
- `tx_schedule`
- `RadarConfig`

### Provider 단계

runtime provider 호출 위치:

- [scene_pipeline.py:523](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L523)

실제 provider:

- [mitsuba_rt_provider.py:10](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L10)

provider 내부에서 하는 일:

1. `ego_origin_m` 검증
2. `spheres`가 비어 있지 않은지 검증
3. Mitsuba import 및 variant 선택
4. sphere list로 Mitsuba scene 구성
5. 각 chirp마다:
   - velocity로 sphere 위치 갱신
   - ego origin에서 ray 발사
   - intersection 계산
   - range, delay, Doppler, amplitude 계산
   - canonical path record 생성

관련 위치:

- [mitsuba_rt_provider.py:15](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L15)
- [mitsuba_rt_provider.py:28](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L28)
- [mitsuba_rt_provider.py:33](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L33)
- [mitsuba_rt_provider.py:45](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/mitsuba_rt_provider.py#L45)

### Synthesis와 출력

provider가 `paths_by_chirp`를 반환하면 scene pipeline은:

1. canonical path 적응
2. optional compensation
3. 공통 synth 호출
4. `path_list.json` 저장
5. `adc_cube.npz` 저장

관련 위치:

- [scene_pipeline.py:534](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L534)
- [scene_pipeline.py:539](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L539)
- [scene_pipeline.py:546](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L546)
- [scene_pipeline.py:556](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L556)

### 운영 의미

현재 interactive high-fidelity path는 이것입니다.

현재 timing evidence:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

현재 evidence 기준으로는 이 경로가 interactive budget 안에서 완료됩니다.

## High Fidelity: PO-SBR

### Preset 구성

`High Fidelity: PO-SBR`를 누르면 아래 값이 채워집니다.

- backend: `po_sbr_rt`
- provider: `avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr`
- required modules: `rtxpy,igl`
- simulation mode: `auto`
- device hint: `gpu`
- advanced fields:
  - `po_sbr_repo_root`
  - `geometry_path`
  - `chirp_interval_s`
  - `bounces`
  - `rays_per_lambda`
  - angle fields
  - `components`

관련 위치:

- [runtime_purpose_presets.mjs:116](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/runtime_purpose_presets.mjs#L116)

### Backend 진입

backend는 여기로 들어갑니다.

- [scene_pipeline.py:575](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L575)

### Provider 단계

runtime provider 호출 위치:

- [scene_pipeline.py:603](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L603)

실제 provider:

- [po_sbr_rt_provider.py:13](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L13)

provider 내부에서 하는 일:

1. chirp 수와 carrier frequency 검증
2. repo root와 geometry path 해결
3. `rays_per_lambda`, `bounces`, component field 검증
4. runtime prerequisite 확인
   - `igl`
   - `rtxpy`
5. `POsolver.py` 로드
6. geometry build
7. 각 chirp, 각 component마다:
   - `po.simulate(...)` 호출
   - amplitude, delay, Doppler, direction 계산
   - canonical path record 생성

관련 위치:

- [po_sbr_rt_provider.py:24](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L24)
- [po_sbr_rt_provider.py:70](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L70)
- [po_sbr_rt_provider.py:72](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L72)
- [po_sbr_rt_provider.py:75](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L75)
- [po_sbr_rt_provider.py:84](/home/seongcheoljeong/workspace/myproject/src/avxsim/runtime_providers/po_sbr_rt_provider.py#L84)

### Synthesis와 출력

provider가 canonical path를 돌려주면 scene pipeline은:

1. path 적응
2. optional compensation
3. 공통 synth 호출
4. `path_list.json` 저장
5. `adc_cube.npz` 저장

관련 위치:

- [scene_pipeline.py:614](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L614)
- [scene_pipeline.py:619](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L619)
- [scene_pipeline.py:627](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L627)
- [scene_pipeline.py:637](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L637)

### 운영 의미

이 경로는 interactive 기본 경로가 아니라 dedicated validation 경로입니다.

현재 timing evidence:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

현재 evidence 기준으로는 interactive-ready가 아니므로, longer-running 또는 dedicated-env validation 경로로 봐야 합니다.

## Low와 High가 다시 합쳐지는 지점

세 track은 공통 synth/output contract에서 다시 합쳐집니다.

1. canonical `paths_by_chirp`
2. optional compensation
3. optional FFD/Jones antenna handling
4. 공통 ADC synthesis
5. 공통 output artifact

합류 지점:

- [scene_pipeline.py:799](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L799)
- [scene_pipeline.py:843](/home/seongcheoljeong/workspace/myproject/src/avxsim/scene_pipeline.py#L843)

이 때문에:

- low fidelity도 FFD 사용 가능
- high fidelity도 FFD 사용 가능
- low-vs-high compare가 같은 artifact contract 위에서 가능

## 결과 인식 체크리스트

### provider 단계까지 갔는지 보려면

아래가 보여야 합니다.

- runtime diagnostics에 구체적인 backend/provider pair
- `Graph Run Result`에 실제 `graph_run_id`

### synthesis 단계까지 갔는지 보려면

아래가 보여야 합니다.

- `adc_cube.npz`
- `path_list.json`

### full contract가 끝났는지 보려면

아래가 보여야 합니다.

- `radar_map.npz`
- `graph_run_summary.json`
- compare/export 버튼들이 실제 의미를 갖기 시작함

## 어떤 경로를 써야 하나

release scope가 바뀌지 않는 한 아래 규칙으로 사용하면 됩니다.

- `Low Fidelity: RadarSimPy + FFD`
  - 빠른 baseline
  - compare reference
- `High Fidelity: Sionna-style RT`
  - interactive high-fidelity path
- `High Fidelity: PO-SBR`
  - dedicated validation 또는 closure path

현재 runtime 판단은 항상 여기서 확인합니다.

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)
