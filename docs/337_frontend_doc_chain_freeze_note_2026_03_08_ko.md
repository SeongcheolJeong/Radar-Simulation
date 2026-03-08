# Frontend 문서 체인 Freeze Note

- 날짜: 2026년 3월 8일
- 상태: 현재 frontend/operator release cut에 대해 active

## 목적

이 문서는 현재 frontend 문서와 evidence-routing 체인을 freeze해서, 이후 업데이트가 새 overview 문서를 계속 늘리는 방향이 아니라 evidence refresh, UI 동작 변경, troubleshooting 정확도 유지에 집중되도록 하기 위한 문서입니다.

같은 컷에 대해 병렬 frontend overview 문서를 계속 추가하지 마십시오.

## 현재 canonical frontend 문서 체인

다음 순서로 사용합니다.

1. [Frontend 문서 맵](329_frontend_doc_map_ko.md)
2. [Frontend Evidence 맵](333_frontend_evidence_map_ko.md)
3. [역할별 Frontend Evidence 읽기 순서](335_frontend_evidence_read_order_by_role_ko.md)
4. [Frontend 트러블슈팅 맵](331_frontend_troubleshooting_map_ko.md)
5. [Generated Reports Index](reports/README.md)

그 다음에 UI별 분기로 들어갑니다.

- `Graph Lab`: [Graph Lab 문서 맵](323_graph_lab_doc_map_ko.md)
- `classic dashboard`: [Classic Dashboard 문서 맵](321_classic_dashboard_doc_map_ko.md)

## 기본 유지 규칙

아래 update trigger가 없는 한, 이 컷에 대해 새로운 frontend summary/routing 문서를 추가하지 마십시오.

대신 다음을 우선합니다.

- frontend evidence refresh
- 기존 frontend map/guide 수정
- freeze된 체인 내부의 링크, routing, wording 수정
- UI 동작이 실제로 바뀐 경우에만 UI별 manual 갱신

## 업데이트를 허용하는 조건

다음 중 하나일 때만 frozen frontend chain을 수정합니다.

- `Graph Lab` operator flow가 의미 있게 바뀌었을 때
- `classic dashboard` flow가 의미 있게 바뀌었을 때
- stable frontend evidence set이 바뀌었을 때
- high-fidelity interactive frontend story가 바뀌었을 때
- troubleshooting decision path가 바뀌었을 때
- 현재 frozen chain 문서 중 하나가 오해를 유발하거나 stale해졌을 때

## 업데이트 조건이 아닌 것

다음 이유만으로는 새로운 frontend overview 문서를 만들지 마십시오.

- wording만 다른 변형
- 같은 routing 의미를 가진 alternate summary
- frozen chain 밖의 중복 EN/KO overview 페이지
- operator 판단을 바꾸지 않는 작은 재배치

## Operator 규칙

현재 컷에서는:

- 위 frozen chain부터 시작하고
- explanation을 추가하기 전에 evidence를 refresh하며
- 긴 manual보다 `_latest.json`과 `latest/` snapshot을 먼저 보고
- UI story 또는 evidence story가 실제로 바뀐 경우에만 chain을 다시 엽니다
