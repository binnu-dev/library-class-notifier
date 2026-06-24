# competitors.md (v1, 16곳 / GM 제외)

> 렌즈 A — 경쟁사 동향의 앵커. 사람이 손으로 편집하는 단일 출처(source of truth).
> 여기서 표기를 바꾸면 `registry.py`의 별칭(alias)도 같이 손봐야 한다 (아래 "주의" 참고).

```
OEM:         현대·기아 / 토요타·혼다 / VW·Mercedes·BMW / Ford·Stellantis / 테슬라 / BYD·지리
서플라이어:  Bosch·Continental·ZF / Denso·Aisin / Mobileye·Nvidia / LG엔솔·삼성SDI·CATL / 현대모비스
제외:        GM (자사)
백로그:      Apple / Huawei / Xiaomi
주의:        법인명 표기 흔들림(Robert Bosch GmbH vs Bosch)은 구현 단계에서 정규화.
```

## 구현 메모

- 위 목록은 **사람이 읽는 앵커**다. BigQuery `assignee_harmonized.name`은 영문 법인명으로
  들어오므로, 실제 쿼리 매칭에 쓰는 영문 별칭은 `patent_landscape/registry.py`의
  `COMPETITORS`에 정의한다.
- "법인명 표기 흔들림" 정규화: 한 경쟁사가 여러 법인명(예: `Robert Bosch GmbH`,
  `Bosch Sensortec`, `Bosch`)으로 출원하므로, 별칭은 부분일치(LIKE/CONTAINS)로 매칭한다.
- 백로그(Apple / Huawei / Xiaomi)는 v1에서 쿼리하지 않는다. `registry.py`에서
  `backlog=True`로 표시만 해 둔다.
