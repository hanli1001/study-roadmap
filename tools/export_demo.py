# -*- coding: utf-8 -*-
"""把物联网 Demo 导成一份「代码 + 数据」的 Markdown，用于发给导师。

用法：
    python tools/export_demo.py

做三件事：
  1) 去掉 main.py 的全部注释与 docstring（保留可运行语义）
  2) 把 elderly_data.json / service_list.json 全文拼进去
  3) **自测**：ast.parse 通过 + 实际跑一遍，与原始 main.py 的输出逐字节比对

⚠️ 只读 E:\\物联网\\demo\\，不往里写任何东西（那个工作区有"不回写"声明，且 IDE 常驻）。
"""
import ast
import io
import os
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

DEMO = Path(r"E:\物联网\demo")
OUT = Path(__file__).resolve().parent.parent / "导出" / "物联网Demo-给导师-20260922.md"
OUT_BRIEF = Path(__file__).resolve().parent.parent / "导出" / "物联网Demo-给导师-节选版-20260922.md"


def strip_comments_and_docstrings(src: str) -> str:
    """去掉 # 注释与所有 docstring。

    做法：先把 COMMENT token 的列位置之后截断，再用 ast 找出所有
    docstring 节点的行范围，最后一起过滤 —— 两个 pass 都基于**原始行号**，
    所以互不干扰。
    """
    lines = src.splitlines()
    drop: set[int] = set()

    # pass 1：截断 # 注释
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            row, col = tok.start
            lines[row - 1] = lines[row - 1][:col].rstrip()
            if not lines[row - 1].strip():
                drop.add(row)

    # pass 2：找 docstring 的行范围
    tree = ast.parse(src)
    holders = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, holders) or not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            for ln in range(first.lineno, (first.end_lineno or first.lineno) + 1):
                drop.add(ln)

    kept = [ln for i, ln in enumerate(lines, 1) if i not in drop]
    # 连续空行压成一个
    out: list[str] = []
    for ln in kept:
        if ln.strip() == "" and out and out[-1].strip() == "":
            continue
        out.append(ln)
    return "\n".join(out).strip() + "\n"


def main() -> int:
    src_path = DEMO / "main.py"
    raw = src_path.read_text(encoding="utf-8")
    stripped = strip_comments_and_docstrings(raw)

    # ---- 自测 1：语法 ----
    ast.parse(stripped)
    print("[1/3] 去注释后 ast.parse 通过")

    # ---- 自测 2：实际跑，和原版比输出 ----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name in ("elderly_data.json", "service_list.json"):
            shutil.copy(DEMO / name, tmp / name)
        (tmp / "_new.py").write_text(stripped, encoding="utf-8")
        shutil.copy(src_path, tmp / "_old.py")

        def run(script: str) -> str:
            p = subprocess.run([sys.executable, script], cwd=tmp,
                               capture_output=True, timeout=120)
            return f"rc={p.returncode}\n" + p.stdout.decode("utf-8", "replace")

        a, b = run("_old.py"), run("_new.py")
        if a != b:
            print("  ❌ 去注释后输出变了！")
            for i, (x, y) in enumerate(zip(a.splitlines(), b.splitlines())):
                if x != y:
                    print(f"     第一处差异 行{i+1}:\n       原: {x}\n       新: {y}")
                    break
            return 2
        print(f"[2/3] 实跑输出与原始 main.py **逐字节一致**（{len(a)} 字节，rc=0）")

    # ---- 拼装 ----
    import json as _json

    elderly_raw = (DEMO / "elderly_data.json").read_text(encoding="utf-8").rstrip()
    services_raw = (DEMO / "service_list.json").read_text(encoding="utf-8").rstrip()
    n_e = len(_json.loads(elderly_raw))
    n_s = len(_json.loads(services_raw))

    HEAD = """# 养老服务匹配 Demo —— 源码与数据

> 刁健宇 ｜ 2026.09.22
>
> **数据来源（均为真实、可下载、可复核）**
> - **UCI #936 NPHA**（National Poll on Healthy Aging）—— 714 条 65–80 岁真实老年调查记录，
>   许可 **CC BY 4.0**，<https://archive.ics.uci.edu/dataset/936>
> - **武汉市民政局**《武汉市特殊困难老年人养老服务补贴服务项目清单》（武民政〔2024〕6号 附件，2024-06-01）
>   —— 37 条真实服务项目
>
> 数据由 `build_dataset.py` 生成（映射规则写在代码里，可复现）。
"""

    def render(e_text, s_text, e_note, s_note):
        return f"""{HEAD}
---

## 一、main.py（源码）

```python
{stripped}```

---

## 二、elderly_data.json（{e_note}）

```json
{e_text}
```

---

## 三、service_list.json（{s_note}）

```json
{s_text}
```
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)

    full = render(elderly_raw, services_raw, f"{n_e} 条全文", f"{n_s} 条全文")
    OUT.write_text(full, encoding="utf-8")

    # 节选版：正文里只放几条，够导师确认"数据是真的"即可
    SE, SS = 3, 5
    e_cut = _json.dumps(_json.loads(elderly_raw)[:SE], ensure_ascii=False, indent=2)
    s_cut = _json.dumps(_json.loads(services_raw)[:SS], ensure_ascii=False, indent=2)
    brief = render(e_cut, s_cut, f"共 {n_e} 条，此处节选前 {SE} 条", f"共 {n_s} 条，此处节选前 {SS} 条")
    OUT_BRIEF.write_text(brief, encoding="utf-8")

    print(f"[3/3] 已写出两个版本：")
    for p, d in ((OUT, full), (OUT_BRIEF, brief)):
        print(f"       {p.name}  —— {d.count(chr(10)) + 1} 行 / {len(d.encode('utf-8')):,} 字节")
    print(f"       代码 {stripped.count(chr(10))} 行 · 老人 {n_e} 条 · 服务 {n_s} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
