# nitter 抓取策略

> nitter 抓取纪律（bangdream-tweet）。与 bangdream-news 的 fetch-strategy 同构但约束不同：news 抓 bang-dream.com（UA 门禁），本 skill 抓 nitter（反爬）。验证日期 2026-07-17。

## 核心约束：HTML / 搜索受反爬，仅 RSS 可自动化

实测两实例 × 三工具（curl / web-reader MCP / Tavily MCP）：

| 实例 \ 方式 | curl | web-reader | Tavily | 浏览器 |
|---|---|---|---|---|
| nitter.net `/rss` | ✓ 200 / 29KB | — | — | ✓ |
| nitter.net HTML / 搜索 | ✗ 200 / **空体** | ✗ fetch failed | ✗ failed | ✓ |
| xcancel.com 全部 | ✗ 503 Cloudflare | ✗ 返回挑战页 | ✗ failed | ✓ |

结论：nitter 的 **HTML / 搜索页对自动化客户端反爬**（空体，或 Cloudflare/Turnstile 挑战 `Verifying your request`），仅真实浏览器可过。**RSS 是唯一稳定可自动化通路**。

## 优先级

1. **RSS（自动化场景必走）**：`https://<instance>/<account>/rss`。nitter.net 实测稳。
2. **浏览器级抓取 = Scrapling `StealthyFetcher`（已验证）**：深度搜索 `/<account>/search?...` 过反爬的唯一自动化路径。实测拿到 nitter search 76KB 真实 HTML / 20 结果（2026-07-17）。装法见下「Scrapling」。
3. ~~curl / web-reader / Tavily 抓 HTML~~：对 nitter 无效（反爬）；这些工具仅对 **RSS** 可用。

## RSS 抓取骨架

```bash
curl -sS -A '<浏览器 UA>' -H 'Accept-Language: ja,en;q=0.8' \
  'https://nitter.net/bang_dream_info/rss'
```

nitter 不像 bang-dream.com 那样强 UA 门禁（裸 curl 也能拿 RSS），但带浏览器 UA 更稳。

## Scrapling（深度搜索可选，已验证）

`StealthyFetcher`（Camoufox 隐身 Firefox）能过 nitter / Cloudflare 反爬——是 HTML / 搜索的**唯一自动化通路**。

实测（2026-07-17）：`StealthyFetcher.fetch("…/bang_dream_info/search?f=tweets&q=Roselia")` → 200 / 76KB / 20 结果（Roselia 命中、RT 归因正确）。封装在 `scripts/search_tweets.py`（未装自动回退 RSS-filter）。

```bash
pip install scrapling "camoufox[geoip]"
python -m camoufox fetch   # ~320MB Camoufox/Firefox 内核
```

- 首次 fetch 慢（启浏览器 ≈ 60s），适合交互 / 低频，**不适合 scan**。
- scan 仍走 RSS（零依赖）。

## 实例

- 默认 `nitter.net`（RSS 可用）。
- `xcancel.com`：全站 Cloudflare 反爬，**仅浏览器**，RSS 直接 400——不作 scan 默认。
- 切换：`BANGDREAM_TWEET_NITTER_BASE=https://<instance>`。
- 选实例原则：**RSS 能拉即合格**（scan 只用 RSS）；HTML / 搜索能否用取决于运行环境是否具备浏览器级抓取。

## 与 news 抓取策略的对照

| 维度 | bangdream-news（bang-dream.com） | bangdream-tweet（nitter） |
|---|---|---|
| 拦截机制 | UA 门禁（裸 curl → 404 空桩页） | 反爬（HTML → 空体 / Cloudflare） |
| 规避 | 带浏览器 UA 即可（任意页） | 仅 RSS 可自动化；HTML 需浏览器 |
| 自动化通路 | RSS + 列表 + 详情页（全可） | 仅 RSS |
