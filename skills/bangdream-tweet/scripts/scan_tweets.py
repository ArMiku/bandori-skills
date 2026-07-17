#!/usr/bin/env python3
"""bangdream-tweet 增量扫描脚本（定时 / 推送场景）。

职责（单一）：读 nitter RSS → 比对 state 去重 → 吐宿主中立 JSON。
不做渲染、不绑调度器、不绑推送渠道——那些由调用方（cron 包装 / hermes adapter）处理。

数据通路：只用 RSS——nitter HTML / 搜索受反爬，自动化不可达。
默认实例 nitter.net（RSS 实测稳）；可用 BANGDREAM_TWEET_NITTER_BASE 覆盖。

去重 key = <guid>（推文 status ID。

用法：
    python scan_tweets.py scan [--state-file <path>] [--account <handle> ...]
    BANGDREAM_TWEET_STATE=/path/state.json python scan_tweets.py scan
    BANGDREAM_TWEET_NITTER_BASE=https://nitter.net python scan_tweets.py scan
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

DEFAULT_BASE = "https://nitter.net"
DEFAULT_ACCOUNTS = ["bang_dream_info"]
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_STATE = Path.home() / ".bangdream-tweet" / "state.json"
SEEN_KEEP = 500  # 推文 20 条/轮，保留约 25 轮

NS = {"dc": "http://purl.org/dc/elements/1.1/"}

IMG_RE = re.compile(r'src="(https?://[^"/]+/pic/([^"]+))"', re.I)
# 引用推文 footer 内的来源链接：/<user>/status/<id>
QT_LINK_RE = re.compile(r"<footer>.*?(https?://[^/<]+/[^/]+/status/(\d+)).*?</footer>", re.I | re.S)


def fetch_rss(base: str, account: str, ua: str) -> str:
    url = f"{base.rstrip('/')}/{account}/rss"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": ua, "Accept-Language": "ja,en;q=0.8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        hint = ""
        if e.code in (400, 403, 503):
            hint = "（疑似反爬/实例不可用：换 BANGDREAM_TWEET_NITTER_BASE 到 RSS 可用的实例，如 nitter.net）"
        elif e.code == 404:
            hint = "（账号或 RSS 路径不存在）"
        sys.exit(f"[scan_tweets] 抓取 {url} 失败：HTTP {e.code} {hint}")
    except urllib.error.URLError as e:
        sys.exit(f"[scan_tweets] 抓取 {url} 失败：{e.reason}")


def to_canonical_link(nitter_url: str) -> str:
    """任意 nitter 实例的推文链接 → 规范 x.com
    /<user>/status/<id>(#m) → https://x.com/<user>/status/<id>"""
    path = urllib.parse.urlparse(nitter_url).path or ""
    return urllib.parse.urlunparse(("https", "x.com", path, "", "", ""))


def media_urls(nitter_pic_url: str) -> dict:
    """nitter /pic/<encoded> → {url: pbs.twimg.com, url_nitter: 原值}
    encoded 形如 media%2F<X>.jpg → pbs.twimg.com/media/<X>.jpg"""
    m = re.search(r"/pic/(.+)$", nitter_pic_url)
    decoded = urllib.parse.unquote(m.group(1)) if m else nitter_pic_url
    return {"url": f"https://pbs.twimg.com/{html_mod.unescape(decoded)}", "url_nitter": nitter_pic_url}


def extract_media(description: str) -> list[dict]:
    return [media_urls(m.group(1)) for m in IMG_RE.finditer(description or "")]


def extract_quote(description: str):
    """引用推文（QT）：nitter description 内 <blockquote> + <footer> 指向原推。
    返回 {text, link(x.com), link_nitter} 或 None。"""
    if "<blockquote>" not in (description or ""):
        return None
    m = QT_LINK_RE.search(description)
    if not m:
        return None
    nitter_link = m.group(1)
    bq = description.split("<blockquote>", 1)[1].split("</blockquote>", 1)[0]
    bq = bq.split("<footer", 1)[0]  # 去掉来源 footer
    text = html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bq))).strip()
    return {"text": text[:280], "link": to_canonical_link(nitter_link), "link_nitter": nitter_link}


def parse_items(xml_text: str, account: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for it in root.iter("item"):
        def txt(tag: str) -> str:
            el = it.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        creator_el = it.find("dc:creator", NS)
        creator = (creator_el.text or "").strip().lstrip("@") if creator_el is not None and creator_el.text else ""

        guid = txt("guid")
        link_nitter = txt("link")
        pub_raw = txt("pubDate")
        try:
            pub_iso = parsedate_to_datetime(pub_raw).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            pub_iso = pub_raw

        is_rt = bool(creator) and creator != account
        desc = txt("description")
        items.append({
            "id": guid,
            "account": account,
            "type": "retweet" if is_rt else "original",
            "retweeted_author": f"@{creator}" if is_rt else None,
            "title": txt("title"),
            "text": txt("title"),  # nitter <title> 即推文纯文本
            "link": to_canonical_link(link_nitter),
            "link_nitter": link_nitter,
            "published_at": pub_iso,
            "media": extract_media(desc),
            "quote": extract_quote(desc),
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
    tmp.write_text(json.dumps({"seen": seen}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # 原子写


def cmd_scan(args: argparse.Namespace) -> int:
    base = os.environ.get("BANGDREAM_TWEET_NITTER_BASE", DEFAULT_BASE)
    ua = os.environ.get("BANGDREAM_TWEET_UA", DEFAULT_UA)
    accounts = list(args.account or DEFAULT_ACCOUNTS)
    state_path = Path(
        args.state_file or os.environ.get("BANGDREAM_TWEET_STATE") or DEFAULT_STATE
    ).expanduser()

    state = load_state(state_path)
    seen_old = state.get("seen", [])
    seen_set = set(seen_old)

    all_items: list[dict] = []
    for acct in accounts:
        all_items.extend(parse_items(fetch_rss(base, acct, ua), acct))

    new_items = [it for it in all_items if it["id"] not in seen_set]

    # 更新 seen：本轮 ID 在前 + 旧 seen 中本轮未出现的，截断 SEEN_KEEP
    current_ids = [it["id"] for it in all_items]
    current_set = set(current_ids)
    merged = current_ids + [s for s in seen_old if s not in current_set]
    save_state(state_path, merged[:SEEN_KEEP])

    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "instance": base,
        "accounts": accounts,
        "count": len(new_items),
        "new_items": new_items,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="bangdream-tweet 增量扫描（输出宿主中立 JSON）。")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="读 nitter RSS → diff state → 输出新推文 JSON")
    p_scan.add_argument(
        "--state-file",
        help=f"状态文件路径（默认 {DEFAULT_STATE}，或 $BANGDREAM_TWEET_STATE）",
    )
    p_scan.add_argument(
        "--account", action="append", help="账号（可多次；默认 bang_dream_info）"
    )
    args = parser.parse_args()
    if args.cmd == "scan":
        return cmd_scan(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
