#!/usr/bin/env python3
"""bangdream-tweet 账号内搜索（深度搜索，交互场景）。

能力（已验证 2026-07-17）：用 Scrapling StealthyFetcher（Camoufox 隐身浏览器）
过 nitter 反爬，抓 `/<account>/search` 结果页 → 解析推文 → 宿主中立 JSON。
Scrapling 未安装 / 抓取失败时，回退 RSS-filter（仅最新 20 条，按关键词客户端过滤）。

可选依赖（深度搜索所需；不装也能跑，走 RSS 兜底）：
    pip install scrapling "camoufox[geoip]"
    python -m camoufox fetch

用法：
    python search_tweets.py "Roselia"
    python search_tweets.py "Roselia" --account bang_dream_info --since 2026-06-01 --until 2026-07-17 --min-faves 100
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

DEFAULT_BASE = "https://nitter.net"
DEFAULT_ACCOUNT = "bang_dream_info"
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

STATUS_RE = re.compile(r"/([^/]+)/status/(\d+)")
NS = {"dc": "http://purl.org/dc/elements/1.1/"}


def to_canonical_link(href: str, base: str) -> tuple[str, str]:
    """nitter /<user>/status/<id>(#m) → (x.com 规范, nitter 全链)。"""
    full = href if href.startswith("http") else f"{base.rstrip('/')}{href}"
    path = urllib.parse.urlparse(full).path or ""
    canon = urllib.parse.urlunparse(("https", "x.com", path, "", "", ""))
    return canon, full


def media_urls(nitter_pic_url: str) -> dict:
    """nitter /pic/<encoded> → {url: pbs, url_nitter}。"""
    m = re.search(r"/pic/(.+)$", nitter_pic_url)
    decoded = urllib.parse.unquote(m.group(1)) if m else nitter_pic_url
    return {"url": f"https://pbs.twimg.com/{html_mod.unescape(decoded)}", "url_nitter": nitter_pic_url}


def fetch_rss(base: str, account: str, ua: str) -> str:
    url = f"{base.rstrip('/')}/{account}/rss"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "ja,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def rss_fallback(base: str, account: str, ua: str, query: str) -> list[dict]:
    """Scrapling 不可用时：抓 RSS（最新 20）→ 按关键词客户端过滤。"""
    root = ET.fromstring(fetch_rss(base, account, ua))
    q = (query or "").lower()
    out = []
    for it in root.iter("item"):
        def txt(tag: str) -> str:
            el = it.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        title = txt("title")
        if q and q not in title.lower():
            continue
        creator_el = it.find("dc:creator", NS)
        creator = (creator_el.text or "").strip().lstrip("@") if creator_el is not None and creator_el.text else ""
        is_rt = bool(creator) and creator != account
        canon, nitter_link = to_canonical_link(txt("link"), base)
        out.append({
            "id": txt("guid"), "account": account,
            "type": "retweet" if is_rt else "original",
            "retweeted_author": f"@{creator}" if is_rt else None,
            "title": title, "text": title,
            "link": canon, "link_nitter": nitter_link,
            "published_at": txt("pubDate"),
        })
    return out


def stealth_search(base: str, account: str, query: str, since: str, until: str, min_faves: str):
    """Scrapling StealthyFetcher 抓 search 页 → 解析。返回 (results, used_url)。"""
    from scrapling.fetchers import StealthyFetcher

    params = f"f=tweets&q={urllib.parse.quote(query)}"
    if since:
        params += f"&since={since}"
    if until:
        params += f"&until={until}"
    if min_faves:
        params += f"&min_faves={min_faves}"
    url = f"{base.rstrip('/')}/{account}/search?{params}"

    page = StealthyFetcher().fetch(url, headless=True, humanize=False, network_idle=True, timeout=60000)
    results = []
    for item in page.css(".timeline-item"):
        link_el = item.css_first("a.tweet-link")
        href = link_el.attrib.get("href", "") if link_el else ""
        m = STATUS_RE.search(href)
        if not m:
            continue
        user, tid = m.group(1), m.group(2)
        text_el = item.css_first(".tweet-content")
        text = " ".join(text_el.text.split()) if text_el else ""
        date_a = item.css_first(".tweet-date a")  # 日期在 span 内 <a> 的 title（"Jul 16, 2026 · ..."）
        raw_date = date_a.attrib.get("title", "") if date_a else ""
        try:  # 归一成 ISO，与 scan_tweets 对齐
            date = datetime.strptime(raw_date, "%b %d, %Y · %I:%M %p UTC").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            date = raw_date
        is_rt = len(item.css(".retweet-header")) > 0 or user != account
        canon, nitter_link = to_canonical_link(href, base)
        media = [media_urls(img.attrib.get("src", "")) for img in item.css('img[src*="/pic/"]')]
        results.append({
            "id": tid, "account": account,
            "type": "retweet" if is_rt else "original",
            "retweeted_author": f"@{user}" if is_rt and user != account else None,
            "title": text, "text": text,
            "link": canon, "link_nitter": nitter_link,
            "published_at": date,
            "media": media,
        })
    return results, url


def main() -> int:
    ap = argparse.ArgumentParser(description="bangdream-tweet 账号内搜索（Scrapling；未装回退 RSS）。")
    ap.add_argument("query", help="搜索关键词")
    ap.add_argument("--account", default=DEFAULT_ACCOUNT)
    ap.add_argument("--since", help="起始日 YYYY-MM-DD（仅 Scrapling 模式生效）")
    ap.add_argument("--until", help="截止日 YYYY-MM-DD（仅 Scrapling 模式生效）")
    ap.add_argument("--min-faves", dest="min_faves", help="最低点赞数（仅 Scrapling 模式生效）")
    ap.add_argument("--base", default=None, help=f"nitter 实例（默认 {DEFAULT_BASE}，或 $BANGDREAM_TWEET_NITTER_BASE）")
    args = ap.parse_args()

    base = args.base or os.environ.get("BANGDREAM_TWEET_NITTER_BASE", DEFAULT_BASE)

    try:
        from scrapling.fetchers import StealthyFetcher  # noqa: F401
        results, used_url = stealth_search(base, args.account, args.query, args.since, args.until, args.min_faves)
        mode = "scrapling-stealthy"
    except Exception as e:
        print(
            f"[search_tweets] Scrapling 不可用/失败（{type(e).__name__}: {e}），回退 RSS-filter（仅最新 20 条）。"
            f" 装法：pip install scrapling \"camoufox[geoip]\" && python -m camoufox fetch",
            file=sys.stderr,
        )
        results = rss_fallback(base, args.account, DEFAULT_UA, args.query)
        used_url = f"{base.rstrip('/')}/{args.account}/rss"
        mode = "rss-fallback"

    payload = {
        "mode": mode,
        "query": args.query,
        "account": args.account,
        "instance": base,
        "source_url": used_url,
        "count": len(results),
        "results": results,
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
