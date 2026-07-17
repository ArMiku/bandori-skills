---
name: bangdream-schedule
description: BanG Dream 官网 Schedule（スケジュール）月历查询 SOP。给用户提供 BangDream/邦多利/邦邦 企划【按月】的日程总览——ライブ/イベント、专辑/BD 発售、电台节目、电视/动画放送、外部音乐节出演等【跨类聚合】的月度安排。当用户问「这个月/本月/某月(X月/202608)有什么安排/日程/活动/发售」「这个月邦有什么」「下个月有什么动态」等【带明确月份、想一屏看全跨类日程】时使用本 Skill。不带明确月份的"最近有什么活动/发售"→ 走 live / discography。企划包括 Poppin'Party(ppp)、Afterglow(ag)、Pastel＊Palettes(pp)、Roselia(萝)、ハロー、ハッピーワールド！(hhw)、Morfonica(蝶团)、RAISE A SUILEN(RAS)、MyGO!!!!!(狗)、Ave Mujica(鸡)、夢限大みゅーたいぷ(梦团)、millsage、一家Dumb Rock!、シャッフルユニット。
---

# BanG Dream! Schedule 月历查询 SOP

## When NOT to use

- 非 BanG Dream 企划相关
- **不带明确月份的"最近有什么活动"** → `bangdream-live`（判据：有"本月/某月/X月"才进 schedule，只说"最近"走 live）
- **不带明确月份的"最近有什么发售"** → `bangdream-discography`
- News / 告知 / 资讯 → `bangdream-news`（schedule 日历里**没有 news 型卡片**）
- 官方 X 推文 → `bangdream-tweet`
- 某条 live / discography 的**详情深查**（票务 / 特典 / 价格 / 场馆）→ 对应 skill；schedule 只负责给到该条的 url 入口，不自己采详情

## 定位（一句话）

schedule 是**月历入口 / 索引层**：按月铺开跨类卡片（每张带「类型 + 标题 + 日期 + 详情页 url」），**不采集详情**。用户追问某一条时，拿本 skill 返回的 url，喂给 live / discography 的详情页流程。

## 数据源

| 数据源 | 用途 |
|--------|------|
| `https://bang-dream.com/schedule/?month=YYYYMM` | 指定年月的月历（服务端按月渲染，单页一月，**无分页**） |

> **决策层红线**：
> - **红线 1（UA 门禁）**：bang-dream.com 对 `/schedule/` 做 UA 门禁——裸 `curl`（默认 UA）返回 **404 空桩页（≈228B）**，易被误判成"JS 未渲染"。**任何抓取必须带浏览器 UA。**
> - **红线 2**：**必须抓原始 HTML，不能用 markdown 输出**。专用工具的 markdown 模式**会把卡片 `<a href>` 和类型 class 全丢掉**（实测 webReader markdown 模式下卡片只剩纯文字标题、links 摘要为空）——而 href 和 class 正是 schedule 路由与分类型所依赖的字段。**抓不到 href/class，整个 skill 失效。** 工具判定、curl/py 骨架见 [网页抓取策略](#网页抓取策略)。

## 查询流程

### 1. 确定目标月 → 构造 `?month=YYYYMM`

- **永远显式传 `?month=YYYYMM`**，不要用裸 `/schedule/`——裸 URL 的"默认月"会漂（实测同一天连抓两次，一次返 5 月、一次返别的月），不可靠。
  - 「这个月 / 本月」→ 当前年月（**按 JST 口径**），模型用上下文当前日期算出 `YYYYMM`（如 2026-07 → `202607`）。
  - 「X 月 / 2026年8月 / 8月」→ `?month=202608`。
  - 「下个月 / 接下来俩月」→ 算出对应一个或多个 `YYYYMM`，**多次请求拼接**，按日期升序合并。
- 跨月拼接时注意月末/次月衔接，去重跨月边界重复项。

### 2. 抓原始 HTML → 按 class 解析卡片

- 抓 `?month=YYYYMM` 的**原始 HTML**（带 UA），用 BeautifulSoup 等解析。
- 卡片是 `<a>` 元素，**类型编码在 CSS class**、**详情 url 在 href**。结构与类型映射见 [Schedule 卡片类型与解析](#schedule卡片类型与解析)。
- **去重**：同一条卡片在原始 HTML 里出现两次——desktop 栅格（`...calendar-body-cell-body-item-inner`）+ mobile 列表（`...calendar-body-column-list-item-inner`）各一份。按 href（无 href 则按 标题+日期）去重。
- 日期取自卡片所在日历单元格；部分条目自带时刻（如 `20:30〜`）。

### 3. 按用户意图过滤

| 用户意图 | 展示哪些 class |
|----------|----------------|
| 「有什么**活动**」 | `is-live-event` + `is-external`（外部音乐节出演也算活动） |
| 「有什么**专辑/发售**」 | `is-release` |
| 「有什么**放送/电视/电台**」 | `is-media` |
| 「有什么**安排/日程**」（笼统，无具体类型） | **全量**：四类全铺（含 `is-media` 日常放送） |

> 笼统"安排"默认全量、连 `is-media` 日常放送也铺。日常放送条目较多（每周电台/电视），全量时按日期分组输出，避免刷屏式平铺。

### 4. 详情路由（追问某一条时）

**路由看 href 的域名 / 路径，不看 class**（实测同一 class 下 href 可能站内、也可能站外）：

| href | 追问详情时 |
|------|-----------|
| `bang-dream.com/events/<slug>` | → 走 `bangdream-live` 详情页流程 |
| `bang-dream.com/discographies/<数字ID>` | → 走 `bangdream-discography` 详情页流程 |
| `bang-dream.com/news/<id>` | → 走 `bangdream-news`（日历里实测基本不出现） |
| 其他任何站**外**域名 | 对不上 skill → **把外链直接给用户**，不进详情流程 |

> 实测（2026-07）：`is-live-event` 多数指向 `/events/`（个别指向站外）；`is-release` → `/discographies/`；`is-external` 与 `is-media`（放送类）**都指向站外**（音乐节官网 / 电台・电视台站，如 `funky802.com`、`bushiroad-store.com`）→ 一律给外链。**`is-media` 不是"无链接"，是外链**——别因为它没指向 bang-dream 就当纯文字丢掉。
>
> class 的用途是**类型过滤**（步骤 3 展示哪些），不是路由。
>
> news 不走 schedule：日历里没有 news 型卡片；用户要 news 走 `bangdream-news`。

## Output

按**日期升序**分组输出；每条带「类型标签 + 标题 +（有则）时刻 +（有则）详情 url」。笼统问给全量、指定类型只给该类。不输出抓取 / 解析 / 去重的过程信息。空月 / 未来未公布月份如实回「该月暂无公布日程」。

## Reference

<div id="schedule卡片类型与解析"></div>

- [Schedule 卡片类型与解析](./reference/schedule-filter.md)

<div id="网页抓取策略"></div>

- [网页抓取策略](./reference/fetch-strategy.md)
