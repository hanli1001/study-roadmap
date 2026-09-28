# -*- coding: utf-8 -*-
"""验收 批改单-D8-20260928.html —— 真在浏览器里跑一遍，不靠读源码。

用法：python -X utf8 tools/_check_grade_sheet.py
需要：playwright + 本机 Edge（channel="msedge"）
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "交互演示" / "批改单-D8-20260928.html"
SHOTS = ROOT / "交互演示"

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (("   " + str(detail)) if detail else ""))

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(PAGE.as_uri(), wait_until="load")
        pg.wait_for_timeout(500)

        # 1 基本渲染
        check("标题正确", pg.title().startswith("批改单 · D8 作业"), pg.title())
        check("页面非空（正文 > 8000 字）", len(pg.inner_text("body")) > 8000, len(pg.inner_text("body")))
        check("章节数 = 10", pg.locator("section.sec").count() == 10, pg.locator("section.sec").count())

        # 2 控制台
        real = [e for e in errs if "favicon" not in e.lower()]
        check("无控制台报错", not real, real[:3])

        # 3 勾选框
        ids = pg.eval_on_selector_all(".task input", "els => els.map(e => e.id)")
        check("返工勾选框 11 个", len(ids) == 11, len(ids))
        check("id 无重复", len(set(ids)) == len(ids), ids)
        tick0 = pg.inner_text("#tick")
        check("进度条初始为 0 / 11", tick0.startswith("0 / 11"), tick0)

        # 4 勾两个 → 刷新还在
        pg.check("#r1"); pg.check("#r2"); pg.wait_for_timeout(120)
        check("勾 2 个后进度 = 2 / 11", pg.inner_text("#tick").startswith("2 / 11"), pg.inner_text("#tick"))
        check("勾上的条目加了删除线", "done" in (pg.get_attribute("#r1", "class") or "") or
              "done" in pg.eval_on_selector("#r1", "e => e.parentNode.className"))
        pg.reload(wait_until="load"); pg.wait_for_timeout(400)
        check("刷新后仍是 2 / 11（localStorage）", pg.inner_text("#tick").startswith("2 / 11"), pg.inner_text("#tick"))
        pg.evaluate("localStorage.removeItem('lab.redo.D8.20260928')")
        pg.reload(wait_until="load"); pg.wait_for_timeout(400)

        # 5 Markdown 残留（W-40 那个病）
        body = pg.inner_text("body")
        check("无字面 ** 残留", "**" not in body, body.count("**"))
        check("无字面 ` 残留", "`" not in body, body.count("`"))

        # 6 链接都能找到
        hrefs = pg.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        bad = [h for h in hrefs if h.startswith(("http", "#")) is False and not (PAGE.parent / h).exists()]
        check("所有相对链接文件存在", not bad, bad)

        # 7 溢出（整页级，不看单个元素 —— 上次栽过）
        for w in (1440, 390):
            pg.set_viewport_size({"width": w, "height": 1000}); pg.wait_for_timeout(300)
            ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            check(f"{w}px 无整页横向溢出", ov <= 1, f"溢出 {ov}px")

        # 8 截图
        pg.set_viewport_size({"width": 1440, "height": 1000})
        pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(400)
        pg.screenshot(path=str(SHOTS / "_shot-grade-top.png"))
        pg.screenshot(path=str(SHOTS / "_shot-grade-full.png"), full_page=True)
        pg.set_viewport_size({"width": 390, "height": 900})
        pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(400)
        pg.screenshot(path=str(SHOTS / "_shot-grade-mobile.png"))

        # 9 打印态
        pg.set_viewport_size({"width": 1440, "height": 1000})
        pg.emulate_media(media="print"); pg.wait_for_timeout(250)
        pg.evaluate("window.scrollTo(0, 0)")
        vis = pg.eval_on_selector("#tick", "e => getComputedStyle(e).display")
        check("打印态隐藏进度条", vis == "none", vis)
        pg.screenshot(path=str(SHOTS / "_shot-grade-print.png"), full_page=True)

        b.close()

    print()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"{len(results) - n_fail} PASS / {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
