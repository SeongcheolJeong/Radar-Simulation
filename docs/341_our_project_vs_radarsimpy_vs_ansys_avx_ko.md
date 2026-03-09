# 우리 프로젝트 vs RadarSimPy vs Ansys AVx

## 목적

이 문서는 아래 질문에 직접 답하기 위한 문서입니다.

- 우리 프로젝트는 plain `RadarSimPy`보다 더 좋은가?
- 우리 프로젝트는 이미 `Ansys AVx`급인가?
- 현재 우리 시뮬레이션의 물리 수준은 어느 정도인가?

이 문서는 UI 사용 문서가 아니라, 포지셔닝과 physics level을 설명하는 문서입니다.

## 가장 짧은 결론

가장 정확한 한 줄은 아래입니다.

```text
plain RadarSimPy < 우리 프로젝트 < Ansys AVx
```

이 한 줄은 항목별로 나눠서 읽어야 합니다.

- 우리 프로젝트는 hybrid simulation workbench 관점에서 plain `RadarSimPy`보다 강합니다.
- 하지만 아직 `Ansys AVx`급 실시간 production sensor platform은 아닙니다.

## 비교 범위

이 문서는 아래 세 대상을 비교합니다.

1. `RadarSimPy`를 직접 사용하는 경우
2. `RadarSimPy`를 포함할 수 있지만, 자체 backend abstraction, path pipeline, antenna 처리, compensation, validation, frontend workflow를 더한 이 저장소
3. 상용 high-fidelity reference인 `Ansys AVxcelerate Sensors`와 `Ansys Perceive EM`

## plain RadarSimPy보다 우리 프로젝트가 나은 점

### 1. backend-agnostic simulation pipeline

이 저장소는 명시적으로 아래 구조를 가집니다.

- `PathGenerator`
- `AntennaModel`
- `FmcwMultiplexingSynthesizer`
- `OutputWriter`

관련 문서:

- [03_architecture.md](03_architecture.md)

이 구조 덕분에 같은 output contract 아래에서 아래 backend를 교체해 쓸 수 있습니다.

- low fidelity: `radarsimpy_rt`
- high fidelity: `sionna_rt`
- 더 높은 물리 수준의 asymptotic EM 경로: `po_sbr_rt`

핵심 실행 entrypoint:

- [scene_pipeline.py](../src/avxsim/scene_pipeline.py)

### 2. antenna와 polarization 처리 수준이 더 높음

plain `RadarSimPy`도 radar system과 signal-chain 관점에서는 유용하지만, 이 프로젝트는 repo 차원에서 아래를 더합니다.

- FFD antenna pattern
- Jones vector / matrix
- global Jones transform

관련 코드:

- [synth.py](../src/avxsim/synth.py)
- [scene_pipeline.py](../src/avxsim/scene_pipeline.py)

### 3. path list 위에 얹히는 compensation layer

이 저장소는 아래 보정 레이어를 명시적으로 가집니다.

- wideband correction
- manifold asset gain / phase
- diffuse spawn
- clutter spawn

관련 코드:

- [radar_compensation.py](../src/avxsim/radar_compensation.py)

즉, 이 프로젝트는 단순한 path tracer도 아니고, 단순한 waveform simulator도 아닙니다. path set을 받은 뒤 synthesis 전에 물리 보정을 적용할 수 있습니다.

### 4. validation과 operator workflow가 더 강함

plain `RadarSimPy`에는 이 저장소 수준의 통합 workflow가 없습니다.

- low-vs-high track comparison
- frontend runtime selection
- artifact inspection
- stable evidence report
- release gate / parity validation

관련 문서와 report:

- [289_canonical_validation_scenario_pack.md](289_canonical_validation_scenario_pack.md)
- [docs/reports/README.md](reports/README.md)
- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

## Ansys AVx보다 아직 아래인 점

이 프로젝트를 이미 `Ansys AVx`와 동급이라고 말하면 과장입니다.

공식 `Ansys AVxcelerate Sensors`는 physically accurate real-time sensor simulation, SiL/HiL, multi-sensor workflow, GPU radar, multi-bounce, dielectric transmission을 제품 기능으로 제시합니다. 공식 `Ansys Perceive EM`은 PO-based SBR solver, GPU acceleration, large-scale radar/wireless modeling, real-time channel modeling을 제시합니다. 이건 단순 알고리즘이 아니라 product-level claim입니다.

공식 참고:

- [Ansys AVxcelerate Sensors](https://www.ansys.com/products/av-simulation/ansys-avxcelerate-sensors)
- [Ansys Perceive EM](https://www.ansys.com/products/electronics/ansys-perceive-em)

실제로는 이 저장소가 아직 아래와 같은 부분에서 AVx보다 낮습니다.

### 1. real-time productization

이 저장소에는 high-fidelity backend가 있지만, 현재 interactive high-fidelity 권장은 아래입니다.

- interactive frontend용: `Sionna-style RT`
- dedicated validation용: `PO-SBR`

관련 evidence:

- [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

이건 broad real-time GPU production radar platform을 주장하는 것과는 다릅니다.

### 2. scene / material complexity

`Ansys AVx`와 `Perceive EM`은 large-scale scene, richer material behavior, multi-bounce, transmission, productized solver stack을 전제로 설명됩니다.

이 저장소도 아래는 갖고 있습니다.

- path-based high-fidelity option
- PO-SBR backend path
- basic analytic path보다 높은 scene realism

하지만 아직은 commercial end-to-end autonomy sensor platform이 아니라 repo-scale hybrid simulator입니다.

### 3. HIL / raw-sensor production story

`Ansys AVx`는 raw-sensor output과 HiL/SiL/MiL connectivity를 제품 capability로 명시합니다.

이 저장소도 output contract, evidence export, operator workflow는 강하지만, 그것이 곧 mature commercial raw-sensor integration product를 의미하지는 않습니다.

## 우리 시뮬레이션의 physics level

가장 정확한 표현은 아래입니다.

```text
이 프로젝트는 hybrid radar simulator다.
full-wave Maxwell solver는 아니다.
physics level은 어떤 backend가 path set을 만들었는지에 따라 달라진다.
```

## 공통적으로 강한 물리 계층

모든 track에서 이 저장소가 가장 강한 부분은 아래입니다.

- FMCW signal-chain synthesis
- path data에서 ADC 생성
- downstream radar-map 생성
- antenna / polarization augmentation
- output / evidence contract

이 공통 signal-chain 계층은 주로 아래에 있습니다.

- [synth.py](../src/avxsim/synth.py)
- [scene_pipeline.py](../src/avxsim/scene_pipeline.py)

## runtime track별 physics ladder

### Low Fidelity: `RadarSimPy + FFD`

이 단계는 아래처럼 보는 것이 가장 정확합니다.

- system-level radar simulation은 강함
- waveform / DSP realism은 좋음
- FFD/Jones를 쓰면 antenna realism도 좋아짐
- 하지만 scene EM realism은 ray-tracing이나 PO-SBR보다 제한적

실무 해석:

- signal-chain physics: 강함
- antenna / polarization physics: 중간 이상
- scene propagation / scattering realism: 낮음~중간

관련 provider:

- [radarsimpy_rt_provider.py](../src/avxsim/runtime_providers/radarsimpy_rt_provider.py)

### High Fidelity: `Sionna-style RT`

이 단계는 아래처럼 보는 것이 맞습니다.

- low fidelity보다 geometric ray/path realism이 높음
- ray-intersection style logic으로 path 생성
- plain analytic / point-target-only flow보다 propagation realism이 높음
- 그래도 full EM은 아님

실무 해석:

- signal-chain physics: 강함
- antenna / polarization physics: 중간 이상
- propagation realism: 중간
- scattering realism: 중간 수준 이하

관련 provider:

- [mitsuba_rt_provider.py](../src/avxsim/runtime_providers/mitsuba_rt_provider.py)

### High Fidelity: `PO-SBR`

현재 repo 안에서 가장 physics level이 높은 backend path는 이것입니다.

가장 정확한 표현은 아래입니다.

- asymptotic EM-oriented path generation
- PO/SBR 계열 scattering workflow
- low-fidelity path보다 더 높은 large-scene physical plausibility
- 그래도 full-wave solver는 아님

실무 해석:

- signal-chain physics: 강함
- antenna / polarization physics: 중간 이상
- propagation / scattering realism: 중간~상
- full-wave EM: 아님

관련 provider:

- [po_sbr_rt_provider.py](../src/avxsim/runtime_providers/po_sbr_rt_provider.py)

## 외부 설명에 쓸 때 가장 안전한 문장

가장 안전하고 정확한 제품 설명은 아래입니다.

```text
이 저장소는 hybrid FMCW radar simulation workbench이다.
backend abstraction, antenna handling, compensation layer, validation,
operator workflow 측면에서는 plain RadarSimPy보다 강하다.
하지만 아직 Ansys AVx급 real-time production radar platform은 아니다.
```

## 비교 요약 표

| 항목 | plain RadarSimPy | 우리 프로젝트 | Ansys AVx / Perceive EM |
| --- | --- | --- | --- |
| FMCW / DSP simulation | 강함 | 강함 | 강함 |
| backend 교체 가능성 | 제한적 | 강함 | 강함 |
| FFD / Jones handling | 제한적 | 있음 | product-level |
| compensation layer | 제한적 | 있음 | product-level |
| ray/path backend 선택지 | 제한적 | 있음 | 있음 |
| PO/SBR-style backend | 제한적 | 있음 | 강함 |
| stable validation / evidence workflow | 제한적 | 강함 | product workflow |
| real-time GPU production path | 제한적 | 아직 productized 아님 | 강함 |
| full-wave EM | 아님 | 아님 | 이 제품군 기준 보통 아님 |

## 현재 release 기준 실무 판단

현재 release cut 기준으로 가장 정확한 engineering judgment는 아래입니다.

1. 이 프로젝트는 hybrid workflow와 operator-facing validation 관점에서 plain `RadarSimPy`보다 이미 더 강하다.
2. 이 프로젝트는 아직 `Ansys AVx`와 동급의 production-scale real-time GPU sensor platform은 아니다.
3. 현재 physics level은 아래처럼 설명하는 것이 맞다.
   - `RadarSimPy + FFD`: low fidelity
   - `Sionna-style RT`: medium fidelity
   - `PO-SBR`: medium to higher fidelity
   - 전체적으로는 hybrid이며, full-wave는 아님

## 관련 문서

- [Graph Lab Low/High Fidelity 실행 흐름](339_graph_lab_low_high_fidelity_execution_flow_ko.md)
- [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md)
- [Release-Candidate Snapshot](291_release_candidate_snapshot_2026_03_08.md)
- [Generated Reports Index](reports/README.md)

