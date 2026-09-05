#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_services_work.json + _summaries2/<id>.json(상세: oneLiner+sections+figures, drop) 을 합쳐
services.json / services.js 를 만든다. 서비스 -> 회사 -> 글(상세 요약) 그룹핑.
원문 그림(figures)은 assets/ 로 내려받아 자체 호스팅한다(외부 핫링크 차단 회피)."""
import hashlib
import json
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from curl_cffi import requests as creq
try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

HERE = Path(__file__).resolve().parent
SUM = HERE / "_summaries2"
ASSETS = HERE / "assets"


def localize_figure(url: str, referer: str) -> str:
    """원문 그림을 내려받아 assets/ 에 저장하고 로컬 경로를 반환(실패 시 '')."""
    url = url.replace("techblog.woowa.in", "techblog.woowahan.com")
    key = hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
    dest = ASSETS / f"{key}.jpg"
    rel = f"assets/{key}.jpg"
    if dest.exists():
        return rel
    if Image is None:
        return ""
    for attempt in range(2):
        try:
            r = creq.get(url, impersonate="chrome", timeout=25 + attempt * 15,
                         headers={"Referer": referer, "Accept": "image/avif,image/webp,image/*,*/*"})
            if r.status_code == 200 and r.content:
                im = Image.open(BytesIO(r.content))
                if im.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", im.size, (255, 255, 255))
                    im = im.convert("RGBA"); bg.paste(im, mask=im.split()[-1]); im = bg
                else:
                    im = im.convert("RGB")
                w, h = im.size
                if w > 1000:
                    im = im.resize((1000, max(1, round(h * 1000 / w))), Image.LANCZOS)
                if w < 120 or h < 90:            # 아이콘·아바타 등 너무 작은 건 제외
                    return ""
                ASSETS.mkdir(exist_ok=True)
                im.save(dest, "JPEG", quality=82, optimize=True)
                return rel
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.8)
    return ""
# 화면에 보일 서비스 순서
ORDER = ["incident", "reco", "search", "cs", "devprod", "data", "knowledge", "design", "quality", "translate"]


def main():
    work = {s["id"]: s for s in json.loads((HERE / "_services_work.json").read_text(encoding="utf-8"))}
    manual_file = HERE / "_manual_structured.json"
    manual = json.loads(manual_file.read_text(encoding="utf-8")) if manual_file.exists() else {}
    services = []
    ordered_ids = [i for i in ORDER if i in work] + [i for i in work if i not in ORDER]

    def loc_fig(f, referer):
        """fig({src,caption}) 을 로컬화. 이미 assets/ 경로면 그대로 통과."""
        if not f:
            return None
        src = (f.get("src") or "").strip()
        cap = f.get("caption", "")
        if src.startswith("assets/"):
            return {"src": src, "caption": cap}
        if not src.startswith("http"):
            return None
        local = localize_figure(src, referer)
        time.sleep(0.3)
        if local:
            return {"src": local, "caption": cap}
        return None

    for sid in ordered_ids:
        svc = work[sid]
        sfile = SUM / f"{sid}.json"
        summ = json.loads(sfile.read_text(encoding="utf-8")) if sfile.exists() else {}
        comps = {}
        for it in svc["items"]:
            s = manual.get(it["url"]) or summ.get(it["url"])
            if not s or s.get("drop"):          # 요약 없음/서비스 무관 → 제외
                continue
            # 동작 단계(how) 안의 인라인 그림 로컬화
            how = []
            for step in (s.get("how") or []):
                st = {"step": step.get("step", ""), "desc": step.get("desc", "")}
                fig = loc_fig(step.get("fig"), it["url"])
                if fig:
                    st["fig"] = fig
                    print(f"    [fig] {it['company']} {fig['src']}")
                how.append(st)
            # 하단 보조 그림(figures) 로컬화
            figs = []
            for f in (s.get("figures") or [])[:2]:
                fig = loc_fig(f, it["url"])
                if fig:
                    figs.append(fig)
                    print(f"    [fig] {it['company']} {fig['src']}")
            art = {
                "url": it["url"], "title": it["title"], "date": it.get("date", ""),
                "image": it.get("image", ""), "author": it.get("author", ""),
                "oneLiner": s.get("oneLiner", ""),
                "problem": s.get("problem", ""),
                "how": how,
                "keys": s.get("keys", []),
                "results": s.get("results", []),
                "figures": figs,
            }
            c = comps.setdefault(it["source"], {
                "source": it["source"], "name": it["company"], "color": it["color"], "articles": []})
            c["articles"].append(art)
        if len(comps) < 2:                      # 회사 2곳 미만 서비스는 제외
            print(f"[skip] {svc['name']} (확정 회사 {len(comps)})")
            continue
        comp_list = sorted(comps.values(), key=lambda c: -len(c["articles"]))
        for c in comp_list:
            c["articles"].sort(key=lambda a: a.get("date", ""), reverse=True)
        services.append({
            "id": sid, "name": svc["name"], "icon": svc["icon"], "desc": svc["desc"],
            "companyCount": len(comp_list),
            "articleCount": sum(len(c["articles"]) for c in comp_list),
            "companies": comp_list,
        })

    payload = {"generatedAt": datetime.now(timezone.utc).isoformat(), "services": services}
    (HERE / "services.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "services.js").write_text(
        "// 자동 생성 - build_services.py + assemble_services.py\nwindow.SERVICES_DATA = "
        + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("services.json / services.js 생성:")
    for s in services:
        print(f"  {s['name']:<22} 회사 {s['companyCount']} · 글 {s['articleCount']}")


if __name__ == "__main__":
    main()
