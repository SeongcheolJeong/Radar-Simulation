# 정식 검증 시나리오 팩

## 목적

이 문서는 release-candidate 마감 전에 고정 순서로 실행할 검증 시나리오 팩을 정의합니다.

이 팩으로 아래 네 가지 질문에 답합니다.

1. frontend/operator 워크플로우가 아직 정상인가?
2. low-fidelity RadarSimPy 경로가 아직 정상인가?
3. high-fidelity backend 계약/패리티가 아직 정상인가?
4. paid RadarSimPy production 경로가 end-to-end로 아직 정상인가?

- 영문 원본: [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md)

원클릭 실행:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

## 사용 규칙

- 저장소 루트에서 실행합니다.
- `PYTHONPATH=src`를 유지합니다.
- 실제로 설치된 runtime만 포함하는 subset을 선택합니다.
- 가능하면 아래 출력 경로를 그대로 사용합니다.
- 결과 해석은 [Generated Reports Index](reports/README.md)를 기준으로 합니다.

## 시나리오 매트릭스

| 시나리오 ID | 목적 | 최소 전제 조건 | 주요 명령 | 지속 evidence |
| --- | --- | --- | --- | --- |
| `FE-1` | Graph Lab 브라우저/operator flow | `.venv`, Playwright browsers | `scripts/validate_graph_lab_playwright_e2e.py` | `graph_lab_playwright_e2e_latest.json`, `graph_lab_playwright_snapshots/latest/`, `frontend_quickstart_v1.json` |
| `FE-2` | frontend runtime payload -> provider info contract | `.venv`, local RadarSimPy runtime assets | `scripts/validate_frontend_runtime_payload_provider_info_optional.py --require-runtime` | `frontend_runtime_payload_provider_info_optional_latest.json` |
| `RS-1` | trial-runtime layered parity | `.venv`, RadarSimPy trial bundle | `scripts/run_radarsimpy_layered_parity_suite.py --require-runtime-trial` | `radarsimpy_layered_parity_suite_trial_latest.json`, `radarsimpy_layered_parity_trial_latest.json` |
| `HF-1` | Sionna-style RT parity contract | `.venv` 또는 `.venv-sionna311` | `scripts/run_scene_backend_parity_sionna_rt.py` | `scene_backend_parity_sionna_rt_latest.json` |
| `HF-2` | PO-SBR parity/readiness path | `.venv` 또는 `.venv-po-sbr` | `scripts/run_scene_backend_parity_po_sbr_rt.py`, `scripts/run_po_sbr_post_change_gate.py --strict` | `scene_backend_parity_po_sbr_rt_latest.json`, `po_sbr_post_change_gate_*.json`, 선택적으로 `po_sbr_progress_snapshot_manual.json` |
| `RS-2` | paid RadarSimPy production closure | `.venv`, paid `.lic`, runtime bundle | `scripts/run_radarsimpy_paid_6m_gate_ci.sh` | `radarsimpy_*_paid_6m.json`, `frontend_runtime_payload_provider_info_paid_6m.json` |

## 권장 실행 순서

아래 순서로 실행합니다.

1. `FE-1`
2. `FE-2`
3. `RS-1`
4. `HF-1`
5. `HF-2`
6. `RS-2`

이 순서는 가볍고 신호가 큰 검증에서 시작해, 무거운 runtime/paid-license 검증으로 올라가는 구조입니다.

## 시나리오별 상세

### FE-1: Graph Lab 브라우저 흐름

다음에 사용합니다.

- `frontend/graph_lab`를 변경했을 때
- web/API orchestration을 변경했을 때
- API health만이 아니라 실제 operator 수준 신뢰도가 필요할 때

실행:

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python \
  scripts/validate_graph_lab_playwright_e2e.py \
  --require-playwright \
  --output-json docs/reports/graph_lab_playwright_e2e_latest.json
```

기대 evidence:

- `docs/reports/graph_lab_playwright_e2e_latest.json`
- `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`
- `docs/reports/graph_lab_playwright_snapshots/latest/page_full.png`

pass 의미:

- 브라우저 flow가 아직 동작한다.
- compare workflow가 아직 렌더링된다.
- exported decision brief가 live UI 상태와 아직 일치한다.

### FE-2: Frontend Runtime Contract

다음에 사용합니다.

- runtime preset wiring을 변경했을 때
- multiplexing/BPM/custom payload generation을 변경했을 때
- frontend intent가 `radarsimpy_rt` provider info까지 도달하는지 증명이 필요할 때

실행:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/validate_frontend_runtime_payload_provider_info_optional.py \
  --require-runtime \
  --output-json docs/reports/frontend_runtime_payload_provider_info_optional_latest.json
```

기대 evidence:

- `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

pass 의미:

- frontend `tdm`, `bpm`, `custom` 입력이 provider 쪽 multiplexing field로 예상대로 매핑된다.

### RS-1: Trial Runtime Layered Parity

다음에 사용합니다.

- RadarSimPy wrapper/runtime coupling을 변경했을 때
- white-box vs black-box 비교 로직을 변경했을 때
- paid path 전에 가장 싼 runtime-backed parity 확인이 필요할 때

실행:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/run_radarsimpy_layered_parity_suite.py \
  --output-json docs/reports/radarsimpy_layered_parity_suite_trial_latest.json \
  --trial-output-json docs/reports/radarsimpy_layered_parity_trial_latest.json \
  --require-runtime-trial
```

기대 evidence:

- `docs/reports/radarsimpy_layered_parity_suite_trial_latest.json`
- `docs/reports/radarsimpy_layered_parity_trial_latest.json`

pass 의미:

- trial-runtime white-box vs RadarSimPy black-box layered parity가 유지된다.
- 저장소가 paid-only 기능 없이 local trial bundle을 계속 사용할 수 있다.

### HF-1: Sionna-Style RT Parity Contract

다음에 사용합니다.

- `sionna_rt` backend handling을 변경했을 때
- scene-backend parity logic을 변경했을 때
- Sionna-style 경로의 deterministic candidate-vs-reference parity가 필요할 때

실행:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/run_scene_backend_parity_sionna_rt.py \
  --output-json docs/reports/scene_backend_parity_sionna_rt_latest.json
```

기대 evidence:

- `docs/reports/scene_backend_parity_sionna_rt_latest.json`

pass 의미:

- analytic reference scene과 `sionna_rt` candidate scene이 현재 parity contract를 계속 만족한다.

### HF-2: PO-SBR Parity And Readiness

다음에 사용합니다.

- `po_sbr_rt` backend handling을 변경했을 때
- runtime-affecting PO-SBR 코드를 변경했을 때
- candidate-vs-reference parity와 readiness/closure 상태가 둘 다 필요할 때

실행:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/run_scene_backend_parity_po_sbr_rt.py \
  --output-json docs/reports/scene_backend_parity_po_sbr_rt_latest.json
PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --strict
PYTHONPATH=src .venv/bin/python \
  scripts/show_po_sbr_progress.py \
  --strict-ready \
  --output-json docs/reports/po_sbr_progress_snapshot_manual.json
```

기대 evidence:

- `docs/reports/scene_backend_parity_po_sbr_rt_latest.json`
- `docs/reports/po_sbr_progress_snapshot_manual.json`
- 최신 `docs/reports/po_sbr_post_change_gate_*.json`

pass 의미:

- PO-SBR candidate scene이 analytic-reference parity contract를 계속 만족한다.
- runtime-affecting readiness gate가 계속 green이다.
- 현재 closure/progress 상태가 계속 ready다.

### RS-2: Paid RadarSimPy Production Closure

다음에 사용합니다.

- release-facing RadarSimPy evidence가 필요할 때
- paid `.lic`와 runtime asset이 준비되어 있을 때
- trial path가 아니라 production path를 마감할 때

실행:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

기대 evidence:

- `docs/reports/radarsimpy_production_release_gate_paid_6m.json`
- `docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json`
- `docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json`
- `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json`

pass 의미:

- production gate, readiness, simulator reference parity, frontend/provider contract가 paid runtime path 기준으로 모두 통과한다.

## 최소 subset

### Base frontend/operator subset

실행:

- `FE-1`

용도:

- operator/browser confidence만 필요할 때

### Low-fidelity runtime subset

실행:

- `FE-1`
- `FE-2`
- `RS-1`

용도:

- frontend + RadarSimPy trial path 신뢰도만 필요할 때

### High-fidelity contract subset

실행:

- `HF-1`
- `HF-2`

용도:

- scene backend나 ray-tracing 인접 로직을 바꿨을 때

### Release-candidate subset

실행:

- `FE-1`
- `FE-2`
- `RS-1`
- `HF-2`
- `RS-2`

`HF-1`은 Sionna-style 경로가 이번 release story에 실제 포함될 때만 추가합니다.

위 원클릭 runner는 기본적으로 이 subset을 실행하고, `--with-sionna`를 주면 `HF-1`도 포함합니다.

## 현재 남은 gap

남은 핵심은 시나리오 정의나 runner wiring이 아니라 release freeze입니다.

- release-candidate subset을 기본 closure path로 계속 green 유지
- `HF-1`을 default release story에 필수로 포함할지 최종 결정
- refreshed stable reports 기준으로 release-candidate snapshot을 확정
