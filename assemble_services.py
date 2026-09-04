#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_services_work.json + _summaries/<id>.json 을 합쳐 services.json / services.js 를 만든다.
서비스 -> 회사(company) -> 글(요약 포함) 형태로 그룹핑한다.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    work = json.loads((HERE / "_services_work.json").read_text(encoding="utf-8"))
    services = []
    for svc in work:
        sid = svc["id"]
        sfile = HERE / "_summaries" / f"{sid}.json"
        summ = {}
        if sfile.exists():
            try:
                summ = json.loads(sfile.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                summ = {}
        # 회사별 그룹핑
        comps = {}
        for it in svc["items"]:
            s = summ.get(it["url"], {})
            art = {
                "url": it["url"], "title": it["title"], "date": it.get("date", ""),
                "image": it.get("image", ""), "author": it.get("author", ""),
                "oneLiner": s.get("oneLiner", ""), "bullets": s.get("bullets", []),
                "thin": bool(s.get("thin", False)),
            }
            c = comps.setdefault(it["source"], {
                "source": it["source"], "name": it["company"], "color": it["color"], "articles": []})
            c["articles"].append(art)
        # 회사 정렬: 글 많은 순, 각 회사 글은 최신순
        comp_list = sorted(comps.values(), key=lambda c: -len(c["articles"]))
        for c in comp_list:
            c["articles"].sort(key=lambda a: a.get("date", ""), reverse=True)
        services.append({
            "id": sid, "name": svc["name"], "icon": svc["icon"], "desc": svc["desc"],
            "companyCount": len(comp_list),
            "articleCount": sum(len(c["articles"]) for c in comp_list),
            "companies": comp_list,
        })

    from datetime import datetime, timezone
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
