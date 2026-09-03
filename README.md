# 테크 블로그 AI 클리핑

국내 주요 테크 기업 기술 블로그에서 **AI 관련 글만** 자동으로 모아 보여주는 사이트.

🔗 **https://fromslow.github.io/tech-blog-ai-clip/**

## 수집 대상
토스 · 쏘카 · 배달의민족 · 당근 · 카카오 · 네이버 · 라인 · 뱅크샐러드 · 컬리 · 무신사 · 하이퍼커넥트 · 쿠팡 · 여기어때 · NHN

## 특징
- RSS·API로 수집 → AI/ML 글만 필터링
- 최근 1년치부터 계속 누적 (삭제 없음)
- 기업 · 태그 · 검색 필터, 다크 / 라이트 모드
- 대표 이미지 자동 저장, 매일 자동 수집 → 자동 배포

## 새로고침
```bash
pip install -r requirements.txt
python fetch_feeds.py
```

## 구조
| 파일 | 설명 |
|------|------|
| `index.html` | 웹사이트 |
| `fetch_feeds.py` | 수집 · AI 필터 · 이미지 저장 |
| `data.js` | 수집된 글 데이터 (자동 생성) |
| `thumbs/` · `logos/` | 썸네일 · 로고 |
