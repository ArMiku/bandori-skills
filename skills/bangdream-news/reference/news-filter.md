# News 列表筛选 / RSS 字段

> 数据来源：
> - 列表页 <https://bang-dream.com/news/>（WordPress 站点，服务端渲染，主题 `bangdream-portal`）
> - RSS feed <https://bang-dream.com/feed/>（`application/rss+xml`，**全站 feed 即 news feed**——所有 item 的 link 均指向 `/news/<id>/`）
>
> 本文基于对该页面 HTML 筛选表单与 RSS 的实际抓取验证（验证日期：2026-07-17）。站点改版后需复核。

## 筛选表单概览

页面筛选由**一个 GET 表单**实现，提交后所有筛选项以**查询参数**形式附加到 `/news/` URL 上。

五个控件维度：

| 维度 | 参数名 | 控件类型 | 默认值 | 说明 |
|------|--------|---------|--------|------|
| キーワード検索 | `s` | 文本输入 | 空 | 自由文本，匹配标题/正文 |
| カテゴリ | `category` | 单选 radio | `all` | 6 选（见下） |
| 年 | `year` | 下拉 select | `all` | 不限 |
| 月 | `month` | 下拉 select | `all` | 不限 |
| アーティスト | `artist[]` | 多选 checkbox | `all` | 与 events 同源 |

> 默认状态（不传任何参数）= 全部，按发布日**降序（新→旧）**。未筛选共约 **136 页**。

## 各筛选项取值

### カテゴリ `category`（单选 radio）

| value | 显示名（对应 RSS `<category>`） |
|-------|------|
| `all` | すべて（默认） |
| `info` | お知らせ |
| `release` | リリース |
| `live-event` | ライブ・イベント |
| `media` | メディア |
| `goods` | グッズ |

### 年 `year`

`all`（默认）或具体年份。页面当前列出 `2016`–`2027`，会随活动向上扩展。

### 月 `month`

`all`（默认）或 `1`–`12`。年、月各自独立可选：可只选年、只选月或同时指定。

### アーティスト `artist[]`（多选）

传参 `artist[]=value`，多选则重复：`artist[]=roselia&artist[]=mygo`。默认 `all` = 不过滤；不需要该维度时**完全不传** `artist[]`，勿把 `all` 与具体值混用。

| value | 显示名（常用简称） |
|-------|------------------|
| `poppinparty` | Poppin'Party（ppp） |
| `afterglow` | Afterglow（ag） |
| `pastel-palettes` | Pastel＊Palettes（pp） |
| `roselia` | Roselia（萝） |
| `hello-happy-world` | ハロー、ハッピーワールド！（hhw） |
| `morfonica` | Morfonica（蝶团） |
| `raise-a-suilen` | RAISE A SUILEN（RAS） |
| `mygo` | MyGO!!!!!（狗） |
| `avemujica` | Ave Mujica（鸡） |
| `yumemita` | 夢限大みゅーたいぷ（梦团） |
| `millsage` | millsage |
| `ikka-dumb-rock` | 一家Dumb Rock! |
| `shuffle` | シャッフルユニット |
| `other` | その他 |

> 值与 `/events/` 的 `artist[]` 同源。

### キーワード `s`

自由文本，匹配新闻标题/正文。日文需按需 URL 编码。实测 `?s=MyGO` 返回「検索結果」页且结果集变化，确认生效。

## URL 构造规则

**第 1 页**：筛选参数直接挂在 `/news/` 之后：

```
https://bang-dream.com/news/?category=release&year=2026&month=7&s=MyGO
https://bang-dream.com/news/?artist[]=roselia&category=live-event
```

**第 N 页（N ≥ 2）**：分页为**路径段** `/page/N/`，筛选查询串原样追加在后面：

```
https://bang-dream.com/news/page/2/?category=release
```

> ⚠️ **关键点**：分页是路径式 `/page/N/`，**不是** `?page=N`。带上筛选条件时，筛选查询串要拼到分页路径之后。第 1 页用 `/news/?{filters}`（不存在 `/page/1/`）。

常用示例：

| 目标 | URL |
|------|-----|
| 只看 リリース | `/news/?category=release` |
| 2026 年 7 月 | `/news/?year=2026&month=7` |
| 关键词「MyGO」 | `/news/?s=MyGO` |
| Roselia 的 Live-Event 类，第 2 页 | `/news/page/2/?artist[]=roselia&category=live-event` |

## 默认排序

按发布日**降序**（最新在前）。例：未筛选首页前几条依次为 2026 年 7 月 → 6 月。

## RSS feed

`https://bang-dream.com/feed/`（`application/rss+xml`），**全站 feed 即 news feed**——所有 item 的 link 均指向 `/news/<id>/`。

| 字段 | 说明 |
|------|------|
| `<item>` 数量 | **10 条**（固定，最近 10 篇） |
| `<title>` / `<link>` | 标题 / `https://bang-dream.com/news/<id>/` |
| `<pubDate>` | RFC 822，如 `Thu, 16 Jul 2026 13:55:41 +0000` |
| `<category>` | 日文分类名（お知らせ / リリース / ライブ・イベント …），对应 `category` 参数的显示名 |
| `<description>` | 纯文本摘要（CDATA），可作 summary |
| `<content:encoded>` | 完整正文 HTML（CDATA），最新 10 条可**直接从 RSS 取全文**，免抓详情页 |
| `<guid>` | **无** |

> **去重 key**：RSS 无 `<guid>`，稳定唯一键用 link 中的文章 ID（`/news/2371/` → `2371`）。
> 抓取纪律（UA 门禁对 feed 同样生效，裸 curl → 404）：见 [网页抓取策略](./fetch-strategy.md)。

## 与采集相关的注意点

- **SSR**：`/news/` 列表与详情页均服务端渲染，带浏览器 UA 抓回即可解析，无需 JS。
- **务必翻完分页**：未筛选约 136 页；筛选后页数减少。采集遍历所有 `/page/N/`，避免漏取。
- **筛选后分页拼接**：第 2 页起为 `/news/page/N/?{原筛选查询串}`，构造时保留全部筛选参数。
- **`artist[]` 多选**：URL 中同名参数多次出现，按数组处理，勿后值覆盖前值；`[]` 无需编码（实测保留字面 `[]` 可被服务端识别）。
- **列表卡片信息有限**：仅含分类标签 + 标题 + 日期 + 缩略图，正文需进入 `/news/<id>/` 详情页（正文容器 `<article class="p-news-detail__content c-post-content">`）。
- **列表卡片 DOM 结构**（curl/py 兜底解析用，验证日期 2026-07-17）：每条是 `<article class="p-news-list__item">`，内含选择器如下——直接拿来 BeautifulSoup `select`，无需试错猜 class。

  ```html
  <article class="p-news-list__item">
    <a class="p-news-list__item-link" href="https://bang-dream.com/news/<id>/">
      <figure class="p-news-list__item-thumb"><img .../></figure>
      <div class="p-news-list__item-date">2026.06.19</div>
      <div class="p-news-list__item-category"><span>お知らせ</span></div>
      <h3 class="p-news-list__item-title">标题</h3>
    </a>
  </article>
  ```

  | 字段 | 选择器 | 备注 |
  |------|--------|------|
  | 文章 ID / 链接 | `a.p-news-list__item-link[href]` | link 末段数字即去重/详情页 ID |
  | 日期 | `.p-news-list__item-date` | 格式 `YYYY.MM.DD`（非 RSS 的 RFC822） |
  | 分类 | `.p-news-list__item-category span` | 显示名（お知らせ / リリース …），对应 `category` 参数 |
  | 标题 | `.p-news-list__item-title` | |
  | 结果总数 | `span.c-sort-query__count` | 如 Roselia 筛选显示「188 件」 |
