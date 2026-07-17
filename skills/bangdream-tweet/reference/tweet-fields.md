# 推文字段 / 归一规则

> nitter RSS 字段映射与输出归一。验证日期 2026-07-17（实测 `nitter.net/bang_dream_info/rss`：HTTP 200 / 29KB / 20 条）。

## RSS item → 输出字段

| nitter RSS | 输出字段 | 说明 |
|---|---|---|
| `<guid>` | `id` | 推文 status ID，去重 key |
| feed URL 的 account | `account` | 被扫描账号（如 `bang_dream_info`） |
| `<dc:creator>` vs account | `type` / `retweeted_author` | ≠ account → `retweet` + `retweeted_author`；= account → `original` |
| `<title>` | `title` / `text` | nitter 把推文全文放 `<title>`（纯文本） |
| `<link>` | `link` / `link_nitter` | `link` = x.com 规范；`link_nitter` = 原值 |
| `<pubDate>` | `published_at` | RFC822 → ISO UTC |
| `<description>` 内 `<img src=".../pic/...">` | `media[]` | 每图双 URL：pbs + nitter |
| `<description>` 内 `<blockquote>` | `quote` | 引用推文：text + x.com link + nitter link |

## 归一规则

### 链接

任意 nitter 实例 `/<user>/status/<id>(#m)` → `https://x.com/<user>/status/<id>`（换域、丢 `#m`）。

### 媒体

`https://<instance>/pic/<encoded>` → URL-decode → `https://pbs.twimg.com/<decoded>`。

例：`/pic/media%2FHNWxXnPbgAEXR2J.jpg` → `pbs.twimg.com/media/HNWxXnPbgAEXR2J.jpg`。

保留 `url_nitter` 原值（本环境 / CN 可拉取兜底；`pbs.twimg.com` 实测本环境 SSL 失败，看图优先 `url_nitter`）。

### type 判定

- `original`：`dc:creator` == 被扫描账号
- `retweet`：`dc:creator` != 账号（综合号转发各团号，如 `@BDP_yumemita`）
- `reply`：nitter 回复标记（本批 0；出现按 "Replying to" 标记判定，待复测）

## 样本（实测 2026-07-17）

- 20 条：约 16 `original` + 4 `retweet`（`@BDP_yumemita`）；19/20 含媒体；2 条引用推文。
- 推文量大于 news，state `SEEN_KEEP = 500`（ADR-0008）。
