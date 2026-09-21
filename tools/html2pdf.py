"""打印流水线：把 打印资料/*.html 批量转成 A4 PDF（用 Edge/Chrome 无头模式，不需要装任何库）

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


def to_pdf(browser: str, src: Path, profile: Path) -> bool:
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
        src.as_uri(),
    ]
    subprocess.run(cmd, capture_output=True, timeout=90)
    for _ in range(20):                    # 等文件落盘
        if out.exists() and out.stat().st_size > 0:
            return True
        time.sleep(0.3)
    return False


def main() -> int:
    browser = find_browser()
    targets = [Path(a) for a in sys.argv[1:]] or sorted(SRC_DIR.glob("*.html"))
    if not targets:
        print("打印资料/ 里没有 html 文件")
        return 1

    profile = Path(os.environ.get("TEMP", r"E:\Temp")) / "html2pdf-profile"
    profile.mkdir(parents=True, exist_ok=True)

    print(f"浏览器：{Path(browser).name}")
    ok = True
    for src in targets:
        src = src if src.is_absolute() else (ROOT / src)
        if not src.exists():
            print(f"  [跳过] 文件不存在：{src}")
            ok = False
            continue
        good = to_pdf(browser, src, profile)
        size = src.with_suffix(".pdf").stat().st_size if good else 0
        print(f"  [{'OK' if good else '失败'}] {src.name}  ->  {src.with_suffix('.pdf').name}  {size} bytes")
        ok = ok and good
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
