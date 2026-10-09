# -*- coding: utf-8 -*-
"""变式题页面验收 —— 真在浏览器里开一遍、填一遍、刷新一遍、打印态看一眼。

存在的理由（同 `_check_v1_kickoff.py`）：
    这类页面最容易坏的三个地方，靠"打开看一眼"都抓不到 ——
    ① 谜底从折叠区外面漏出去（W-56）
    ② Markdown 反引号 / `**` 漏进正文（W-40，本工作区复发过多次）
    ③ 窄屏横向溢出、打印态折叠区不摊开

用法：
    python -X utf8 tools/_check_variants.py
    python -X utf8 tools/_check_variants.py --shot
"""
from __future__ import annotations

import sys
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "交互演示" / "变式题-v1第1步-20261009.html"
SHOT_DIR = ROOT / "交互演示"

# 「先猜再跑」那几题的答案 —— 展开折叠区之前，整页文本里一个都不许出现
SECRETS = ["12,014", "1,257", "11,990", "11,999", "1,762,106", "170,189"]

PROBE_JS = """(secrets) => {
  const txt = document.body.innerText;
  const clone = document.body.cloneNode(true);
  clone.querySelectorAll('details').forEach(x => x.remove());
  const outside = clone.innerText;
  const leaked = secrets.filter(s => outside.includes(s));
  return {
    title: document.title,
    secs: document.querySelectorAll('section.sec').length,
    nums: [...document.querySelectorAll('section.sec > h2')].map(h => h.dataset.n),
    guesses: document.querySelectorAll('.guess').length,
    areas: document.querySelectorAll('.guess textarea').length,
    tasks: document.querySelectorAll('.task input').length,
    details: document.querySelectorAll('details').length,
    leaked: leaked,
    starStar: (txt.match(/\\*\\*/g) || []).length,
    backtick: (txt.match(/`/g) || []).length,
    tick: (document.getElementById('tick') || {}).textContent || '',
    links: [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')),
    areasEmpty: [...document.querySelectorAll('.guess textarea')].every(a => a.value === ''),
  };
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    want_shot = "--shot" in sys.argv
    url = "file:///" + urllib.parse.quote(str(PAGE).replace("\\", "/"))
    print("页面：" + str(PAGE) + "\n")

    results: list[tuple[bool, str, str]] = []

    def check(name: str, cond: bool, detail: str) -> None:
        results.append((bool(cond), name, detail))
        print(("  [PASS] " if cond else "  [FAIL] ") + name + "  —— " + detail)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(url)
        page.wait_for_timeout(400)
        d = page.evaluate(PROBE_JS, SECRETS)

        check("页面加载无 JS 报错", not errors, repr(errors[:3]))
        check("标题正确", "变式题" in d["title"], d["title"])
        check("9 个小节齐全", d["secs"] == 9, f"{d['secs']} 节 · {d['nums']}")
        check("猜测框 10 个 / 打勾 6 个", d["areas"] == 10 and d["tasks"] == 6,
              f"textarea={d['areas']} checkbox={d['tasks']} guess块={d['guesses']}")
        check("折叠区存在", d["details"] >= 4, f"{d['details']} 个 <details>")

        # —— W-56：谜底不能在折叠区之外 ——
        check("五道题的答案全部只在折叠区里", not d["leaked"],
              ("泄漏：" + ", ".join(d["leaked"])) if d["leaked"] else "折叠区外一个都没有")
        check("全新打开时猜测框全空（测试没污染页面）", d["areasEmpty"],
              "全空" if d["areasEmpty"] else "有残留值")

        # —— W-40 家族 ——
        check("正文无字面 ** 残留", d["starStar"] == 0, f"** × {d['starStar']}")
        check("正文无反引号残留（应是 <code>）", d["backtick"] == 0, f"` × {d['backtick']}")

        # —— 链接 ——
        local = [h for h in d["links"] if h and not h.startswith(("http", "#", "mailto"))]
        missing = [h for h in local if not (PAGE.parent / h.split("?")[0]).exists()]
        check("站内链接都指向真实文件", not missing,
              f"{len(local)} 条：" + ("、".join(missing) if missing else "全部存在"))

        # —— 折叠区能开 ——
        page.click("details summary")
        page.wait_for_timeout(150)
        check("折叠区能展开", page.evaluate("() => document.querySelector('details').open") is True,
              "ok")

        # —— 填 → 刷新 → 还在 ——
        page.fill(".guess textarea", "我猜大约 8000 个")
        page.check("#k1")
        page.wait_for_timeout(150)
        t1 = page.evaluate("() => document.getElementById('tick').textContent")
        page.reload()
        page.wait_for_timeout(400)
        kept = page.evaluate("() => document.querySelector('.guess textarea').value")
        boxed = page.evaluate("() => document.getElementById('k1').checked")
        t2 = page.evaluate("() => document.getElementById('tick').textContent")
        check("猜测刷新不丢", "8000" in kept, kept[:20] or "(空)")
        check("打勾刷新不丢", boxed is True, str(boxed))
        check("进度计数正确", "1 / 10" in t1 and "1 / 6" in t1 and "1 / 10" in t2,
              f"{t1.strip()} | {t2.strip()}")

        # —— 两种宽度 ——
        for w in (1440, 390):
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(250)
            ov = page.evaluate("() => document.documentElement.scrollWidth"
                               " - document.documentElement.clientWidth")
            check(f"{w}px 无横向溢出", ov <= 1, f"溢出 {ov}px")

        # —— 打印态：折叠区必须摊开 ——
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.emulate_media(media="print")
        page.wait_for_timeout(200)
        vis = page.evaluate("() => getComputedStyle(document.querySelector('details p')).display")
        check("打印态折叠区内容可见", vis != "none", f"display={vis}")
        page.emulate_media(media="screen")

        if want_shot:
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.evaluate("() => { document.querySelectorAll('details').forEach(x => x.open = true);"
                          " window.scrollTo(0, 0); }")
            page.wait_for_timeout(300)
            page.screenshot(path=str(SHOT_DIR / "_shot-vary-top.png"))
            page.screenshot(path=str(SHOT_DIR / "_shot-vary-full.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 900})
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(250)
            page.screenshot(path=str(SHOT_DIR / "_shot-vary-mobile.png"))
            print("\n截图 → " + str(SHOT_DIR))

        browser.close()

    npass = sum(1 for ok, _, _ in results if ok)
    print(f"\n{'='*62}\n{npass} PASS / {len(results)-npass} FAIL   共 {len(results)} 项\n{'='*62}")
    for ok, name, detail in results:
        if not ok:
            print("  FAIL: " + name + " —— " + detail)
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
