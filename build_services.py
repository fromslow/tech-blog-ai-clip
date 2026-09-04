#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서비스(구현 사례)별 정리 페이지용 데이터 준비 스크립트.

1) data.json 의 AI 글을 서비스(유즈케이스) 카테고리로 분류한다.
2) 각 서비스에서 회사당 최대 N개 글을 고른다.
3) 고른 글의 본문 전문을 받아 _content/<hash>.txt 로 저장한다 (요약 입력용).
4) _services_work.json 에 (서비스 -> 회사 -> 글 목록 + 본문 경로) 를 쓴다.

요약(summary)은 이후 사람이/모델이 _content 를 읽고 자기 표현으로 작성해 services.json 을 만든다.
"""
import hashlib
import json
import re
import time
from pathlib import Path

from curl_cffi import requests as creq

HERE = Path(__file__).resolve().parent
CONTENT_DIR = HERE / "_content"
PER_COMPANY = 2          # 서비스별 회사당 최대 글 수
CONTENT_CAP = 14000      # 본문 저장 최대 글자수

# 서비스 카테고리: id, 이름, 아이콘(remixicon), 설명, 매칭 키워드(정규식)
SERVICES = [
    {"id": "agent", "name": "AI 에이전트", "icon": "ri-robot-2-line",
     "desc": "LLM 에이전트로 업무·운영을 자동화한 사례",
     "pat": [r"에이전트", r"\bagent\b", r"\bMCP\b", r"copilot"]},
    {"id": "incident", "name": "장애 원인 분석 · SRE", "icon": "ri-alarm-warning-line",
     "desc": "AI로 장애를 탐지·분석하고 대응을 자동화한 사례",
     "pat": [r"장애", r"원인 ?분석", r"incident", r"\bSRE\b", r"이상 ?탐지", r"anomaly", r"알림|alert"]},
    {"id": "rag", "name": "RAG · 검색 · 임베딩", "icon": "ri-search-eye-line",
     "desc": "임베딩·벡터 검색·검색 증강 생성을 적용한 사례",
     "pat": [r"\bRAG\b", r"검색 ?증강", r"임베딩", r"embedding", r"벡터", r"시맨틱", r"semantic"]},
    {"id": "serving", "name": "LLM 서빙 · 비용 최적화", "icon": "ri-speed-up-line",
     "desc": "LLM 추론 서빙, 지연시간·비용을 최적화한 사례",
     "pat": [r"서빙", r"serving", r"vllm", r"추론", r"비용 ?(절감|최적화)", r"캐시|cache", r"latency|지연"]},
    {"id": "reco", "name": "추천 · 개인화", "icon": "ri-thumb-up-line",
     "desc": "추천 시스템과 개인화에 AI를 적용한 사례",
     "pat": [r"추천", r"recommend", r"개인화", r"personaliz"]},
    {"id": "devprod", "name": "코드리뷰 · 개발생산성", "icon": "ri-code-box-line",
     "desc": "AI 코드리뷰·코딩 어시스트로 개발 생산성을 높인 사례",
     "pat": [r"코드 ?리뷰", r"code ?review", r"개발 ?생산성", r"ai ?코딩|코딩 ?어시", r"생산성"]},
    {"id": "knowledge", "name": "지식관리 · 문서 자동화", "icon": "ri-book-open-line",
     "desc": "문서·릴리즈노트·위키 등 지식을 AI로 자동화한 사례",
     "pat": [r"위키|wiki", r"지식", r"ssot", r"릴리즈 ?노트", r"문서.*(자동|생성|요약)"]},
    {"id": "text2sql", "name": "Text2SQL · 자연어 질의", "icon": "ri-database-2-line",
     "desc": "자연어를 SQL·쿼리로 바꿔 데이터를 다루게 한 사례",
     "pat": [r"text\s*-?2?\s*-?sql", r"text2sql", r"자연어.{0,8}(sql|쿼리|질의|분석|조회)", r"nl2sql"]},
]


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    raw = re.sub(r"(?is)<(script|style|nav|footer|header|aside|form|noscript).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    import html as _h
    text = _h.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_main(html_text: str) -> str:
    # <article> 또는 <main> 우선, 없으면 body 전체
    for tag in ("article", "main"):
        m = re.search(r"(?is)<" + tag + r"[^>]*>(.*?)</" + tag + r">", html_text)
        if m and len(strip_html(m.group(1))) > 400:
            return strip_html(m.group(1))
    return strip_html(html_text)


def load_feed_contents() -> dict:
    """각 소스의 피드/API 에서 url -> 본문 HTML 맵을 만든다.
    Medium·D2·카카오 등 JS 렌더링 페이지는 직접 받으면 껍데기만 오므로,
    RSS content:encoded / WordPress content.rendered / D2 postHtml 을 본문으로 쓴다."""
    import feedparser
    import importlib.util
    spec = importlib.util.spec_from_file_location("ff", HERE / "fetch_feeds.py")
    ff = importlib.util.module_from_spec(spec); spec.loader.exec_module(ff)
    cmap = {}
    for src in ff.SOURCES:
        try:
            if src["type"] == "rss":
                feed = feedparser.parse(ff.http_get(src["feed"]).content)
                for e in feed.entries:
                    html = (e.get("content", [{}])[0].get("value", "") if e.get("content") else "") or e.get("summary", "")
                    if e.get("link") and html:
                        cmap[e["link"]] = html
            elif src["type"] == "wordpress":
                page = 1
                while page <= 6:
                    r = ff.http_get(f"{src['api']}?per_page=50&page={page}&orderby=date&order=desc")
                    if r.status_code != 200:
                        break
                    items = r.json()
                    if not items:
                        break
                    for p in items:
                        cmap[p.get("link", "")] = p.get("content", {}).get("rendered", "")
                    if page >= int(r.headers.get("X-WP-TotalPages", "1") or "1"):
                        break
                    page += 1
                    time.sleep(0.5)
            elif src["type"] == "d2":
                pg = 0
                while pg < 20:
                    r = ff.http_get(f"{src['api']}?page={pg}&size=30")
                    if r.status_code != 200:
                        break
                    j = r.json(); items = j.get("content", [])
                    if not items:
                        break
                    for it in items:
                        path = it.get("url", "")
                        link = path if path.startswith("http") else f"https://d2.naver.com{path}"
                        cmap[link] = it.get("postHtml", "")
                    if pg + 1 >= j.get("page", {}).get("totalPages", 1):
                        break
                    pg += 1
                    time.sleep(0.4)
        except Exception as e:  # noqa: BLE001
            print(f"    feed content 실패 {src['id']}: {type(e).__name__}")
        time.sleep(0.5)
    return cmap


FEEDS = None


def fetch_text(url: str) -> str:
    global FEEDS
    if FEEDS is None:
        print("  피드 본문 맵 로딩중...")
        FEEDS = load_feed_contents()
        print(f"  피드 본문 {len(FEEDS)}개")
    feed_txt = extract_main(FEEDS[url]) if url in FEEDS else ""
    page_txt = ""
    if len(feed_txt) < 800:                    # 피드 본문이 부실하면 페이지도 시도
        try:
            r = creq.get(url, impersonate="chrome", timeout=25,
                         headers={"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"})
            if r.status_code == 200:
                page_txt = extract_main(r.text)
        except Exception:  # noqa: BLE001
            pass
    best = feed_txt if len(feed_txt) >= len(page_txt) else page_txt
    return best[:CONTENT_CAP]


def main():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    posts = data["posts"]

    def hay(p):
        return (p["title"] + " \n " + p.get("summary", "")).lower()

    CONTENT_DIR.mkdir(exist_ok=True)
    work = []
    seen_urls = {}

    for svc in SERVICES:
        # 서비스 매칭 글 -> 회사별 그룹, 최신순
        by_comp = {}
        for p in posts:
            h = hay(p)
            if any(re.search(pt, h) for pt in svc["pat"]):
                by_comp.setdefault(p["source"], []).append(p)
        chosen = []
        for src, plist in by_comp.items():
            plist.sort(key=lambda x: x.get("date", ""), reverse=True)
            chosen += plist[:PER_COMPANY]
        # 회사 2곳 미만이면 서비스에서 제외
        if len({c["source"] for c in chosen}) < 2:
            print(f"[skip] {svc['name']} (회사 부족)")
            continue

        items = []
        for p in chosen:
            key = hashlib.md5(p["url"].encode()).hexdigest()[:16]
            cf = CONTENT_DIR / f"{key}.txt"
            if key not in seen_urls:
                if cf.exists():
                    txt = cf.read_text(encoding="utf-8")
                else:
                    try:
                        txt = fetch_text(p["url"])
                    except Exception as e:  # noqa: BLE001
                        txt = ""
                        print(f"    fetch 실패: {p['title'][:30]} ({type(e).__name__})")
                    cf.write_text(txt, encoding="utf-8")
                    time.sleep(1.0)
                seen_urls[key] = len(txt)
            items.append({
                "url": p["url"], "source": p["source"], "company": p["sourceName"],
                "color": p["color"], "title": p["title"], "date": p.get("date", ""),
                "image": p.get("image", ""), "author": p.get("author", ""),
                "contentFile": f"_content/{key}.txt", "chars": seen_urls[key],
            })
        work.append({"id": svc["id"], "name": svc["name"], "icon": svc["icon"],
                     "desc": svc["desc"], "items": items})
        print(f"[OK] {svc['name']:<22} 회사 {len({i['source'] for i in items})} · 글 {len(items)}")

    (HERE / "_services_work.json").write_text(
        json.dumps(work, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(s["items"]) for s in work)
    print(f"\n서비스 {len(work)}개 · 글 {total}건 · 본문 {len(seen_urls)}개 저장 -> _services_work.json")


if __name__ == "__main__":
    main()
