---
registry: DF-REG-REPLIT-FUSION-FACTORY-001
lot: DF-REPLIT-GITHUB-PARTS-FUSION-001
room: DREAM REPLIT PARTNERS FUSION FACTORY
status: draft
approved: false
created: 2026-10-14
sensitivity: none
---

# DREAM REPLIT PARTNERS FUSION FACTORY

GitHub 오픈소스를 부품으로 확인하고, 라이선스와 실행 증거가 있는 것만 Replit 조립 공장에 올리는 방이다.

이 폴더는 초안이다. 사람이 승인하기 전에는 `rooms/grok-knowledge-01/insights.json` 의 승인 페이퍼 목록에 올리지 않는다.

## 파일

| 파일 | 내용 |
|---|---|
| [radar-report-2026-10-14.md](radar-report-2026-10-14.md) | 첫 실행 보고. 기억 복구, 중복 제거, 발견 기술, 판정, HOLD |
| [parts-registry.json](parts-registry.json) | 부품 등록부. 부품 24개, 필수 필드 전부 |
| [replit-warehouse-design.md](replit-warehouse-design.md) | Replit 시각 부품 창고 설계. 화면, 데이터, 어댑터 계약 |
| [golden-test/moviepy_smoke.py](golden-test/moviepy_smoke.py) | 첫 GOLDEN TEST 스크립트 |
| [golden-test/evidence/](golden-test/evidence/) | 실행 증거 JSON 과 프레임 이미지 |
| [engines/compose-001/](engines/compose-001/) | DF-ENGINE-COMPOSE-001 영상 합성 엔진. 계약, 시험, 레드팀, 증거 |
| [studios/character-m40/](studios/character-m40/) | M40 캐릭터 스튜디오 설계, 스키마, 얼굴 일관성 평가기 |

## 판정 규칙

- L1 DISCOVERED. GitHub 원본과 라이선스 원문을 읽었다.
- L2 VERIFIED. 실제로 실행했고 증거 파일이 있다.
- L3 PRODUCTION READY. DREAM 시스템에 연결해 정상 작동했다. 지금은 0개다.

발견은 설치가 아니다. 설치는 연동이 아니다. 시험하지 않은 기능은 PASS 가 아니다.

코드 라이선스와 모델 가중치 라이선스는 따로 적는다. Stars 는 품질의 근거가 아니다. README 의 주장은 실행 PASS 가 아니다.

## 금지

- 기존 FM v2 / FM v3 백로그, MULTI-6 SLIM SAFE DOCK 수정
- 검증되지 않은 기술 자동 설치
- 라이선스를 확인하지 않은 모델의 상업 사용
- 사용자 승인 없는 유료 작업, Replit 앱 생성, GPU 사용
- 사용자 승인 없는 SNS 발행
- 가짜 PASS, 가짜 실행 결과, 근거 없는 성능 수치

## 시험 다시 돌리기

```
python3 -m venv .venv
.venv/bin/pip install moviepy==2.2.1 auto-editor==29.3.1
.venv/bin/python factory/replit-fusion/golden-test/moviepy_smoke.py /tmp/gt-out
```

한국어 자막에는 한글 글꼴 경로가 필요하다. 기본값은 `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc` 이고, 두 번째 인자로 바꿀 수 있다.
