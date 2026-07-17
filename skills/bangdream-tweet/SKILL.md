---
name: bangdream-tweet
description: BanG Dream 官方 X（Twitter，经 nitter 镜像）动态查询 skill。给用户提供 BangDream/邦多利/邦邦 官方 X 账号 @bang_dream_info 推文（原创/引用RT/转发）的查询与解读。当用户想看官方最近发了什么推、搜某条推、按时间筛推文、或获取某条推全文/图时，使用本 Skill。定时/推送场景由 scripts/scan_tweets.py 承担。企划包括 Poppin'Party(ppp)、Afterglow(ag)、Pastel＊Palettes(pp)、Roselia(萝)、ハロー、ハッピーワールド！(hhw)、Morfonica(蝶团)、RAISE A SUILEN(RAS)、MyGO!!!!!(狗)、Ave Mujica(鸡)、夢限大みゅーたいぷ(梦团)、millsage、一家Dumb Rock!、シャッフルユニット。
---

# BanG Dream! 官方 X（nitter）查询 skill

## When NOT to use

- 非 BanG Dream 企划相关
- 官网 News（お知らせ / リリース等）→ `bangdream-news`
- Live / Event 票务、抽选、场馆、场贩 → `bangdream-live`
- 非官方 X 账号动态（本 skill 仅综合官方号 `@bang_dream_info`）

## 数据源

| 数据源 | 用途 | 自动化可达 |
|--------|------|-----------|
| `https://nitter.net/bang_dream_info/rss`（RSS，20 条） | 最新 / 增量（含 guid / pubDate / 媒体 / 引用） | ✓ 稳定（唯一） |
| `https://nitter.net/bang_dream_info`（HTML 时间线） | 浏览器看 | ✗ 反爬 |
| `/<account>/search?f=tweets&q=&since=&until=&min_faves=`（HTML） | 账号内深度搜索 | ✗ 反爬（浏览器可用） |

> **抓取红线（见 [抓取策略](#抓取策略)）**：nitter 实例的 HTML / 搜索页对自动化客户端（curl / web-reader / Tavily）**反爬**（空体或 Cloudflare 挑战），仅真实浏览器可过。**RSS 是唯一稳定可自动化通路**。实例可配。

## 查询流程

### 1. 最新推文 / 增量

抓 RSS（20 条，新→旧）。每条含：`type`（original / retweet）、`media`（pbs + nitter 双 URL）、`quote`（引用推文）。字段映射与归一见 [推文字段 / 归一规则](#推文字段--归一规则)。

### 2. 关键词 / 时间过滤（RSS 内）

RSS 只给最新 20 条；「最近有没有提到 X」「这两天发的」在客户端按 `text` / `published_at` 过滤即可——永远可用。

### 3. 深度搜索（需使用 Scrapling）

```bash
python scripts/search_tweets.py "<关键词>" [--account bang_dream_info] [--since 2026-06-01] [--until 2026-07-17] [--min-faves 100]
```

- 装了 Scrapling 时用 `StealthyFetcher`（Camoufox 隐身浏览器）过反爬，抓 `/<account>/search?f=tweets&q=&since=&until=&min_faves=` → 解析推文（type / link / media / published_at / RT 归因）→ 宿主中立 JSON。实测 76KB 真实 HTML / 20 结果。
- **可选依赖**：`pip install scrapling "camoufox[geoip]" && python -m camoufox fetch`（~320MB 浏览器内核）。
- **不装也能用**：脚本自动回退「流程 2」RSS-filter（仅最新 20 条）。

## 链接 / 媒体归一（输出纪律）

**面向用户的链接一律用规范域名 `x.com`。nitter 仅供后端抓取，禁止外漏到给用户的回复。**（用户直接看的是官方 X `x.com/bang_dream_info`，nitter 只是抓取后端。）

- 推文链接 → `https://x.com/<account>/status/<id>`（脚本 `link` 字段已归一，直接用它）。`link_nitter` 仅内部备用，**不展示给用户、不建议用户访问**。
- 媒体 → `pbs.twimg.com`（规范主，优先展示）+ `nitter /pic/`（可达性兜底，仅 pbs 加载失败时用）。
- RT 标注 `[RT @原作者]`；数据层不过滤。
- **兜底引导也走 x.com**：当 RSS/搜索无果、需建议用户自行查看时，引导到 `https://x.com/bang_dream_info`（官方账号）或 `https://x.com/search?q=...&f=live`（X 搜索），**不要给任何 `nitter.net/...` 链接**。

**Red Flags（出现即违规，自查删除）**：
- 给用户的推文/账号/搜索链接里出现 `nitter.net`。
- 回复末尾出现「想看更多请访问 nitter.net/…」「浏览器打开 nitter.net/…/search」之类。
- 把脚本的 `link_nitter` 字段当作主链接贴给用户。

## 定时推送（scan 脚本）

对话场景用上面的 SOP；**定时 / 推送场景**（cron / hermes 等常驻 agent、无对话上下文）走 `scripts/scan_tweets.py`：

```bash
python scripts/scan_tweets.py scan [--state-file <path>] [--account <handle> ...]
```

- 读 nitter RSS（默认实例 `nitter.net`，可 `BANGDREAM_TWEET_NITTER_BASE` 覆盖）→ 比对 state 去重（key = `<guid>` 推文 ID）→ **只吐宿主中立 JSON**（`new_items`：id / account / type / retweeted_author / title / text / link / link_nitter / published_at / media / quote）。
- state 默认 `~/.bangdream-tweet/state.json`（或 `BANGDREAM_TWEET_STATE`）；UA 可 `BANGDREAM_TWEET_UA` 覆盖。
- 渲染 / 推送渠道不在脚本内，由调用方决定；`count=0` 表示无更新。

## Output

推文：正文 + 时间 + `x.com` 链接（+ 媒体 URL / 引用推文）。RT 标注 `[RT @原作者]`。**面向用户的一切链接都用 `x.com`（见输出纪律）；nitter 仅供后端抓取，不外漏——包括无结果时建议用户去看的链接。** 不输出抓取 / 反爬判断的过程信息。

## Reference

<div id="推文字段--归一规则"></div>

- [推文字段 / 归一规则](./reference/tweet-fields.md)

<div id="抓取策略"></div>

- [抓取策略（HTML 反爬 vs RSS）](./reference/fetch-strategy.md)
