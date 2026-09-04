#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_summaries/_re_*.json (재요약) 을 서비스별 요약 파일에 병합한다.
같은 url 이 여러 서비스에 있으면 모든 서비스 파일에서 갱신한다."""
import json
from pathlib import Path

SUM = Path(__file__).resolve().parent / "_summaries"


def main():
    remap = {}
    for f in SUM.glob("_re_*.json"):
        remap.update(json.loads(f.read_text(encoding="utf-8")))
    print("재요약 항목:", len(remap))
    updated = 0
    for f in SUM.glob("*.json"):
        if f.name.startswith("_re_"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for url in list(d.keys()):
            if url in remap:
                d[url] = remap[url]
                changed = True
                updated += 1
        if changed:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("서비스 파일에서 갱신된 항목:", updated)
    # 남은 thin 집계
    thin = 0
    for f in SUM.glob("*.json"):
        if f.name.startswith("_re_"):
            continue
        for v in json.loads(f.read_text(encoding="utf-8")).values():
            if v.get("thin"):
                thin += 1
    print("남은 thin:", thin)


if __name__ == "__main__":
    main()
