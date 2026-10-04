"""打印流水线：把 打印资料/*.html 批量转成 A4 PDF（用 Edge/Chrome 无头模式，不需要装任何库）

⏸ 默认不跑（2026-10-05 学员定：交付物只出 HTML，要纸自己 Ctrl+P）。
   只有学员明确说「要 PDF」时才用这个脚本 —— 别再顺手生成。

用法：
    python tools/html2pdf.py                  # 转 打印资料/ 下全部 html
    python tools/html2pdf.py 某个文件.html     # 只转一个

原理：Edge 的 --print-to-pdf + HTML 里的 @page 打印样式。
注意：路径要传 Windows 形式（反斜杠），否则 browser 会静默不产出文件。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "打印资料"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    raise SystemExit("找不到 Edge/Chrome —— 装一个或用浏览器手动「打印 → 另存为 PDF」")


def file_url(p: Path) -> str:
    r"""Windows 绝对路径 → Edge 能吃的 file URL。

    ⚠️ 别改回 p.as_uri()！实测（2026-09-21，Edge headless=new）：
        file:///E:\项目学习\打印资料\x.html      → 成功，出 PDF
        file:///E:/%E9%A1%B9%E7%9B%AE.../x.html  （as_uri 的编码正斜杠形式）
                                                → **静默不产出任何文件，退出码还是 0**
    这条坑极其阴险：命令不报错、也不出文件，容易被当成"生成好了"。
    所以 to_pdf() 里必须验文件大小，不能只看退出码。
    """
    return "file:///" + str(p)


def split_query(raw: str) -> tuple[Path, str]:
    """拆出 `路径?查询串`。

    为什么需要：同一个页面要能出不同的 PDF —— 例如函数卡册全量 38 页太重，
    学员真正会打印的只是「现在」那 24 张（约 8 页）。靠 URL 查询串切换打印子集，
    就不必维护第二份 HTML（两份必然各自变旧）。
    """
    if "?" in raw:
        path, q = raw.split("?", 1)
        return Path(path), "?" + q
    return Path(raw), ""


def to_pdf(browser: str, src: Path, profile: Path, query: str = "") -> bool:
    out = src.with_suffix(".pdf")
    if out.exists():
        out.unlink()                       # 先删，避免"旧文件被当成成功"
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-pdf-header-footer",          # 不要浏览器自带的页眉页脚
        f"--user-data-dir={profile}",
        f"--print-to-pdf={out}",
        file_url(src) + query,
    ]
    subprocess.run(cmd, capture_output=True, timeout=90)
    # 等文件落盘。别把轮询调太短：中文内容多、表格大的页面可能 10 秒以上才写完，
    # 实测 6 秒会把已经生成好的 PDF 误判成"失败"（文件其实随后就出现了）。
    for _ in range(90):                    # 90 × 0.5s = 最多等 45 秒
        if out.exists() and out.stat().st_size > 0:
            # 再确认一次大小稳定，避免把"正在写"当成"写完了"
            size = out.stat().st_size
            time.sleep(0.4)
            if out.exists() and out.stat().st_size == size:
                return True
        time.sleep(0.5)
    return False


def main() -> int:
    browser = find_browser()
    targets = [split_query(a) for a in sys.argv[1:]] or [(p, "") for p in sorted(SRC_DIR.glob("*.html"))]
    if not targets:
        print("打印资料/ 里没有 html 文件")
        return 1

    profile = Path(os.environ.get("TEMP", r"E:\Temp")) / "html2pdf-profile"
    profile.mkdir(parents=True, exist_ok=True)

    print(f"浏览器：{Path(browser).name}")
    ok = True
    for src, query in targets:
        src = src if src.is_absolute() else (ROOT / src)
        if not src.exists():
            print(f"  [跳过] 文件不存在：{src}")
            ok = False
            continue
        good = to_pdf(browser, src, profile, query)
        size = src.with_suffix(".pdf").stat().st_size if good else 0
        print(f"  [{'OK' if good else '失败'}] {src.name}  ->  {src.with_suffix('.pdf').name}  {size} bytes")
        ok = ok and good
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
