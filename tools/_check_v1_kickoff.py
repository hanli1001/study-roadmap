# -*- coding: utf-8 -*-
"""v1 开工单页面验收 —— 真在浏览器里开一遍、点一遍、刷新一遍。

为什么要有它：
    "打开看一眼"抓不出「刷新后猜测没了」「窄屏横向溢出」「Markdown 反引号漏进正文」
    这一类毛病（W-40 在这个工作区已经复发过 N 次）。所以每条都断成可执行的动作。

用法：
    python -X utf8 tools/_check_v1_kickoff.py
    python -X utf8 tools/_check_v1_kickoff.py --shot
需要：playwright + 本机 Edge（channel="msedge"）
"""
from __future__ import annotations

import re
import sys
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "交互演示" / "v1开工单-20261009.html"
SHOT_DIR = pathlib.Path(r"E:\Temp\agent-scratch\20261008")

PROBE_JS = """() => {
  const txt = document.body.innerText;
  return {
    title: document.title,
    secs: document.querySelectorAll('section.sec').length,
    h2nums: [...document.querySelectorAll('section.sec > h2')].map(h => h.dataset.n),
    guesses: document.querySelectorAll('.guess').length,
    areas: document.querySelectorAll('.guess textarea').length,
    railStops: document.querySelectorAll('.rail2 .st2').length,
    railNow: (document.querySelector('.rail2 .st2.now') || {}).textContent || '',
    details: document.querySelectorAll('details').length,
    starStar: (txt.match(/\\*\\*/g) || []).length,
    backtick: (txt.match(/`/g) || []).length,
    tick: (document.getElementById('tick') || {}).textContent || '',
    gh: !!document.querySelector('a[href*="github.com/hanli1001/ask-my-notes"]'),
    links: [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')),
    // 正文里不该出现的"答案"词 —— 先猜第①题问的是「最大的一个有多大」，
    // 所以只有"最大值"算剧透；文件数和总字数不算（它们回答不了①，且是页面的钩子）。
    leakBeforeFold: (() => {
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('details').forEach(x => x.remove());
      return /170,189|17\\s*万/.test(clone.innerText) ? 'LEAK:max' : 'ok';
    })(),
    areasEmpty: [...document.querySelectorAll('.guess textarea')]
                  .every(a => a.value === ''),
  };
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    want_shot = "--shot" in sys.argv
    if want_shot:
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
    url = "file:///" + urllib.parse.quote(str(PAGE).replace("\\", "/"))
    print("页面：" + str(PAGE))
    print("地址：" + url + "\n")

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
        d = page.evaluate(PROBE_JS)

        check("页面加载无 JS 报错", not errors, "errors=" + repr(errors[:3]))
        check("标题正确", "作品 v1" in d["title"], d["title"])
        check("10 个小节齐全", d["secs"] == 10, f"{d['secs']} 节 · 标记={d['h2nums']}")
        check("4 道先猜题", d["guesses"] == 4 and d["areas"] == 4,
              f"guess={d['guesses']} textarea={d['areas']}")
        check("7 站进度条 + 第 2 站是「现在」",
              d["railStops"] == 7 and "你今天在这" in d["railNow"],
              f"stops={d['railStops']} now={d['railNow'].strip()[:18]!r}")

        # —— Markdown 残留（W-40 家族，这个工作区复发过多次）——
        check("正文无字面 ** 残留", d["starStar"] == 0, f"** × {d['starStar']}")
        check("正文无反引号残留（应是 <code>）", d["backtick"] == 0, f"` × {d['backtick']}")

        # —— 谜底不能泄露在折叠区之外 ——
        check("第①题的答案（最大值）藏在折叠区里", d["leakBeforeFold"] == "ok",
              d["leakBeforeFold"])
        check("全新打开时 4 个猜测框是空的（测试没污染页面）", d["areasEmpty"],
              "全空" if d["areasEmpty"] else "有残留值")
        check("折叠区存在", d["details"] >= 1, f"{d['details']} 个 <details>")
        page.click("details summary")
        page.wait_for_timeout(200)
        opened = page.evaluate("() => document.querySelector('details').open")
        check("折叠区能展开", opened is True, f"open={opened}")

        # —— 外链 / 内链 ——
        check("有 GitHub 仓库链接", d["gh"], "ask-my-notes")
        local = [h for h in d["links"] if h and not h.startswith(("http", "#", "mailto"))]
        missing = [h for h in local if not (PAGE.parent / h.split("?")[0]).exists()]
        check("站内链接都指向真实文件", not missing,
              f"{len(local)} 条：" + (", ".join(missing) if missing else "全部存在"))

        # —— 猜测框：写进去 → 刷新 → 还在（localStorage）——
        page.fill(".guess textarea", "我猜大约 5 万字，因为目测几个 md 都挺长")
        page.wait_for_timeout(150)
        t1 = page.evaluate("() => document.getElementById('tick').textContent")
        page.reload()
        page.wait_for_timeout(400)
        kept = page.evaluate("() => document.querySelector('.guess textarea').value")
        t2 = page.evaluate("() => document.getElementById('tick').textContent")
        check("猜测写进 localStorage 且刷新不丢", "5 万字" in kept, kept[:24] or "(空)")
        check("进度计数随猜测更新", "1 / 4" in t1 and "1 / 4" in t2, f"{t1.strip()} | {t2.strip()}")

        # —— 打勾（本页目前无 .task，保留能力检查：不该崩）——
        check("页面无 .task 时脚本不报错", not errors, "errors=" + repr(errors[:3]))

        # —— 两种宽度：不许横向溢出 ——
        for w in (1440, 390):
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(250)
            ov = page.evaluate(
                "() => { const e = document.documentElement;"
                " return e.scrollWidth - e.clientWidth; }")
            check(f"{w}px 无横向溢出", ov <= 1, f"溢出 {ov}px")

        # —— 打印态：折叠区必须摊开（否则纸上全是「量完之后再展开」）——
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.emulate_media(media="print")
        page.wait_for_timeout(200)
        vis = page.evaluate(
            "() => { const p = document.querySelector('details p');"
            " const cs = getComputedStyle(p); return cs.display; }")
        check("打印态折叠区内容可见", vis != "none", f"details p display={vis}")
        page.emulate_media(media="screen")

        if want_shot:
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.evaluate("() => { document.querySelectorAll('details').forEach(d=>d.open=true); }")
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(250)
            page.screenshot(path=str(SHOT_DIR / "_shot-v1kick-top.png"))
            page.screenshot(path=str(SHOT_DIR / "_shot-v1kick-full.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 900})
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(250)
            page.screenshot(path=str(SHOT_DIR / "_shot-v1kick-mobile.png"))
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.emulate_media(media="print")
            page.pdf(path=str(SHOT_DIR / "_shot-v1kick-print.pdf"), format="A4",
                     print_background=True)
            page.emulate_media(media="screen")
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
