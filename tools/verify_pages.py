"""页面验收：用本机 Edge 无头，把「函数卡册 / 每周书」的交互与版式逐项量成数字。

为什么要单独有它（而不是"打开看一眼"）：
    这两类页面**以后每周都会出新版**（学员要求「以后都这么做」）。
    "看着没问题"不算验证 —— 上一版就是靠人眼才发现「代码被裁切」「两条筛选栏同名」
    「.resume 黄条永远显示」这些问题，其中两个是**只有量才量得出来**的。
    这个脚本把该量的都量成数字，跑一次就知道有没有回归。

用法：
    python tools/verify_pages.py                      # 默认 http://127.0.0.1:8903
    python tools/verify_pages.py http://127.0.0.1:8000
    python tools/verify_pages.py --shot               # 顺便截图（存 交互演示/_shot-*.png）

前置：本机 Edge（脚本自动找），以及一个静态服务器（`python -m http.server 8903`）。
"""
from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOT_DIR = ROOT / "交互演示"

EDGES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def url(base: str, rel: str) -> str:
    return base.rstrip("/") + "/" + urllib.parse.quote(rel)


def _check_page_overflow(pg, w: int, check, check_true, notes) -> None:
    """判定**整页**是否横向溢出。

    为什么不逐个元素量：轨道（.rail）在窄屏是**故意的横滑容器**
    （`overflow-x:auto` + 子元素 `min-width:620px`，宁可滑也不糊）——
    它的子元素当然会超出视口右边，但整页并没有坏。逐元素量会把这种设计误判成 bug
    （我第一次就是这么误报的）。真正的判据是**文档本身有没有被顶宽**。
    逐元素的结果保留下来当诊断信息，只在整页真的溢出时才打印。
    """
    pg.set_viewport_size({"width": w, "height": 900})
    pg.wait_for_timeout(300)
    r = pg.evaluate("""() => {
        const d = document.documentElement, bad = [];
        document.querySelectorAll('body *').forEach(el => {
            const b = el.getBoundingClientRect();
            if (b.right > d.clientWidth + 1.5 && b.width > 0) bad.push(el.tagName + '.' + String(el.className).slice(0, 40));
        });
        return {sw: d.scrollWidth, cw: d.clientWidth, bad: bad};
    }""")
    ok = r["sw"] <= r["cw"] + 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {w}px 整页无横向溢出: scrollWidth={r['sw']} clientWidth={r['cw']}"
          + ("" if ok else f"  ← 越界元素 {r['bad'][:4]}"))
    if not ok:
        check_true(f"{w}px 整页无横向溢出", False, f"越界 {r['bad'][:4]}")
    elif r["bad"]:
        notes.append(f"{w}px 有 {len(r['bad'])} 个子元素超出视口，但在横滑容器内（如 .rail）—— 设计如此，不算溢出")


def main() -> int:
    base = next((a for a in sys.argv[1:] if a.startswith("http")), "http://127.0.0.1:8903")
    want_shot = "--shot" in sys.argv
    exe = next((p for p in EDGES if Path(p).exists()), None)
    if exe is None:
        print("找不到 Edge，无法验收")
        return 2

    from playwright.sync_api import sync_playwright

    fails: list[str] = []
    notes: list[str] = []

    def check(name: str, got, want) -> None:
        ok = got == want
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {got!r}" + ("" if ok else f"  期望 {want!r}"))
        if not ok:
            fails.append(f"{name}: 得到 {got!r}，期望 {want!r}")

    def check_true(name: str, got, why: str = "") -> None:
        print(f"  [{'PASS' if got else 'FAIL'}] {name}" + ("" if got else f"  ← {why}"))
        if not got:
            fails.append(name)

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=exe, headless=True)

        # ══════════════ 函数卡册 ══════════════
        print("\n【函数卡册】")
        pg = br.new_page(viewport={"width": 1440, "height": 1050})
        errs: list[str] = []

        def _note_err(m):
            """favicon 的 404 不算页面错误 —— 而且**它的 URL 在 location 里、不在 message 文本里**，
            按文本过滤 ("favicon" not in m.text) 是过滤不掉的（我第一次就这么写错了）。"""
            if m.type != "error":
                return
            u = (m.location or {}).get("url", "")
            if u.endswith("favicon.ico"):
                return
            errs.append(f"{m.text} @ {u}")

        pg.on("console", _note_err)
        pg.goto(url(base, "交互演示/函数卡.html"), wait_until="load")
        pg.wait_for_timeout(600)

        check_true("控制台无报错", not errs, "; ".join(errs)[:140])

        n = pg.evaluate("document.querySelectorAll('#grid .fncard').length")
        check_true("屏幕卡片已渲染", n > 100, f"只渲染了 {n} 张")
        notes.append(f"卡片总数 = {n}")

        rows = pg.evaluate("""() => [...document.querySelectorAll('#routeTable tbody tr')]
            .map(tr => ({段: tr.children[0].innerText.split('\\n')[0],
                         数: parseInt(tr.children[1].innerText, 10)}))""")
        check("路线覆盖表行数", len(rows), 8)
        empty = [r["段"] for r in rows if not r["数"]]
        check_true("路线覆盖表没有 0 张的段", not empty, f"空段：{empty}")
        notes.append("路线覆盖：" + " / ".join(f"{r['段']}={r['数']}" for r in rows))

        cats = pg.evaluate("[...document.querySelectorAll('#catChips .chip')].map(c => c.textContent)")
        check("类别筛选按钮数", len(cats), 11)      # 全部 + 10 类
        stages = pg.evaluate("[...document.querySelectorAll('#stageChips .chip')].map(c => c.textContent)")
        check("阶段筛选按钮数", len(stages), 5)      # 全部 + 4 阶段

        def search(kw: str) -> str:
            pg.fill("#q", kw)
            pg.wait_for_timeout(220)
            return pg.inner_text("#count")

        check("搜索「接反」", search("接反"), "显示 3 / 共 126 张")
        # ⚠️ 搜索是**全文**匹配：搜 agent 会连"提到 Agent 的 LLM API 卡"一起命中（14 张），
        #    这是对的。要精确数就用类别按钮（见下）。我第一次把期望写成 10 = 我错了，不是页面错。
        got = search("agent")
        n_agent = int(got.split()[1])
        check_true("搜索「agent」至少包含全部 10 张 Agent 卡", n_agent >= 10, got)
        notes.append(f"搜 agent 命中 {n_agent} 张（全文匹配，含 4 张提到 Agent 的 LLM 卡）")
        check("搜索不存在的词", search("zzz没有zzz"), "显示 0 / 共 126 张")
        check_true("空结果提示可见", pg.is_visible("#empty"))
        check("清空后", search(""), "显示 126 / 共 126 张")

        # 点「阶段A」筛选
        pg.click("#stageChips .chip:has-text('阶段A')")
        pg.wait_for_timeout(150)
        check("筛「阶段A」", pg.inner_text("#count"), "显示 47 / 共 126 张")
        tags = pg.evaluate("[...document.querySelectorAll('#grid .fncard .tag')].map(t=>t.textContent)")
        check_true("筛出来的卡确实都是阶段A", all(t in ("阶段A",) for t in tags if t in
                                              ("现在", "近期", "阶段A", "以后")), "混进了别的阶段")
        pg.click("#stageChips .chip:has-text('全部')")
        pg.wait_for_timeout(150)

        # 打印区不随筛选变（W-42 的教训）
        pg.click("#stageChips .chip:has-text('阶段A')")
        pg.wait_for_timeout(150)
        check("打印区卡片数（不随筛选）", pg.evaluate("document.querySelectorAll('#printAll .fncard').length"), 126)
        pg.click("#stageChips .chip:has-text('全部')")
        pg.wait_for_timeout(150)

        # 横向溢出（两种宽度）
        for w in (1440, 390):
            _check_page_overflow(pg, w, check, check_true, notes)
        pg.set_viewport_size({"width": 1440, "height": 1050})

        # ── 打印态（@media print）真渲染一眼 ────────────────────
        # 打印样式是最容易"静默失效"的地方（W-42：复习台那版 PDF 打出来一个答案都没有）
        pg.emulate_media(media="print")
        pg.set_viewport_size({"width": 794, "height": 1123})
        pg.wait_for_timeout(350)
        v = pg.evaluate("""() => ({
            deck: getComputedStyle(document.getElementById('deck')).display,
            print: getComputedStyle(document.getElementById('printAll')).display,
            bar: getComputedStyle(document.querySelector('.fnbar')).display,
            copy: getComputedStyle(document.querySelector('.fncopy')).display,
            cols: getComputedStyle(document.querySelector('#printAll .fn-grid')).columnCount,
            cards: document.querySelectorAll('#printAll .fncard').length,
            h: Math.round(document.getElementById('printAll').getBoundingClientRect().height)})""")
        check("打印态：屏幕查卡台隐藏", v["deck"], "none")
        check("打印态：打印区显示", v["print"], "block")
        check("打印态：筛选栏隐藏", v["bar"], "none")
        check("打印态：复制按钮隐藏", v["copy"], "none")
        check("打印态：分栏数", v["cols"], "2")
        check("打印态：卡片数（全量）", v["cards"], 126)
        notes.append(f"打印区总高 {v['h']}px（A4 可印高约 1017px）")
        if want_shot:
            pg.evaluate("window.scrollTo(0, 900)")
            pg.wait_for_timeout(250)
            pg.screenshot(path=str(SHOT_DIR / "_shot-fncard-print-a4.png"))
        pg.emulate_media(media="screen")
        pg.set_viewport_size({"width": 1440, "height": 1050})
        pg.wait_for_timeout(200)

        if want_shot:
            pg.screenshot(path=str(SHOT_DIR / "_shot-fncard-top.png"))
            pg.evaluate("document.getElementById('deck').scrollIntoView()")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(SHOT_DIR / "_shot-fncard-deck.png"))
            pg.evaluate("window.scrollTo(0, 0)")
            pg.wait_for_timeout(200)
            pg.screenshot(path=str(SHOT_DIR / "_shot-fncard-route.png"), clip={"x": 150, "y": 60, "width": 1080, "height": 700})

        # ══════════════ 每周书 ══════════════
        print("\n【本周书】")
        book = url(base, "每周书/W39-数据怎么连起来.html")
        pg2 = br.new_page(viewport={"width": 1440, "height": 1050})
        errs2: list[str] = []
        pg2.on("console", lambda m: errs2.append(f"{m.text} @ {(m.location or {}).get('url','')}")
               if (m.type == "error" and not (m.location or {}).get("url", "").endswith("favicon.ico")) else None)
        pg2.goto(book, wait_until="load")
        pg2.wait_for_timeout(600)
        check_true("控制台无报错", not errs2, "; ".join(errs2)[:140])

        chaps = pg2.evaluate("[...document.querySelectorAll('.chap, #cover')].map(e => e.getAttribute('data-nav'))")
        check_true("章节块 ≥ 13", len(chaps) >= 13, f"只有 {len(chaps)}")
        notes.append(f"章节块 = {len(chaps)}")

        # 「上次读到哪」条：没有 localStorage 时必须是**折叠**的（W-44）
        pg2.evaluate("localStorage.removeItem('lab.book.W39')")
        pg2.reload(wait_until="load")
        pg2.wait_for_timeout(400)
        h = pg2.evaluate("document.getElementById('resume').getBoundingClientRect().height")
        check("无书签时「上次读到哪」条高度", round(h), 0)

        # 真实点击「下一章」→ 页面真的动了
        y0 = pg2.evaluate("window.scrollY")
        pg2.click("#btnNext")
        pg2.wait_for_timeout(1500)
        y1 = pg2.evaluate("window.scrollY")
        check_true("点「下一章」页面真的滚动", y1 > y0, f"{y0} → {y1}")
        check_true("当前章标签跟着变", pg2.inner_text("#nowChap") != "封面", pg2.inner_text("#nowChap"))

        for w in (1440, 390):
            _check_page_overflow(pg2, w, check, check_true, notes)
        pg2.set_viewport_size({"width": 1440, "height": 1050})

        pg2.set_viewport_size({"width": 1440, "height": 1050})
        if want_shot:
            pg2.evaluate("window.scrollTo(0, 0)")
            pg2.wait_for_timeout(300)
            pg2.screenshot(path=str(SHOT_DIR / "_shot-book-top.png"))
            pg2.click(".toc a[href='#c5']")
            pg2.wait_for_timeout(1200)
            pg2.screenshot(path=str(SHOT_DIR / "_shot-book-c5.png"))

        br.close()

    print("\n──────── 备注 ────────")
    for x in notes:
        print(" ·", x)
    if fails:
        print(f"\n❌ 验收失败 {len(fails)} 项：")
        for f in fails:
            print("  -", f)
        return 1
    print("\n✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
