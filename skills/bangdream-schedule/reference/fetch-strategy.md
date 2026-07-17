# 网页抓取策略（schedule 专属）

> **bang-dream.com 站点抓取纪律**：UA 门禁、工具优先级、curl/py 兜底骨架与 news / live / discography 共用同一套；**schedule 唯一的硬差别在下方「红线 2：必须原始 HTML」**。
> 验证日期：2026-07-17（schedule 侧复核 `/schedule/?month=` 的 UA 门禁、markdown vs 原始 HTML 差异）。

## 红线 1：UA 门禁（与兄弟 skill 一致）

裸 `curl`（默认 UA）对 `/schedule/` 一律返回 **404 空桩页（≈228B）**，易被误判成"JS 未渲染"。**任何抓取必须带浏览器 UA。** 实测（2026-07-17）：

- `https://bang-dream.com/schedule/?month=202608`：无 UA → 404；带浏览器 UA → `200 / ~71KB`，SSR，卡片 `<a class="is-live-event ...">` 全在。
- 裸 `/schedule/`（不传 month）：默认月**会漂**（连抓两次返过不同月份）→ 见文末「永远显式 `?month=`」。

## 红线 2：必须抓原始 HTML，不能用 markdown

**这是 schedule 与另三个 skill 的唯一硬差别。** 另三个 skill 用专用工具的 **markdown** 输出即可（正文够用）；schedule **不行**：

- 实测 webReader markdown 模式抓 `/schedule/`：卡片**只剩纯文字标题**，`<a href>` **全丢**、links 摘要为空。
- 而 schedule 的路由与分类型**完全依赖 href 和 CSS class**（`is-live-event` / `is-release` / `is-media` / `is-external`）。**抓不到这俩字段，整个 skill 失效。**

→ 因此 schedule 必须：

- 专用工具**只用来取原始 HTML**（若有 raw / html 输出模式）；或
- 直接 `curl` / `py` 取 `resp.text`，**自己解析 HTML**。

## 兜底骨架（curl / py）

### curl

```bash
curl -sS \
  -A '<浏览器 UA>' \
  -H 'Accept-Language: ja,en;q=0.8' \
  'https://bang-dream.com/schedule/?month=202608'
```

- `-A '<浏览器 UA>'`：**必带**（否则 404）。任意近期桌面浏览器 UA（Chrome / Firefox / Safari 当前版均可，门禁只验"像不像浏览器"）。
- 永远带 `?month=YYYYMM`，不要裸 `/schedule/`。

### py（requests + BeautifulSoup，解析卡片）

```python
import requests
from bs4 import BeautifulSoup

UA = "<浏览器 UA>"  # 必带（否则 404）
headers = {"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"}
resp = requests.get("https://bang-dream.com/schedule/?month=202608",
                    headers=headers, timeout=20)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

# 卡片：<a class="is-{type} p-schedule-content__calendar-body-{cell|column}-...-item-inner" href="...">
TYPE_CLASS = {
    "is-live-event": "live",
    "is-release":    "discography",
    "is-external":   "external",
    "is-media":      "media",
}
seen, cards = set(), []
for a in soup.select(
    "a.p-schedule-content__calendar-body-cell-body-item-inner,"
    "a.p-schedule-content__calendar-body-column-list-item-inner"
):
    classes = a.get("class", [])
    t = next((c for c in classes if c in TYPE_CLASS), None)
    if not t:
        continue
    href = a.get("href")          # events/discographies 为站内；其余(is-external/is-media)多为站外外链；极少数无 href 时为 None
    title = a.get_text(strip=True)
    key = href or title
    if key in seen:
        continue                  # desktop / mobile 去重
    seen.add(key)
    cards.append({"type": TYPE_CLASS[t], "title": title, "href": href})
```

> 日期需结合卡片所在日历单元格（`is-current-month` / `is-next-month` 等）归位——向上找最近的日期单元格 DOM 取日期，按实际结构补充。

## 永远显式 `?month=`

- 裸 `/schedule/` 默认月漂移，不可靠。
- "本月"由模型按当前日期（**JST** 口径）算 `YYYYMM` 显式传入。
- 跨月（"接下来俩月"）= 多次请求各自 `?month=`，按日期升序合并去重。
