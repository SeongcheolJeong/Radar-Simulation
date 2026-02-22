# Radar Simulation 중간결과 보고서 (팀 공유용)

- 작성일: 2026-02-22
- 저장소: `/Users/seongcheoljeong/Documents/Codex_test`
- 기준 브랜치: `codex/hybrid-adapter-real-parser`
- 중간목표: AVX 유사 오프라인 파이프라인(`Object Scene -> Path List + Raw ADC Cube -> Radar Map`)의 구현/검증 상태 공유

## 1) Executive Summary

| 항목 | 상태 |
|---|---|
| 전체 마일스톤 진행률 | **77 / 78 완료 (98.7%)** |
| 미완료 항목 | **M14.6**: `po-sbr` 런타임 파일럿(리눅스+NVIDIA) |
| 자동 검증 로그 | **pass 175 / fail 0** |
| 현재 핵심 출력 | `path_list.json`, `adc_cube.npz`, `radar_map.npz` |
| macOS 런타임 상태 | `sionna_rt_full_runtime: ready`, `po_sbr_runtime: blocked` |

근거 문서:
- `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/validation_log.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_5_2026_02_22.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_2026_02_22.json`

## 2) 목표 대비 구현 상태 (AVX 유사 관점)

| 목표 기능 | 상태 | 비고/근거 |
|---|---|---|
| Propagation Path List 출력 | 완료 | `path_id/material_tag/reflection_order/pol` 확장 포함 (M11.3) |
| Raw ADC 4D 출력(`sample, chirp, tx, rx`) | 완료 | TDM 스케줄/안테나/복소합성 경로 고정 |
| RD/RA 맵 생성 | 완료 | `radar_map.npz`로 저장, parity 지표 포함 |
| HybridDynamicRT 참조 파이프라인 | 완료 | 프레임 ingest + Python 재구현(p-code wave1/2) 완료 |
| .ffd + Jones 편파 흐름 | 완료 | parser/interpolation/calibration까지 구현 |
| Object scene 기반 실행 | 완료 | scene json -> canonical output E2E 통과 |
| Sionna RT 런타임 연동 | 완료(macOS) | `sionna.rt` import 및 runtime provider 실행 검증 |
| PO-SBR 런타임 연동 | 부분완료 | 어댑터/스텁/게이트는 완료, **실행 증적은 Linux+NVIDIA 필요** |

## 3) 이번 중간 데모 입력 조건

데모 파일:
- Scene: `/Users/seongcheoljeong/Documents/Codex_test/data/demo/avx_like_showcase_2026_02_22/scene_avx_like_runtime.json`
- 요약 리포트(JSON): `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/avx_like_showcase_macos_2026_02_22.json`

### Radar/배열 설정

| 항목 | 값 |
|---|---|
| Carrier | 77 GHz |
| Chirp slope | 20e12 Hz/s |
| Sampling | 20 MHz, 1024 samples/chirp |
| Chirp 수 | 16 |
| TDM Tx 스케줄 | `[0,1,0,1,...]` |
| Tx/Rx | 2 Tx, 4 Rx |
| RD FFT / RA FFT | 64 / 32 |
| Range bin limit | 256 |

### 객체(시뮬레이션 타겟)

| 타겟 | 위치 (m) | 속도 (m/s) | 특성 |
|---|---|---|---|
| Static sphere | `[24.0, 2.5, 0.0]` | `[0, 0, 0]` | 강한 정지 반사체 |
| Moving sphere | `[36.0, -1.5, 0.0]` | `[-8, 0, 0]` | 약한 이동 반사체 |

## 4) 정량 결과 요약

### 출력 아티팩트 요약

| 출력 | 결과 |
|---|---|
| Path list | 16 chirp, 총 32 paths(각 chirp당 2개) |
| ADC cube | shape=`[1024, 16, 2, 4]`, dtype=`complex64` |
| RD map | shape=`[64, 256]` |
| RA map | shape=`[32, 256]` |

### 경로 기반 기대값 vs 관측값 (데모 프레임 0 기준)

| 항목 | 기대값 | 관측값(로컬 최대) | 오차 |
|---|---:|---:|---:|
| Static target range | 23.5299 m | 23.5677 m (bin 161) | +0.0378 m |
| Static target Doppler | 0.0 Hz | 0.0 Hz (bin 32) | 0.0 Hz |
| Moving target range | 35.2312 m | 35.1319 m (bin 240) | -0.0993 m |
| Moving target Doppler | -4105.95 Hz | -3906.25 Hz (bin 22) | +199.70 Hz (~4.86%) |
| Moving target 상대세기 | - | RD 상 정점 대비 **-46.28 dB** | - |

해석:
- 강한 정지 타겟은 기대치와 매우 근접하게 재현됨.
- 이동 타겟도 기대 bin 근방에서 검출되지만, 동적 범위가 커서(정지 타겟 대비 약함) 시각적으로는 약하게 보임.
- 현재 품질은 “파이프라인 유효성/기초 물리 일관성” 검증에는 충분하고, 고정밀 산란 품질은 PO-SBR 런타임/파라미터 튜닝이 남아 있음.

## 5) 첨부 결과물 (시각화)

### Range-Doppler Map

![RD Map](../data/demo/avx_like_showcase_2026_02_22/visuals/rd_map.png)

### Range-Angle Map

![RA Map](../data/demo/avx_like_showcase_2026_02_22/visuals/ra_map.png)

### ADC Magnitude (Tx0-Rx0)

![ADC Tx0 Rx0](../data/demo/avx_like_showcase_2026_02_22/visuals/adc_tx0_rx0.png)

### Path Scatter (Chirp 0)

![Path Scatter Chirp0](../data/demo/avx_like_showcase_2026_02_22/visuals/path_scatter_chirp0.png)

## 6) 오픈소스 레퍼런스 반영 현황

| 레퍼런스 | 반영 상태 | 비고 |
|---|---|---|
| HybridDynamicRT | 높음 | MATLAB `.p` 의존 없이 Python 재구현 경로 구축 완료 |
| Sionna RT | 높음 | 런타임 provider 연동 + macOS 실행 검증 완료 |
| PO-SBR-Python | 중간 | adapter/stub/검증/런북 완료, Linux 실실행만 미완료 |
| RadarSimPy | 중간 | periodic parity-lock 자동화로 회귀감시 용도 반영 |

## 7) 리스크 및 남은 일

| 항목 | 현재 상태 | 영향도 | 대응 |
|---|---|---|---|
| M14.6 Linux 실행증적 부재 | 미완료 | 산란 고충실도 claim 제한 | Linux+NVIDIA에서 strict pilot 실행 및 리포트 고정 |
| 이동 타겟 가시성(동적 범위) | 정지 타겟 대비 약함 | 데모 시 해석 난이도 증가 | 장면별 amplitude scaling/AGC형 시각화 옵션 추가 |
| 실측 기반 최종 lock 일반화 | 부분완료 | 시나리오별 편차 존재 | 시나리오군 확장 후 family lock 정책 유지 |

## 8) 다음 단계 (우선순위)

1. **M14.6 종료**: Linux+NVIDIA에서 `po_sbr` strict pilot 실행(`pilot_status=executed`) 및 closure readiness true화.
2. **데모 품질 개선**: moving target visibility를 위한 map-level scaling 옵션(보고용)과 타겟별 annotation 자동화.
3. **팀 사용성 패키징**: `scene json 1개`로 `path/adc/rd/ra/report`까지 생성하는 one-command report 스크립트 추가.
4. **최종 평가 준비**: AVX 목표 출력 관점의 acceptance matrix(필수/권장) 확정 및 회귀 체크리스트 동결.

---

### 부록: 주요 근거 파일

- `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/validation_log.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/07_reference_repo_strategy.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/avx_like_showcase_macos_2026_02_22.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_5_2026_02_22.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_2026_02_22.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_2026_02_22.json`
