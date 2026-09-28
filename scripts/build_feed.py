#!/usr/bin/env python3
"""Собирает feed.xml (RSS 2.0) из data/updates.json.

Запуск из корня репозитория:  python3 scripts/build_feed.py [--base https://user.github.io/repo/]
Базовый адрес нужен только для ссылки на сам сайт в заголовке ленты.
"""
import argparse, json, sys, email.utils, datetime as dt
from pathlib import Path
from xml.sax.saxutils import escape

KINDS = {"act": "Акт", "draft": "Проект", "letter": "Разъяснение", "court": "Суд", "event": "Событие"}
ROOT = Path(__file__).resolve().parents[1]

def rfc822(iso: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return email.utils.format_datetime(dt.datetime(y, m, d, 6, 0, tzinfo=dt.timezone(dt.timedelta(hours=3))))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="", help="адрес сайта, например https://user.github.io/ot-monitor/")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    items = json.loads((ROOT / "data" / "updates.json").read_text(encoding="utf-8"))
    items.sort(key=lambda x: (x.get("addedAt") or x["date"], x["date"]), reverse=True)
    items = items[: args.limit]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
           "<title>Монитор охраны труда</title>",
           f"<link>{escape(args.base) or 'https://example.org/'}</link>",
           "<description>Изменения законодательства РФ об охране труда по официальным источникам</description>",
           "<language>ru</language>"]
    if args.base:
        out.append(f'<atom:link href="{escape(args.base.rstrip("/") + "/feed.xml")}" rel="self" type="application/rss+xml"/>')
    if items:
        out.append(f"<lastBuildDate>{rfc822(items[0].get('addedAt') or items[0]['date'])}</lastBuildDate>")
    for it in items:
        kind = KINDS.get(it.get("kind"), "Акт")
        eff = f" Вступает в силу: {it['effective']}." if it.get("effective") else ""
        desc = f"[{kind} · {it.get('source','')}] {it.get('summary','')}{eff}"
        for c in it.get("changes") or []:
            desc += f"\n\n{c.get('where','')}\nБЫЛО: {c.get('before','')}\nСТАЛО: {c.get('after','')}"
        out += ["<item>",
                f"<title>{escape(it['title'])}</title>",
                f"<link>{escape(it.get('url') or args.base)}</link>",
                f'<guid isPermaLink="false">{escape(it["id"])}</guid>',
                f"<pubDate>{rfc822(it['date'])}</pubDate>",
                f"<description>{escape(desc)}</description>"]
        out += [f"<category>{escape(t)}</category>" for t in it.get("topics", [])]
        out.append("</item>")
    out += ["</channel>", "</rss>", ""]
    (ROOT / "feed.xml").write_text("\n".join(out), encoding="utf-8")
    print(f"feed.xml: {len(items)} записей")
    return 0

if __name__ == "__main__":
    sys.exit(main())
