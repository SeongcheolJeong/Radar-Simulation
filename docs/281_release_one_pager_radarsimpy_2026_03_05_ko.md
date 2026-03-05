# 릴리즈 1페이지 요약 (외부 공유용)

- 일자: 2026년 3월 5일
- 범위: RadarSimPy 런타임 통합 + 프론트엔드 멀티플렉싱 제어 + 프로덕션 검증
- 상세 문서: `docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md`
- 영문 요약: `docs/280_release_one_pager_radarsimpy_2026_03_05.md`

## 핵심 결과

이번 릴리즈로 런타임 경로가 TDM 중심 동작에서 멀티플렉싱 인지 실행(`tdm`, `bpm`, `custom`)으로 확장되었고, 프론트엔드에서 해당 제어를 직접 노출했습니다. 또한 유료 6개월 라이선스 기준 프로덕션 검증 게이트를 모두 통과했습니다.

## 주요 제공 사항

1. 런타임 멀티플렉싱 일반화
- `radarsimpy_rt`가 멀티플렉싱 플랜을 해석하고 `pulse_amp`/`pulse_phs`를 TX 채널에 반영
- 런타임 진단 정보에 모드/플랜 출처/활성 TX 수/행렬 shape 기록

2. 프론트엔드 제어 및 검증 강화
- Graph Lab 런타임 입력 추가:
  - Multiplexing mode (`tdm|bpm|custom`)
  - BPM phase code
  - Multiplexing plan JSON
- 프리셋 버튼 추가:
  - `TDM`
  - `BPM 2TX`
  - `Custom`
- 입력 검증 강화:
  - 잘못된 모드 차단
  - BPM 비수치 토큰 차단
  - JSON 형식/객체 형식 검증
  - pulse 행렬 비수치 값 차단

3. LGIT 전용 출력 어댑터
- 전용 모듈 추가 및 출력 아티팩트 생성:
  - `lgit_customized_output.npz`
- Scene pipeline 및 Web summary 경로에 통합

4. 프로덕션 검증 자동화
- CI 템플릿 스크립트 추가:
  - `scripts/run_radarsimpy_paid_6m_gate_ci.sh`
- 런타임 오버라이드 계약 / LGIT 출력 스키마 검증 스크립트 추가

## 검증 상태 (이번 릴리즈)

주요 유료 런타임 검증 결과는 모두 green입니다.

- Production release gate: `ready`
  - `docs/reports/radarsimpy_production_release_gate_paid_6m.json`
- Readiness checkpoint: `ready`
  - `docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json`
- Simulator reference parity: `pass=true`
  - `docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json`
- Graph Lab Playwright E2E: `pass`
  - `docs/reports/graph_lab_playwright_e2e_latest.json`

## 운영 실행 조건

호스트에 RadarSimPy가 전역 설치되어 있지 않은 경우:

```bash
export PYTHONPATH=src:external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU
export LD_LIBRARY_PATH=external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export RADARSIMPY_LICENSE_FILE=/home/seongcheoljeong/Documents/license_RadarSimPy_10760.lic
scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

## 기대 효과

- 개발 생산성: 프리셋 + 검증 강화로 런타임 실험 속도 및 안정성 향상
- 통합 신뢰성: 모드 명시 제어와 리포트 기반 게이트로 parity 신뢰도 향상
- 배포 재현성: 단일 CI 스크립트로 프로덕션 검증 절차 재현 가능

