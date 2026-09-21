"""判分器自检（用权威正解跑一遍，确认"全绿"）—— 我用来验证 two_pointer_自测.py 的判分逻辑。

用法：python tools/verify_pointer_grader.py
它做三件事：
  1. 把 样例代码库/two_pointer_自测.py 备份成 .bak-verify
  2. 把四个函数体替换成权威正解（保留你原来的实现不动，只在替换前的文件上动手）
  3. 跑判分 → 期望 25/25 全绿
  4. 用备份恢复原文件（**不会丢你的代码**，除非进程被强杀）
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "样例代码库" / "two_pointer_自测.py"
BACKUP = TARGET.with_suffix(".py.bak-verify")

# 权威正解（与 two_pointer_自测.py 末尾注释里的参考答案一致）
ANSWERS = {
    "two_sum_sorted": '''    L, R = 0, len(nums) - 1
    while L < R:
        s = nums[L] + nums[R]
        if s == target:
            return [L, R]
        elif s > target:
            R -= 1
        else:
            L += 1
    return []''',
    "max_area": '''    L, R, best = 0, len(heights) - 1, 0
    while L < R:
        best = max(best, (R - L) * min(heights[L], heights[R]))
        if heights[L] < heights[R]:
            L += 1
        else:
            R -= 1
    return best''',
    "move_zeroes": '''    pos = 0
    for i in range(len(nums)):
        if nums[i] != 0:
            nums[pos], nums[i] = nums[i], nums[pos]
            pos += 1''',
    "is_palindrome": '''    L, R = 0, len(s) - 1
    while L < R:
        if s[L] != s[R]:
            return False
        L += 1
        R -= 1
    return True''',
}

STUB_TAIL = '# ══════════════════════════════════════════════════════════\n# 判分（不用改）'


def extract_body(text, name):
    """抓出某个函数的函数体（去掉 docstring），到下一个顶层定义为止。"""
    m = re.search(
        r'(def ' + name + r'\(.*?\n)((?:    """.*?"""\n)?)(.*?)(?=\n\n\n|\n# |\Z)',
        text, re.S)
    if not m:
        return None, None, None
    return m.group(1) + m.group(2), m.group(2), m.group(3)


def main():
    if not TARGET.exists():
        print("找不到目标文件", TARGET); return 1
    src = TARGET.read_text(encoding="utf-8")

    rebuilt = src
    for name, body in ANSWERS.items():
        head, doc, old_body = extract_body(rebuilt, name)
        if head is None:
            print(f"抓不到 {name} 的函数体"); return 1
        new_body = "\n" + body + "\n"
        rebuilt = rebuilt.replace(head + old_body, head + new_body, 1)

    shutil.copy2(TARGET, BACKUP)
    try:
        TARGET.write_text(rebuilt, encoding="utf-8")
        r = subprocess.run([sys.executable, str(TARGET)],
                           capture_output=True, text=True, encoding="utf-8",
                           timeout=180, env={"PYTHONIOENCODING": "utf-8", "PATH": __import__("os").environ["PATH"]})
        out = r.stdout
        reds = [l for l in out.splitlines() if "❌" in l or "⏱️" in l]
        verdict = [l for l in out.splitlines() if "全绿" in l or "进度" in l]
        print("\n".join(verdict))
        print(f"失败/超时条数：{len(reds)}")
        for l in reds[:5]:
            print("  ", l.strip())
        return 0 if not reds else 2
    finally:
        shutil.move(str(BACKUP), str(TARGET))
        print("已恢复你的原文件 ✅")


if __name__ == "__main__":
    sys.exit(main())
