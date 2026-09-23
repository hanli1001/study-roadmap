# 一次性修复器：把"内容里的 ASCII 直引号"换成中文引号「」，但绝不碰代码里的引号。
#
# 判据（只对 "..." 双引号字符串生效）：
#   · 正等着"开引号"时，看它**后一个字符是不是中文** —— 是 → 这是内容（开引号）；不是 → 这是字符串结束符。
#   · 正等着"闭引号"时，直接判定为内容（闭引号）。
#   · 三引号块整段跳过；'...' 原样保留（里面可能装 JSON）；注释行整行照抄。
# 依据：中文引号永远紧贴汉字，而代码里的引号后面跟的是空格/逗号/点/括号。
import ast
import os
import sys
from pathlib import Path

CJK_PUNCT = "、。，；：？！（）《》【】「」『』—…·％%①-⑩"


def is_cjk(c: str) -> bool:
    return "\u4e00" <= c <= "\u9fff" or c in CJK_PUNCT


def main() -> int:
    p = Path(sys.argv[1])
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    out_lines, warnings = [], []
    mode, alt = None, False

    for line in lines:
        i, out, n = 0, [], len(line)
        while i < n:
            ch = line[i]
            if mode is None:
                if ch == "#":
                    out.append(line[i:]); i = n; continue
                if line.startswith('"""', i) or line.startswith("'''", i):
                    mode = "tq"; out.append(line[i:i + 3]); i += 3; continue
                out.append(ch)
                if ch == '"':
                    mode, alt = "dq", False
                elif ch == "'":
                    mode = "sq"
                i += 1; continue
            if mode == "tq":
                if line.startswith('"""', i) or line.startswith("'''", i):
                    mode = None; out.append(line[i:i + 3]); i += 3; continue
                out.append(ch); i += 1; continue
            if mode == "sq":
                out.append(ch)
                if ch == "'" and (i == 0 or line[i - 1] != "\\"):
                    mode = None
                i += 1; continue
            # mode == 'dq'
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                if alt:                                   # 期待闭引号 → 内容
                    out.append("」"); alt = False
                elif i + 1 < n and is_cjk(line[i + 1]):    # 后面紧贴中文 → 内容开引号
                    out.append("「"); alt = True
                else:                                     # 字符串结束
                    out.append(ch); mode = None
            else:
                out.append(ch)
            i += 1
        if mode == "dq" and alt:
            warnings.append(f"line {len(out_lines) + 1}: 字符串结束时仍等着闭引号（内容引号可能是奇数个）")
        if mode == "sq" and os.environ.get("DBG"):
            pass
        out_lines.append("".join(out))

    src = "".join(out_lines)
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"STILL BROKEN line {e.lineno}: {e.msg}")
        print(repr(src.splitlines()[e.lineno - 1][:160]))
        return 1
    if "「" in src:
        if src.count("「") != src.count("」"):
            print(f"UNBALANCED 「={src.count('「')} 」={src.count('」')}")
            return 1
    for w in warnings:
        print("WARN", w)
    p.write_text(src, encoding="utf-8")
    print(f"OK  syntax valid ｜ 「={src.count('「')} 」={src.count('」')} ｜ warnings={len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
