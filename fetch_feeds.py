#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테크 블로그 AI 클리핑 - 누적형 피드 수집기
=========================================
국내 주요 테크 기업 기술 블로그에서 AI/ML 관련 글을 모아, 최근 1년치를
계속 누적(accumulate)한다. 실행할 때마다:

  1. 각 소스에서 최신 글을 가져온다 (RSS / WordPress API / D2 API)
  2. AI 관련 글만 필터링한다
  3. 기존 data.json 과 병합(merge) 하고 URL로 중복 제거한다
  4. 발행일이 1년(365일) 지난 글은 제거해 롤링 윈도우를 유지한다
  5. data.js / data.json 으로 저장한다

→ 매일/매주 실행하면 데이터가 자연스럽게 쌓여 최근 1년 AI 아카이브가 된다.
   (배민·네이버는 API로 과거 1년치를 즉시 백필한다.)

WAF(배민 등)를 통과하기 위해 curl_cffi 로 크롬 TLS 지문을 위장한다.

사용법:  python fetch_feeds.py
"""

import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import feedparser

try:
    from curl_cffi import requests as creq
except ImportError:  # pragma: no cover
    print("curl_cffi 가 필요합니다:  pip install -r requirements.txt", file=sys.stderr)
    raise

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

HERE = Path(__file__).resolve().parent
THUMBS_DIR = HERE / "thumbs"
WINDOW_DAYS = 365
NOW = datetime.now(timezone.utc)
CUTOFF = NOW - timedelta(days=WINDOW_DAYS)

# ---------------------------------------------------------------------------
# 수집 대상.  type: rss | wordpress | d2
# ---------------------------------------------------------------------------
SOURCES = [
    {"id": "toss", "name": "토스", "color": "#3182F6", "home": "https://toss.tech",
     "type": "rss", "feed": "https://toss.tech/rss.xml"},
    {"id": "socar", "name": "쏘카", "color": "#00A0E9", "home": "https://tech.socarcorp.kr",
     "type": "rss", "feed": "https://tech.socarcorp.kr/rss.xml"},
    {"id": "woowahan", "name": "배달의민족", "color": "#2AC1BC", "home": "https://techblog.woowahan.com",
     "type": "wordpress", "api": "https://techblog.woowahan.com/wp-json/wp/v2/posts"},
    {"id": "daangn", "name": "당근", "color": "#FF6F0F", "home": "https://medium.com/daangn",
     "type": "rss", "feed": "https://medium.com/feed/daangn"},
    {"id": "kakao", "name": "카카오", "color": "#FFB900", "home": "https://tech.kakao.com",
     "type": "rss", "feed": "https://tech.kakao.com/feed/"},
    {"id": "naver", "name": "네이버", "color": "#03C75A", "home": "https://d2.naver.com",
     "type": "d2", "api": "https://d2.naver.com/api/v1/contents"},
    {"id": "line", "name": "라인", "color": "#06C755", "home": "https://techblog.lycorp.co.jp/ko",
     "type": "rss", "feed": "https://techblog.lycorp.co.jp/ko/feed/index.xml"},
    {"id": "banksalad", "name": "뱅크샐러드", "color": "#536DFE", "home": "https://blog.banksalad.com",
     "type": "rss", "feed": "https://blog.banksalad.com/rss.xml"},
    {"id": "kurly", "name": "컬리", "color": "#5F0080", "home": "https://helloworld.kurly.com",
     "type": "rss", "feed": "https://helloworld.kurly.com/rss.xml"},
    {"id": "musinsa", "name": "무신사", "color": "#1A1A1A", "home": "https://medium.com/musinsa-tech",
     "type": "rss", "feed": "https://medium.com/feed/musinsa-tech"},
    {"id": "hyperconnect", "name": "하이퍼커넥트", "color": "#8B5CF6", "home": "https://hyperconnect.github.io",
     "type": "rss", "feed": "https://hyperconnect.github.io/feed.xml"},
    {"id": "coupang", "name": "쿠팡", "color": "#E4002B", "home": "https://medium.com/coupang-engineering",
     "type": "rss", "feed": "https://medium.com/feed/coupang-engineering"},
    {"id": "gccompany", "name": "여기어때", "color": "#FF3D77", "home": "https://techblog.gccompany.co.kr",
     "type": "rss", "feed": "https://techblog.gccompany.co.kr/feed"},
    {"id": "nhn", "name": "NHN", "color": "#0E9AA7", "home": "https://meetup.nhncloud.com",
     "type": "rss", "feed": "https://meetup.nhncloud.com/rss"},
    {"id": "myrealtrip", "name": "마이리얼트립", "color": "#00C2B8", "home": "https://medium.com/myrealtrip-product",
     "type": "rss", "feed": "https://medium.com/feed/myrealtrip-product"},
    {"id": "devocean", "name": "데보션", "color": "#5C7CFA", "home": "https://devocean.sk.com",
     "type": "rss", "feed": "https://devocean.sk.com/blog/rss.do"},
]

# ---------------------------------------------------------------------------
# AI/ML 판별 키워드
# ---------------------------------------------------------------------------
ACRONYMS = [
    "AI", "ML", "LLM", "LLMs", "sLLM", "GPT", "RAG", "NLP", "OCR", "STT", "TTS",
    "MLOps", "GenAI", "RLHF", "LoRA", "GAN", "CNN", "RNN", "BERT", "VLM", "ASR", "MCP",
]
PHRASES = [
    "인공지능", "머신러닝", "딥러닝", "machine learning", "deep learning",
    "생성형", "generative", "언어 모델", "언어모델", "language model",
    "임베딩", "embedding", "벡터 검색", "벡터db", "vector search", "vector db", "vectordb",
    "추천 시스템", "추천시스템", "recommendation", "recommender",
    "자연어", "챗봇", "chatbot", "프롬프트", "prompt engineering", "프롬프트 엔지니어링",
    "transformer", "트랜스포머", "파인튜닝", "fine-tun", "파운데이션 모델", "foundation model",
    "diffusion", "확산 모델", "ai 에이전트", "ai에이전트", "ai agent", "copilot",
    "langchain", "랭체인", "llamaindex", "hugging face", "허깅페이스",
    "예측 모델", "이상 탐지", "anomaly detection", "음성 인식", "음성인식", "speech recognition",
    "이미지 생성", "image generation", "데이터 사이언스", "data science",
    "feature store", "model serving", "모델 서빙", "pytorch", "파이토치", "tensorflow", "텐서플로",
    "초거대", "온디바이스", "gemini", "chatgpt", "claude", "검색 증강", "retrieval augmented",
    "멀티모달", "multimodal", "강화학습", "reinforcement learning",
    "컴퓨터 비전", "컴퓨터비전", "computer vision", "시맨틱 검색", "semantic search",
    "생성 ai", "생성형 ai", "초개인화", "지능형",
]
TAG_LABEL = {
    "ai": "AI", "인공지능": "AI", "지능형": "AI",
    "생성형": "생성형 AI", "generative": "생성형 AI", "생성 ai": "생성형 AI", "생성형 ai": "생성형 AI", "genai": "생성형 AI",
    "llm": "LLM", "llms": "LLM", "sllm": "LLM", "언어 모델": "LLM", "언어모델": "LLM", "language model": "LLM", "gpt": "LLM",
    "chatgpt": "LLM", "gemini": "LLM", "claude": "LLM", "bert": "LLM", "초거대": "LLM",
    "머신러닝": "머신러닝", "machine learning": "머신러닝", "ml": "머신러닝",
    "딥러닝": "딥러닝", "deep learning": "딥러닝", "cnn": "딥러닝", "rnn": "딥러닝", "transformer": "딥러닝", "트랜스포머": "딥러닝",
    "rag": "RAG", "검색 증강": "RAG", "retrieval augmented": "RAG",
    "임베딩": "임베딩", "embedding": "임베딩", "벡터 검색": "임베딩", "vector search": "임베딩",
    "vector db": "임베딩", "vectordb": "임베딩", "벡터db": "임베딩", "시맨틱 검색": "임베딩", "semantic search": "임베딩",
    "추천 시스템": "추천", "추천시스템": "추천", "recommendation": "추천", "recommender": "추천",
    "자연어": "자연어처리", "nlp": "자연어처리", "챗봇": "챗봇", "chatbot": "챗봇",
    "컴퓨터 비전": "컴퓨터비전", "컴퓨터비전": "컴퓨터비전", "computer vision": "컴퓨터비전", "vlm": "컴퓨터비전",
    "ocr": "컴퓨터비전", "이미지 생성": "이미지생성", "image generation": "이미지생성", "diffusion": "이미지생성",
    "음성 인식": "음성", "음성인식": "음성", "speech recognition": "음성", "stt": "음성", "tts": "음성", "asr": "음성",
    "mlops": "MLOps", "model serving": "MLOps", "모델 서빙": "MLOps", "feature store": "MLOps",
    "ai 에이전트": "AI 에이전트", "ai에이전트": "AI 에이전트", "ai agent": "AI 에이전트", "copilot": "AI 에이전트",
    "langchain": "AI 에이전트", "랭체인": "AI 에이전트", "mcp": "AI 에이전트",
    "프롬프트": "프롬프트", "prompt engineering": "프롬프트", "프롬프트 엔지니어링": "프롬프트",
    "파인튜닝": "파인튜닝", "fine-tun": "파인튜닝", "lora": "파인튜닝", "rlhf": "파인튜닝",
    "멀티모달": "멀티모달", "multimodal": "멀티모달", "강화학습": "강화학습", "reinforcement learning": "강화학습",
    "예측 모델": "예측/데이터", "이상 탐지": "예측/데이터", "anomaly detection": "예측/데이터",
    "데이터 사이언스": "예측/데이터", "data science": "예측/데이터",
    "pytorch": "프레임워크", "파이토치": "프레임워크", "tensorflow": "프레임워크", "텐서플로": "프레임워크",
    "온디바이스": "온디바이스 AI", "초개인화": "초개인화",
    "파운데이션 모델": "파운데이션 모델", "foundation model": "파운데이션 모델",
}
ACRONYM_RE = re.compile(r"\b(" + "|".join(sorted(ACRONYMS, key=len, reverse=True)) + r")\b", re.I)


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------
def http_get(url: str):
    return creq.get(url, impersonate="chrome", timeout=30,
                    headers={"Accept": "application/rss+xml, application/json, application/xml, text/xml, */*",
                             "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"})


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"The post .*? (first )?appeared.*$", "", text)  # WP RSS 꼬리말 제거
    return re.sub(r"\s+", " ", text).strip()


def first_image_from_html(*blobs) -> str:
    for blob in blobs:
        if not blob:
            continue
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', blob, re.I)
        if m:
            return m.group(1)
    return ""


def match_ai(text: str):
    """AI 관련이면 표시 태그 리스트(중복 제거)를 반환, 아니면 None."""
    low = text.lower()
    hits = [m.lower() for m in ACRONYM_RE.findall(text)]
    hits += [p for p in PHRASES if p.lower() in low]
    if not hits:
        return None
    labels = []
    for h in hits:
        label = TAG_LABEL.get(h)
        if label and label not in labels:
            labels.append(label)
    return labels or ["AI"]


def make_post(src, title, url, iso_date, summary, author="", tags_text="", image=""):
    """정규화 + AI 필터.  통과하면 dict, 아니면 None."""
    title = strip_html(title)
    summary = strip_html(summary)
    labels = match_ai(f"{title}\n{tags_text}\n{summary[:500]}")
    if not labels:
        return None
    return {
        "source": src["id"], "sourceName": src["name"], "color": src["color"],
        "title": title, "url": url, "date": iso_date,
        "summary": summary[:280], "author": strip_html(author),
        "tags": labels[:4], "image": image or "",
    }


def within_window(iso_date: str) -> bool:
    if not iso_date:
        return False
    try:
        d = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    except ValueError:
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d >= CUTOFF


_OG_RE = [
    re.compile(r'<meta[^>]+property=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)', re.I),
]


def fetch_og_image(url: str) -> str:
    """글 페이지에서 대표 이미지(og:image / twitter:image)를 추출한다."""
    try:
        r = http_get(url)
        html_text = r.text[:250000]  # 일부 사이트(카카오 등)는 head 가 커서 넉넉히 스캔
        for rx in _OG_RE:
            m = rx.search(html_text)
            if m:
                img = html.unescape(m.group(1).strip())
                if img.startswith("//"):
                    img = "https:" + img
                elif img.startswith("/"):
                    from urllib.parse import urljoin
                    img = urljoin(url, img)
                if img.startswith("http"):
                    return img
    except Exception:  # noqa: BLE001
        pass
    return ""


def localize_image(img_url: str, post_url: str) -> str:
    """대표 이미지를 내려받아 thumbs/ 에 저장하고 로컬 경로를 반환한다.

    외부 CDN 은 다른 출처에서의 핫링크를 막는 경우가 많아, 브라우저에서 직접
    불러오면 깨진다. 그래서 이미지를 저장소에 함께 담아 같은 출처로 서빙한다.
    (다운로드는 서버에서 하고, Referer 를 글 주소로 넣어 핫링크 차단을 통과한다.)
    실패하면 "" 를 반환해 카드가 그라디언트 플레이스홀더로 표시되게 한다.
    """
    key = hashlib.md5(post_url.encode("utf-8")).hexdigest()[:16]
    rel = f"thumbs/{key}.jpg"
    dest = THUMBS_DIR / f"{key}.jpg"
    if dest.exists():
        return rel                       # 이미 받아둔 이미지 재사용
    if Image is None:
        return ""
    # 배민: 콘텐츠 이미지가 접속 불가한 woowa.in 에 있어 접속 가능한 woowahan.com 으로 치환
    img_url = img_url.replace("techblog.woowa.in", "techblog.woowahan.com")
    try:
        r = creq.get(img_url, impersonate="chrome", timeout=25,
                     headers={"Referer": post_url, "Accept": "image/avif,image/webp,image/*,*/*"})
        if r.status_code != 200 or not r.content:
            return ""
        im = Image.open(BytesIO(r.content))
        if im.mode in ("RGBA", "LA", "P"):     # 투명 배경은 흰색으로 합성
            bg = Image.new("RGB", im.size, (255, 255, 255))
            im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        w, h = im.size
        if w > 640:                            # 카드 크기에 맞춰 축소
            im = im.resize((640, max(1, round(h * 640 / w))), Image.LANCZOS)
        THUMBS_DIR.mkdir(exist_ok=True)
        im.save(dest, "JPEG", quality=80, optimize=True)
        return rel
    except Exception:  # noqa: BLE001
        return ""


# ---------------------------------------------------------------------------
# 소스별 페처
# ---------------------------------------------------------------------------
def fetch_rss(src):
    raw = http_get(src["feed"]).content
    feed = feedparser.parse(raw)
    out = []
    for e in feed.entries:
        iso = ""
        for key in ("published_parsed", "updated_parsed"):
            t = e.get(key)
            if t:
                iso = datetime(*t[:6], tzinfo=timezone.utc).isoformat()
                break
        if not iso:
            # feedparser 가 파싱 못한 날짜(타임존 없는 RFC822 등, 예: 데보션) 폴백
            for key in ("published", "updated"):
                raw = e.get(key)
                if not raw:
                    continue
                try:
                    from email.utils import parsedate_to_datetime
                    d = parsedate_to_datetime(raw)
                    if d.tzinfo is None:
                        d = d.replace(tzinfo=timezone.utc)
                    iso = d.astimezone(timezone.utc).isoformat()
                    break
                except Exception:  # noqa: BLE001
                    continue
        content_html = e.get("content", [{}])[0].get("value", "") if e.get("content") else ""
        summary = e.get("summary", "") or content_html
        tags = " ".join(t.get("term", "") for t in e.get("tags", []) if t.get("term"))
        image = ""
        for k in ("media_content", "media_thumbnail"):
            if e.get(k):
                image = e[k][0].get("url", "")
                if image:
                    break
        if not image:
            image = first_image_from_html(content_html, e.get("summary", ""))
        post = make_post(src, e.get("title", ""), e.get("link", ""), iso, summary,
                         e.get("author", ""), tags, image)
        if post:
            out.append(post)
    return out


def fetch_wordpress(src):
    """WordPress REST API 로 최근 1년치 전량 백필."""
    out = []
    after = CUTOFF.strftime("%Y-%m-%dT%H:%M:%S")
    page = 1
    while page <= 30:  # 안전 상한
        url = f"{src['api']}?per_page=50&page={page}&after={after}&_embed=1&orderby=date&order=desc"
        r = http_get(url)
        if r.status_code != 200:
            break
        items = r.json()
        if not items:
            break
        for p in items:
            iso = p.get("date_gmt") or p.get("date") or ""
            if iso and not iso.endswith("+00:00") and "T" in iso:
                iso = iso + "+00:00"
            emb = p.get("_embedded", {})
            terms = []
            for group in emb.get("wp:term", []) or []:
                terms += [t.get("name", "") for t in group]
            author = ""
            try:
                author = (emb.get("author") or [{}])[0].get("name", "")
            except Exception:  # noqa: BLE001
                pass
            image = ""
            fm = emb.get("wp:featuredmedia") or []
            if fm and isinstance(fm[0], dict):
                image = fm[0].get("source_url", "") or ""
            if not image:
                image = first_image_from_html(p.get("content", {}).get("rendered", ""))
            post = make_post(src, p.get("title", {}).get("rendered", ""), p.get("link", ""),
                             iso, p.get("excerpt", {}).get("rendered", ""),
                             author, " ".join(terms), image)
            if post:
                out.append(post)
        total_pages = int(r.headers.get("X-WP-TotalPages", "1") or "1")
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.6)
    return out


def fetch_d2(src):
    """네이버 D2 API 페이지네이션으로 최근 1년치 백필."""
    out = []
    cutoff_ms = CUTOFF.timestamp() * 1000
    page = 0
    while page < 40:  # 안전 상한
        r = http_get(f"{src['api']}?page={page}&size=30")
        if r.status_code != 200:
            break
        j = r.json()
        items = j.get("content", [])
        if not items:
            break
        stop = False
        for it in items:
            pub = it.get("postPublishedAt")
            if not pub:
                continue
            if pub < cutoff_ms:
                stop = True
                continue
            iso = datetime.fromtimestamp(pub / 1000, tz=timezone.utc).isoformat()
            path = it.get("url", "")
            link = path if path.startswith("http") else f"https://d2.naver.com{path}"
            img = it.get("postImage", "")
            if img and not img.startswith("http"):
                img = f"https://d2.naver.com/{img.lstrip('/')}"
            post = make_post(src, it.get("postTitle", ""), link, iso,
                             it.get("postHtml", ""), "", "", img)
            if post:
                out.append(post)
        meta = j.get("page", {})
        if stop or page + 1 >= meta.get("totalPages", 1):
            break
        page += 1
        time.sleep(0.6)
    return out


FETCHERS = {"rss": fetch_rss, "wordpress": fetch_wordpress, "d2": fetch_d2}


# ---------------------------------------------------------------------------
# 메인: 수집 → 병합/누적 → 1년 윈도우 → 저장
# ---------------------------------------------------------------------------
def load_existing():
    path = HERE / "data.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {p["url"]: p for p in data.get("posts", []) if p.get("url")}
    except Exception:  # noqa: BLE001
        return {}


def main():
    existing = load_existing()
    prev_count = len(existing)
    fetched = []
    stats = []

    for src in SOURCES:
        try:
            posts = FETCHERS[src["type"]](src)
            posts = [p for p in posts if within_window(p["date"])]
            fetched += posts
            stats.append(f"  {src['name']:<8} {len(posts):>3} 건  ({src['type']})")
            print(f"[OK] {src['name']} ({src['id']}): {len(posts)} AI글")
        except Exception as ex:  # noqa: BLE001
            stats.append(f"  {src['name']:<8} 실패: {type(ex).__name__}")
            print(f"[FAIL] {src['name']} ({src['id']}): {ex}", file=sys.stderr)
        time.sleep(1.0)  # throttle

    # ---- 대표 이미지 보강: 이미지 없는 글은 글 페이지의 og:image 로 채운다 ----
    #  이미 수집돼 이미지가 있던 글은 재요청하지 않아, 매일 실행 시 새 글만 조회한다.
    enriched = 0
    for p in fetched:
        if p.get("image"):
            continue
        old = existing.get(p["url"])
        if old and old.get("image"):
            p["image"] = old["image"]          # 이전에 찾아둔 이미지 재사용
            continue
        img = fetch_og_image(p["url"])
        if img:
            p["image"] = img
            enriched += 1
        time.sleep(0.4)                         # throttle
    if enriched:
        print(f"[img] og:image 로 대표 이미지 {enriched}건 보강")

    # ---- 병합/누적 (기존 + 신규, URL 기준 중복 제거) ----
    merged = dict(existing)
    added = 0
    now_iso = NOW.isoformat()
    for p in fetched:
        url = p["url"]
        if not url:
            continue
        if url in merged:
            old = merged[url]
            p["firstSeen"] = old.get("firstSeen", p["date"])
            merged[url] = p  # 최신 메타로 갱신
        else:
            p["firstSeen"] = now_iso
            merged[url] = p
            added += 1

    # ---- 전량 누적: 한 번 모은 글은 삭제하지 않고 계속 쌓는다 ----
    #  (신규 수집은 최근 1년을 기준으로 하되, 과거에 모아둔 글은 1년이 지나도 유지)
    kept = list(merged.values())
    kept.sort(key=lambda x: x.get("date", ""), reverse=True)

    # ---- 대표 이미지 로컬 저장: 외부 CDN 핫링크 차단을 피하려고 thumbs/ 에 내려받는다 ----
    #  이미 thumbs/ 로 바뀐 글은 재요청하지 않으므로, 매일 실행 시 새 글만 내려받는다.
    localized = failed = 0
    for p in kept:
        img = p.get("image", "")
        if not img.startswith("http"):
            continue                       # 이미 로컬(thumbs/…) 이거나 이미지 없음
        local = localize_image(img, p["url"])
        p["image"] = local                 # 성공: thumbs/xxx.jpg / 실패: "" (플레이스홀더)
        if local:
            localized += 1
        else:
            failed += 1
        time.sleep(0.3)                    # throttle
    if localized or failed:
        print(f"[img] 대표 이미지 로컬 저장 {localized}건 (실패 {failed}건)")

    payload = {
        "generatedAt": now_iso,
        "backfillWindowDays": WINDOW_DAYS,
        "sources": [{"id": s["id"], "name": s["name"], "color": s["color"], "home": s["home"]} for s in SOURCES],
        "posts": kept,
    }
    (HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "data.js").write_text(
        "// 자동 생성 - fetch_feeds.py 가 갱신합니다\nwindow.CLIP_DATA = "
        + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")

    print("\n=== 수집 요약 ===")
    print("\n".join(stats))
    print(f"\n이전 누적: {prev_count}건  |  신규 추가: {added}건  |  전량 누적 유지(삭제 없음)")
    print(f"현재 누적: {len(kept)}건  ->  data.json / data.js")


if __name__ == "__main__":
    main()
