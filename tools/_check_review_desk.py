# -*- coding: utf-8 -*-
"""复习台页面验收 —— 真在浏览器里点一遍，不靠读源码。

为什么要有它（2026-10-05）：
    复习台原来写着「点下表里的卡直接补过，补完就少一格」，但**全页唯一可点的入口只标当前档**，
    1 天档 / 3 天档的格子打开是 33 格，把今天列出的 11 张全点「会了」之后**还是剩 22 格，
    而且永远清不掉**。这个 bug 靠"打开看一眼"是看不出来的 —— 页面上红字确实在减少
    （33 → 22），只有**把该点的都点完、再数还剩几格**才暴露。

    所以这个脚本的判定核心是那句：**点完所有能点的，账必须归零。**

用法：
    python -X utf8 tools/_check_review_desk.py
    python -X utf8 tools/_check_review_desk.py --shot     # 顺便截图到 E:\\Temp\\agent-scratch

需要：playwright + 本机 Edge（channel="msedge"）

注意：页面状态存在 localStorage，脚本每条用例都先 clear()，
      否则上一次跑完的勾会带进来（"刷新后仍然是 11/11"这类断言会假通过）。
"""
from __future__ import annotations

import sys
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "交互演示" / "复习台.html"
SHOT_DIR = pathlib.Path(r"E:\Temp\agent-scratch\2026-10-05")

SNAP_JS = """() => {
  const q = s => (document.querySelector(s) || {}).textContent || '';
  const sec = document.querySelector('#overdue');
  return {
    round: q('#tRound').trim(), total: q('#tTotal'), done: q('#tDone'),
    overdueHidden: sec.hasAttribute('hidden'),
    overdueMsg: q('#overdueMsg').replace(/\\s+/g, ' ').trim(),
    overdueCards: document.querySelectorAll('#overdueList .guess').length,
    overdueBtns: document.querySelectorAll('#overdueList button').length,
    calRows: [...document.querySelectorAll('#calBody tr')]
                .map(tr => [...tr.children].map(td => td.textContent.trim()).join(' | ')),
  };
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    want_shot = "--shot" in sys.argv
    if want_shot:
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
    url = "file:///" + urllib.parse.quote(str(PAGE).replace("\\", "/"))

    results: list[tuple[bool, str, str]] = []

    def check(name: str, cond: bool, detail: str) -> None:
        results.append((bool(cond), name, detail))
        print(("  [PASS] " if cond else "  [FAIL] ") + name + "  —— " + detail)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(url)
        page.evaluate("() => localStorage.clear()")
        page.reload()
        page.wait_for_timeout(500)

        # ── ① 打开：账目应当自洽 ──────────────────────────────
        a = page.evaluate(SNAP_JS)
        print("\n① 打开页面（localStorage 空）")
        print(f"   档位 {a['round']} ｜ 今天列出 {a['total']} 张 ｜ 已过 {a['done']}")
        print(f"   逾期 {a['overdueMsg']}")
        check("今天这档是 7 天档（起算 09.23 + 7 = 09.30）", "7 天档" in a["round"], a["round"])
        check("今天列出全部 11 张卡", a["total"] == "11", f"total={a['total']}")
        check("逾期 = 22 格（11 张 × 欠 1 天档 + 3 天档）",
              "有 22 格" in a["overdueMsg"], a["overdueMsg"][:22])
        check("逾期区渲染成 11 张可补卡", a["overdueCards"] == 11, f"cards={a['overdueCards']}")
        check("逾期区按钮 = 22（11 看答案 + 11 补过）",
              a["overdueBtns"] == 22, f"btns={a['overdueBtns']}")
        if want_shot:
            page.screenshot(path=str(SHOT_DIR / "review-2-overdue.png"), full_page=True)

        # ── ② 今天这档全过 ────────────────────────────────────
        n = 0
        while n < 40:
            btn = page.query_selector("#tList .guess button:text-is('会了')")
            if not btn:
                break
            btn.click()
            page.wait_for_timeout(40)
            n += 1
        b = page.evaluate(SNAP_JS)
        print(f"\n② 今天这档点「会了」× {n}")
        check("今天 11/11 过完", b["done"] == "11", f"done={b['done']}")
        check("★ 过完今天这档后，逾期仍是**可补**状态（不是永远清不掉的死账）",
              b["overdueCards"] == 11, f"可补卡={b['overdueCards']}")

        # ── ③ 逾期区逐张补过 → 必须归零 ───────────────────────
        m = 0
        while m < 40:
            btn = page.query_selector("#overdueList .guess button.primary")
            if not btn:
                break
            btn.click()
            page.wait_for_timeout(40)
            m += 1
        c = page.evaluate(SNAP_JS)
        print(f"\n③ 逾期区点「补过」× {m}")
        for row in c["calRows"]:
            print("   " + row)
        check("★ 22 格全部清得掉，逾期区归零", c["overdueHidden"] is True,
              f"hidden={c['overdueHidden']}")
        check("★ 隐藏的同时 DOM 也清空（不留看不见的死按钮）",
              c["overdueCards"] == 0 and c["overdueBtns"] == 0,
              f"cards={c['overdueCards']} btns={c['overdueBtns']}")
        check("补过记成 late：日历早档显示 `n/n *`，不伪装成当天做的",
              all("*" in r.split("|")[1] and "*" in r.split("|")[2] for r in c["calRows"]),
              c["calRows"][0])
        check("补过只动早档：7 天档是今天真做的（4/4 **不带** `*`）、30 天档没动",
              "*" not in c["calRows"][0].split("|")[3] and "0 / 4" in c["calRows"][0].split("|")[4],
              c["calRows"][0])
        if want_shot:
            page.screenshot(path=str(SHOT_DIR / "review-4-calendar.png"), full_page=True)

        # ── ④ 刷新：localStorage 要扛住 ───────────────────────
        page.reload()
        page.wait_for_timeout(500)
        d = page.evaluate(SNAP_JS)
        print("\n④ 刷新页面")
        check("刷新后逾期区仍为空", d["overdueHidden"] is True, f"hidden={d['overdueHidden']}")
        check("刷新后今天这档仍 11/11", d["done"] == "11", f"done={d['done']}")
        check("刷新后日历仍是 `*` 标记", "*" in d["calRows"][0], d["calRows"][0])

        # ── ⑤ 打印态（W-42：复习台打印出来一个答案都没有）────
        page.emulate_media(media="print")
        page.wait_for_timeout(300)
        pr = page.evaluate("""() => ({
            overdueVisible: getComputedStyle(document.querySelector('#overdue')).display,
            allCount: document.querySelectorAll('#allCardsBody .guess').length,
        })""")
        check("打印态隐去逾期区（那里全是按钮）", pr["overdueVisible"] == "none",
              f"display={pr['overdueVisible']}")
        check("打印态答案全量在（11 张，W-42 的教训）", pr["allCount"] == 11,
              f"printAll cards={pr['allCount']}")
        page.emulate_media(media="screen")

        # ── ⑥ 收尾：不留测试污染 ──────────────────────────────
        page.evaluate("() => localStorage.clear()")
        page.reload()
        page.wait_for_timeout(400)
        e = page.evaluate(SNAP_JS)
        check("清 localStorage 后回到初始 22 格（无残留污染）",
              "有 22 格" in e["overdueMsg"], e["overdueMsg"][:22])

        browser.close()

    ok = sum(1 for c, _, _ in results if c)
    print(f"\n================ {ok} / {len(results)} PASS ================")
    for c, name, detail in results:
        if not c:
            print("  FAIL:", name, "|", detail)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
