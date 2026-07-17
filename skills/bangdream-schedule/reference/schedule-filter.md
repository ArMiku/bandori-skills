# Schedule 卡片类型与解析

> 数据来源：`https://bang-dream.com/schedule/?month=YYYYMM`（WordPress 站点，服务端渲染，主题 `bangdream-portal`）。
> 本文基于对该页面原始 HTML 的实际抓取验证（验证日期：2026-07-17）。站点改版后需复核。

## `?month=` 参数

- 格式：`YYYYMM`（6 位），如 `202608` = 2026 年 8 月。
- 服务端按月渲染并返回该月完整月历，**单页一月、无分页**（与 news/discography/live 的多页列表不同）。
- **必须显式传**：裸 `/schedule/` 的默认月会漂（实测连抓两次返过不同月份），不可靠。"本月"由模型按当前日期（JST 口径）算出 `YYYYMM` 再传。
- 未来未公布月份：页面返回该月空月历（无卡片）→ 如实告知"该月暂无公布日程"。

## 卡片类型（CSS class 即类型键）

每张可点击卡片是一个 `<a>`，类型编码在 class 前缀，详情 url 在 `href`：

| class | 类型 | href 形态 | 详情路由 |
|-------|------|-----------|----------|
| `is-live-event` | Live / Event 公演 | `https://bang-dream.com/events/<slug>`（slug，如 `avemujica_livetour`、`kimchikura-fes-26`） | → `bangdream-live` |
| `is-release` | 专辑 / BD / 配信 発售 | `https://bang-dream.com/discographies/<数字ID>` | → `bangdream-discography` |
| `is-external` | 外部音乐节 / 外部出演（LuckyFes、FLOW THE FESTIVAL、マチ★アソビ 等） | **站外**（音乐节官网等） | 对不上 skill → 给外链 |
| `is-media` | 📻电台 / 📺电视・动画放送 | **站外**（电台 / 电视台官网，如 `funky802.com`） | 对不上 skill → 给外链 |

> **路由看 href 域名，不看 class**：href 在 `bang-dream.com/events|discographies|news` 下 → 对应 skill；**其他任何站外域名一律给外链**（`is-external` 与 `is-media` 都是站外）。实测 `is-media` 的 📻📺 条目也带外链（markdown 模式下会被吞成纯文字，正是 fetch-strategy 红线 2 的来由）。class 只用于上面的**类型过滤**。
>
> **news 不在日历里**：扫到的内容类型 class 只有上述四类，没有 `is-news`；日历卡片 href 也无 `/news/<id>`。news 走 `bangdream-news`。
> **emoji 不可靠**：文字里可能带 📻📺🛸 等前缀，但**不统一**（有的发售带 🛸、有的不带）——分类型一律以 **CSS class** 为准，不要靠 emoji。

### 结构性 class（非类型，解析时忽略 / 可利用）

`is-current-month` / `is-last-month` / `is-next-month`（月历跨月填充格）、`is-today`、`is-{weekday}`（`is-monday`…`is-sunday` 列头）、`is-first-day-of-month` / `is-last-day-of-month`。

## 去重（必做）

同一条卡片在原始 HTML 中出现**两次**：

- desktop 栅格视图：`...p-schedule-content__calendar-body-cell-body-item-inner`
- mobile 列表视图：`...p-schedule-content__calendar-body-column-list-item-inner`

两条 href 相同（`is-media` 无 href 则按 标题+所在日期 去重）。**输出前必须去重**，否则每条翻倍。

## 日期 / 时刻

- 日期取自卡片所在的日历单元格（日历按周排版，跨月末/次月初会有 `is-last-month`/`is-next-month` 的填充格，注意归到正确月份）。
- 部分条目自带时刻文字（如 `20:30〜`、`22:00〜`），多为放送 / 配信时间。

## 按意图过滤（对应 SKILL.md 步骤 3）

| 意图 | 取哪些 class |
|------|--------------|
| 活动 | `is-live-event` + `is-external` |
| 专辑 / 发售 | `is-release` |
| 放送（电视/电台） | `is-media` |
| 安排 / 日程（笼统） | 全量（四类全给） |

## 输出形态

按**日期升序**分组；每条 = 类型标签 + 标题 +（有则）时刻 +（有则）详情 url。空月如实回"该月暂无公布日程"。
