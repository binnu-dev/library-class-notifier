# Patent Landscape (외부 특허 동향) — v1

매주 한 번, 외부 특허 신규 공개분을 두 렌즈로 훑어 **결정 가능한 brief 1장**을
이메일로 보낸다. 사람은 brief를 읽고 항목별로 "판다/버린다"만 고른다. 검색·랭킹·
요약은 전부 앞단에서 기계가 끝낸다.

> 범위: **외부 특허만.** 내부 발명신고/스크리닝은 범위 밖.
> 전체 스펙은 저장소 루트의 작업 설명(워크플로우 스펙) 참고.

## 두 렌즈

| | 렌즈 A — 경쟁사 동향 | 렌즈 B — 이종산업 차용 |
|---|---|---|
| 질문 | 경쟁사가 뭘 개발 중인가 | 다른 산업에 차용할 특허가 있나 |
| 방식 | assignee 리스트 직접 쿼리 (결정론적) | CPC 사전필터 → 문제문장↔abstract 임베딩 top-k |
| 앵커 | `anchors/competitors.md` | `anchors/problems.md` |

## 구조

```
patent_landscape/
  anchors/
    competitors.md     # 렌즈 A 앵커 (사람이 편집하는 source of truth)
    problems.md        # 렌즈 B 앵커 (P1~P8 + 이웃 산업)
  registry.py          # 앵커 → 쿼리 레이어 (assignee 별칭, 문제별 CPC/문장)
  config.py            # 환경변수 설정 + 공개일 윈도우 계산
  models.py            # Patent / BriefItem 레코드
  source.py            # PatentSource 프로토콜 + 테스트용 FakePatentSource
  bigquery_source.py   # Google Patents 공개셋(BigQuery) 구현 + 순수 쿼리 빌더
  embeddings.py        # 임베딩 백엔드 (sentence-transformers / hashing 폴백)
  lens_a.py            # 렌즈 A
  lens_b.py            # 렌즈 B
  scoring.py           # v1 점수 휴리스틱 + one-liner 추출
  brief.py             # 이메일 본문 렌더 (A-/B- ID 부여)
  email_delivery.py    # SMTP 발송
  pipeline.py          # source → 두 렌즈 → brief → 발송
  main.py              # 진입점 (주간 cron이 호출)
  tests/               # FakeSource + hashing 임베딩으로 E2E 테스트
```

`anchors/*.md`는 사람이 읽고 편집하는 앵커, `registry.py`는 그 앵커를 쿼리로
옮긴 운영 레이어다. 앵커를 고치면 `registry.py`도 같이 손본다.

## 데이터 소스

1차: **Google Patents BigQuery 공개셋** (`patents-public-data.patents.publications`).
보강(계획): USPTO·EPO 공식 API — `bigquery_source.py`의 seam으로만 박아 둠 (v1 미구현).

## 동작

```bash
# 의존성
pip install -r patent_landscape/requirements.txt

# 드라이런: 쿼리는 돌리되 이메일은 안 보내고 brief를 stdout에 출력
python -m patent_landscape.main --dry-run

# 정식 실행 (쿼리 + 이메일)
python -m patent_landscape.main
```

윈도우는 기본 직전 7일(어제까지). `--lookback-days N`으로 조정.

## 환경변수

| 변수 | 용도 |
|---|---|
| `GCP_PROJECT` | BigQuery 쿼리를 청구할 GCP 프로젝트 |
| `GOOGLE_APPLICATION_CREDENTIALS` | 서비스계정 키 파일 경로 |
| `EMBEDDING_BACKEND` | `auto`(기본) / `sentence-transformers` / `hashing` |
| `EMBEDDING_MODEL` | 기본 `sentence-transformers/all-MiniLM-L6-v2` |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` | 발송 SMTP |
| `EMAIL_FROM` `PATENT_EMAIL_TO` | 발신/수신(쉼표 구분) |
| `PATENT_LOOKBACK_DAYS` | 공개일 윈도우 길이(기본 7) |
| `PATENT_DRY_RUN` | `true`면 발송 생략 |
| `LENS_B_TOP_K` `LENS_B_MIN_SIMILARITY` `LENS_B_CANDIDATE_LIMIT` `LENS_A_LIMIT` | 렌즈 사이징 |

## 트리거

`.github/workflows/patent_landscape.yml` — 매주 수요일 00:00 UTC(=09:00 KST).
필요 시 `workflow_dispatch`로 수동 실행(드라이런 토글 제공).
테스트는 `patent_landscape_ci.yml`이 push/PR마다 hashing 백엔드로 빠르게 돌린다.

## 점수에 대하여 (v1)

brief의 "점수"는 **관련도 중심 휴리스틱**이다. 진짜 신규성(패밀리·인용·청구항)은
v2 딥다이브의 몫이라 여기선 계산하지 않는다 — `scoring.py` 주석 참고.

## 테스트

```bash
python -m pytest patent_landscape/tests -q
```

크리덴셜·모델 다운로드 없이 `FakePatentSource` + hashing 임베딩으로 전 구간을
검증한다.

## 백로그 (v2, 범위 밖)

- "판다 → 딥다이브" 자동 연결: 이메일 회신(`B-02 판다`)을 Power Automate
  Inbox/Outbox로 파싱 → 딥다이브 워크플로우 트리거. (항목 ID는 이미 그 용도로 박아둠.)
- GM 그룹 내부 동향 모니터링(별도 워크플로우).
- 빅테크 신규진입(Apple/Huawei/Xiaomi) 경쟁사 편입 — `registry.py`에 `backlog=True`로 대기.
- 문제 카탈로그 동적화, 인라인 결함 검출(구 P8) 복귀 검토.
