#!/usr/bin/env python3
"""bangdream-news 增量扫描脚本（定时 / 推送场景）。

职责（单一）：读 RSS → 比对 state 去重 → 吐宿主中立 JSON。
不做渲染、不绑调度器、不绑推送渠道——那些由调用方（cron 包装 / hermes adapter）处理。

抓取红线：bang-dream.com 对 feed 做 UA 门禁，默认 UA 返回 404 空桩页。
本脚本默认带浏览器 UA，可用环境变量 BANGDREAM_NEWS_UA 覆盖。

用法：
    python scan_news.py scan [--state-file <path>]
    BANGDREAM_NEWS_STATE=/path/state.json python scan_news.py scan
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

FEED_URL = "https://bang-dream.com/feed/"
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_STATE = Path.home() / ".bangdream-news" / "state.json"
SEEN_KEEP = 200  # state 只保留最近 N 条已见 ID，避免无限增长（RSS 每轮 10 条）


def fetch_rss(ua: str) -> str:
    req = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": ua, "Accept-Language": "ja,en;q=0.8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        # 404/228B 通常是 UA 门禁没过
        hint = "（疑似 UA 门禁：feed 对默认 UA 返回 404，请带浏览器 UA）" if e.code == 404 else ""
        sys.exit(f"[scan_news] 抓取 feed 失败：HTTP {e.code} {hint}")
    except urllib.error.URLError as e:
        sys.exit(f"[scan_news] 抓取 feed 失败：{e.reason}")


def article_id(link: str) -> str:
    """link 形如 https://bang-dream.com/news/2371/ → 取末段数字作去重 key。"""
    for seg in reversed(link.rstrip("/").split("/")):
        if seg.isdigit():
            return seg
    return link  # 兜底：拿不到数字就用完整 link


def parse_items(xml_text: str) -> list[dict]:
    """RSS 无 guid；用 link 中的文章 ID 作去重 key。pubDate 解析成 ISO。"""
    root = ET.fromstring(xml_text)
    items = []
    for it in root.iter("item"):
        def txt(tag: str) -> str:
            el = it.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        link = txt("link")
        pub_raw = txt("pubDate")
        try:
            pub_iso = parsedate_to_datetime(pub_raw).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            pub_iso = pub_raw
        category = [c.text.strip() for c in it.findall("category") if c.text]
        items.append({
            "id": article_id(link),
            "title": txt("title"),
            "link": link,
            "published_at": pub_iso,
            "category": category[0] if category else None,
            "summary": txt("description"),
        })
    return items


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"seen": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and "seen" in data else {"seen": []}
    except (json.JSONDecodeError, OSError):
        return {"seen": []}


def save_state(path: Path, seen: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps({"seen": seen}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)  # 原子写


def cmd_scan(args: argparse.Namespace) -> int:
    ua = os.environ.get("BANGDREAM_NEWS_UA", DEFAULT_UA)
    state_path = Path(
        args.state_file
        or os.environ.get("BANGDREAM_NEWS_STATE")
        or DEFAULT_STATE
    ).expanduser()

    items = parse_items(fetch_rss(ua))
    state = load_state(state_path)
    seen = set(state.get("seen", []))

    new_items = [it for it in items if it["id"] not in seen]

    # 更新 seen：并入本轮（新的在前），去重后截断保留最近 SEEN_KEEP 条
    current_ids = [it["id"] for it in items]
    current_id_set = set(current_ids)
    merged = current_ids + [s for s in state.get("seen", []) if s not in current_id_set]
    save_state(state_path, merged[:SEEN_KEEP])

    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "feed_url": FEED_URL,
        "count": len(new_items),
        "new_items": new_items,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="bangdream-news 增量扫描（输出宿主中立 JSON）。")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="读 RSS → diff state → 输出新文章 JSON")
    p_scan.add_argument(
        "--state-file",
        help=f"状态文件路径（默认 {DEFAULT_STATE}，或 $BANGDREAM_NEWS_STATE）",
    )
    args = parser.parse_args()
    if args.cmd == "scan":
        return cmd_scan(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
