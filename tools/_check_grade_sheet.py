# -*- coding: utf-8 -*-
"""批改单页面验收 —— 真在浏览器里跑一遍，不靠读源码。

用法：
    python -X utf8 tools/_check_grade_sheet.py            # 查下表里全部页面
    python -X utf8 tools/_check_grade_sheet.py 二轮        # 只查文件名含"二轮"的

需要：playwright + 本机 Edge（channel="msedge"）
新增一张批改单时，只要往 PAGES 里加一行。
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "交互演示"

# 文件 → 该页特有的期望值（minlen = 正文最少字数，只用来防"页面是空的"）
PAGES = {
    "批改单-D8-20260928.html":      dict(secs=10, boxes=11, key="lab.redo.D8.20260928", shot="_shot-grade",  minlen=5000),
    "批改单-D8-二轮-20261005.html": dict(secs=8,  boxes=2,  key="lab.redo.D8.round2",  shot="_shot-grade2", minlen=3500),
    "批改单-v1第1步-20261009.html": dict(secs=7,  boxes=4,  key="lab.redo.v1b1.20261009", shot="_shot-grade3", minlen=4000),
}

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (("   " + str(detail)) if detail else ""))


def run(pg, fname, spec):
    page = SHOTS / fname
    check(f"[{fname}] 文件存在", page.exists())
    if not page.exists():
        return
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(page.as_uri(), wait_until="load")
    pg.wait_for_timeout(500)

    check("  标题含「批改单」", pg.title().startswith("批改单"), pg.title())
    check(f"正文 > {spec['minlen']} 字", len(pg.inner_text("body")) > spec["minlen"],
          len(pg.inner_text("body")))
    check(f"  章节数 = {spec['secs']}", pg.locator("section.sec").count() == spec["secs"],
          pg.locator("section.sec").count())
    real = [e for e in errs if "favicon" not in e.lower()]
    check("  无控制台报错", not real, real[:3])

    ids = pg.eval_on_selector_all(".task input", "els => els.map(e => e.id)")
    check(f"  勾选框 {spec['boxes']} 个", len(ids) == spec["boxes"], len(ids))
    check("  id 无重复", len(set(ids)) == len(ids), ids)
    check(f"  进度条初始 0 / {spec['boxes']}",
          pg.inner_text("#tick").startswith(f"0 / {spec['boxes']}"), pg.inner_text("#tick"))
    if len(ids) >= 2:
        pg.check("#" + ids[0]); pg.check("#" + ids[1]); pg.wait_for_timeout(120)
        check(f"  勾 2 个后 = 2 / {spec['boxes']}",
              pg.inner_text("#tick").startswith(f"2 / {spec['boxes']}"), pg.inner_text("#tick"))
        check("  勾上的条目加删除线",
              "done" in pg.eval_on_selector("#" + ids[0], "e => e.parentNode.className"))
        pg.reload(wait_until="load"); pg.wait_for_timeout(400)
        check(f"  刷新后仍是 2 / {spec['boxes']}（localStorage）",
              pg.inner_text("#tick").startswith(f"2 / {spec['boxes']}"), pg.inner_text("#tick"))
        pg.evaluate(f"localStorage.removeItem('{spec['key']}')")
        pg.reload(wait_until="load"); pg.wait_for_timeout(400)

    body = pg.inner_text("body")
    check("  无字面 ** 残留", "**" not in body, body.count("**"))
    check("  无字面 ` 残留", "`" not in body, body.count("`"))

    hrefs = pg.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
    bad = [h for h in hrefs if not h.startswith(("http", "#")) and not (page.parent / h).exists()]
    check("  所有相对链接文件存在", not bad, bad)

    for w in (1440, 390):
        pg.set_viewport_size({"width": w, "height": 1000}); pg.wait_for_timeout(300)
        ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"  {w}px 无整页横向溢出", ov <= 1, f"溢出 {ov}px")

    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(400)
    pg.screenshot(path=str(SHOTS / f"{spec['shot']}-top.png"))
    pg.screenshot(path=str(SHOTS / f"{spec['shot']}-full.png"), full_page=True)
    pg.set_viewport_size({"width": 390, "height": 900})
    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(400)
    pg.screenshot(path=str(SHOTS / f"{spec['shot']}-mobile.png"))

    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.emulate_media(media="print"); pg.wait_for_timeout(250)
    vis = pg.eval_on_selector("#tick", "e => getComputedStyle(e).display")
    check("  打印态隐藏进度条", vis == "none", vis)
    pg.emulate_media(media="screen")


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else ""
    todo = {k: v for k, v in PAGES.items() if want in k}
    if not todo:
        print("没有匹配的页面：", want)
        return 1
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        for fname, spec in todo.items():
            print(f"\n── {fname} ──")
            run(pg, fname, spec)
        b.close()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results) - n_fail} PASS / {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
