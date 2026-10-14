---
registry: DF-REG-REPLIT-FUSION-FACTORY-001
doc: replit-warehouse-design
status: draft
replit_execution: not_verified
---

# Replit 시각 부품 창고 설계 v0.1

설계만 있다. Replit 에서 아직 실행하지 않았다. 앱을 새로 만들면 비용이 들 수 있어 사람 승인 전에는 만들지 않는다.

## 기존 결정과 맞추기

새로 정하지 않고 이미 잠근 결정을 따른다.

- 노션 `REPLIT VISUAL COMMAND OS HANDOFF 2026-10-13`. Replit 은 실행 환경 후보, 비React 1순위는 SvelteKit + Svelte Flow, GitHub/Notion 이 정본, DB 는 교체 가능.
- 노션 `FM v2 · Remotion + KIE SAFE DOCK v0.1`. 생성 도구는 모두 교체 가능한 MACHINE LINE / ADAPTER. 상태 계약 `REQUESTED → ROUTED → GENERATING/EDITING → ASSET_READY → NORMALIZED → REVIEW_REQUIRED → APPROVED`.
- 노션 `DREAM OS 3.4 이후 개발 로드맵`. 기존 앱 ID 를 확보하기 전에는 Replit 앱을 새로 만들지 않는다.

이 창고는 위 Visual Command OS 의 왼쪽 패널 하나다. 별도 OS 를 만들지 않는다.

## 화면

```
┌──────────────────┬───────────────────────────┬──────────────────────┐
│ LEFT             │ CENTER                    │ RIGHT                │
│ GitHub 부품 창고  │ 조립 캔버스 / JOB 관제      │ 결과 / 증거           │
│                  │                           │                      │
│ [검색] [분류]     │  (원본 영상)──▶(VID-002     │ JOB DF-JOB-…          │
│ L1 ● L2 ● L3 ●   │   무음 삭제)──▶(VID-001     │ 상태: REVIEW_REQUIRED │
│                  │   9:16 + 자막)──▶(검수)     │ ▶ 미리보기 mp4         │
│ VID-001 MoviePy  │                           │ ffprobe 표            │
│  MIT · L2 · PASS │  [실행 요청] → Human Gate   │ sha256                │
│ CHR-003 InstantID│                           │ evidence JSON 링크     │
│  ⚠ 비상업 · 차단   │                           │ [승인] [반려]          │
└──────────────────┴───────────────────────────┴──────────────────────┘
```

LEFT. `parts-registry.json` 을 읽어 카드로 보인다. 카드 색은 LEVEL, 경고 아이콘은 `MODEL_WEIGHTS_LICENSE` 에 비상업 조건이 있을 때. `REJECTED_FOR_COMMERCIAL` 과 `BLOCKER` 는 캔버스로 끌어 놓을 수 없다.

CENTER. L2 이상 부품만 노드가 된다. 노드를 이으면 JOB 초안이 생긴다. 실행 버튼은 JOB 을 `REQUESTED` 로 만들 뿐이고, 유료 라인과 GPU 라인은 Human Gate 에서 멈춘다.

RIGHT. 결과 파일, ffprobe 값, 해시, evidence 링크를 보인다. 승인은 사람만 누른다. 승인은 발행이 아니다.

## 데이터

| 층 | 저장소 | 이유 |
|---|---|---|
| 부품 등록부 정본 | GitHub `parts-registry.json` | 다른 AI 가 raw 주소로 읽는다. 버전 기록이 남는다 |
| JOB / 이벤트 | Supabase (나중) | 거버넌스상 DATA/EVENTS. 지금은 설치하지 않는다 |
| 결정 / 기록 | Notion | 거버넌스상 KNOWLEDGE/DECISIONS |
| 결과 파일 | 외부 저장소 URL + sha256 | 큰 바이너리는 GitHub 에 커밋하지 않는다 |

## 부품 어댑터 계약

모든 부품은 같은 모양의 입력과 출력으로 감싼다. 부품을 바꿔도 캔버스와 증거 화면은 그대로다.

```json
{
  "job_id": "DF-JOB-VID-20261014-001",
  "part_id": "DF-PART-VID-001",
  "op": "video.reframe_shorts",
  "input": {"source_url": "…", "aspect": "9:16", "width": 540, "height": 960,
            "subtitles": [{"start": 1.5, "end": 5.0, "text": "…"}]},
  "cost_class": "free_cpu",
  "human_gate": false
}
```

```json
{
  "job_id": "DF-JOB-VID-20261014-001",
  "state": "ASSET_READY",
  "output": {"url": "…", "sha256": "…",
             "ffprobe": {"width": 540, "height": 960, "duration": 5.0}},
  "checks": {"resolution": true, "audio": true},
  "evidence_url": "…"
}
```

`cost_class` 가 `paid_api` 또는 `gpu` 이면 `human_gate` 는 반드시 true 다.

## 첫 조립 후보

`VID-002 auto-editor`(무음 삭제) → `VID-001 MoviePy`(9:16 + 자막) → 검수. 두 부품 모두 이 저장소의 시험 컨테이너에서 PASS 했다. CPU 만 쓰고 유료 API 가 없다.

FM 에 연결할 때는 FM 의 MEDIA JOB ROUTER 에 MACHINE LINE 하나로 붙인다. FM 코드는 바꾸지 않는다.

## Replit 에서 확인할 것

1. Python 환경에서 `pip install moviepy==2.2.1` 이 되는지, 동봉 ffmpeg 가 실행되는지.
2. 한글 글꼴 파일을 저장소에 넣을지, Nix 패키지로 받을지.
3. auto-editor 의 첫 실행 바이너리 다운로드가 Replit 네트워크에서 허용되는지.
4. 540x960 5초 렌더 시간. 시험 컨테이너에서는 원본 생성 포함 7.36초였다. Replit 수치는 실측 전까지 비워 둔다.
