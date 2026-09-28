# Git 基础学习笔记

> 2026.07.07 · 大一暑假 · 第一次 Git 实战

---

## 一、Git 是什么

Git 是**版本控制系统**。它记录文件的每一次修改历史，让你可以随时回到任何版本。

```
传统方式：论文_v1.docx → 论文_v2.docx → 论文_最终版.docx → 论文_真的最终版.docx
Git 方式： 一个文件 + 一条提交历史时间线
```

## 二、三个核心区域

```
 工作区                   暂存区                   版本库
(你的文件夹)    ──git add──▶   (购物车)    ──git commit──▶   (.git 隐藏文件夹)
  红色 Untracked/modified     绿色 Changes to be committed     永久保存在历史记录
```

| 区域 | 是什么 | 文件状态 |
|------|--------|----------|
| 工作区 | 你正在编辑的文件 | 红色（未追踪/已修改） |
| 暂存区 | 本次要保存的"购物车" | 绿色（待提交） |
| 版本库 | 永久历史记录 | 已存档 |

## 三、常用命令速查

| 命令 | 作用 | 示例 |
|------|------|------|
| `git init` | 初始化仓库 | `git init` |
| `git status` | 查看当前状态 | `git status` |
| `git add <文件>` | 加入暂存区 | `git add main.py` |
| `git commit -m "说明"` | 永久保存一个版本 | `git commit -m "修复登录bug"` |
| `git diff` | 查看具体改了什么 | `git diff` |
| `git log` | 查看提交历史 | `git log --oneline` |
| `git checkout -b <分支名>` | 创建并切换分支 | `git checkout -b dev` |
| `git checkout <分支名>` | 切换到已有分支 | `git checkout main` |
| `git merge <分支名>` | 合并分支到当前分支 | `git merge dev` |
| `git push` | 推送到 GitHub | `git push` |
| `git pull` | 从 GitHub 拉取更新 | `git pull` |
| `git remote -v` | 查看远程仓库地址 | `git remote -v` |

## 四、分支模型

```
main ─────●────────────────────●──   (稳定版本/正式版)
            ╲                  ╱
dev ─────────●────●────●─────    (开发分支/实验改动)
                        ↑
                     git merge 把 dev 合入 main
```

- **main**：主分支，正式版本，永远保持可运行
- **dev / feature**：开发分支，在上面做实验性修改，改完再合并回 main

## 五、日常工作流

```
1. git checkout -b feature-xxx     # 创建新分支
2. 在 PyCharm/VS Code 里改代码
3. git status                      # 看改了什么
4. git diff                        # 看具体差异
5. git add <文件>                  # 加入购物车
6. git commit -m "做了什么"        # 结账保存
7. git checkout main               # 切回主分支
8. git merge feature-xxx           # 合并
9. git push                        # 推到 GitHub
```

**最小循环（日常 90% 的情况）：**

```
改代码 → git add → git commit → git push
```

## 六、远程仓库 (origin)

`origin` 是 GitHub 仓库地址的**别名**。

实际地址：`git@github.com:hanli1001/study-roadmap.git`
别名：`origin`

所以 `git push origin main` = 推到 GitHub 仓库的 main 分支
`git push` 省略时默认推到 origin

## 七、踩过的坑

| 坑 | 原因 | 解决 |
|----|------|------|
| `.gitignore` 不生效 | PowerShell `echo >` 输出 UTF-16 编码，Git 读不懂 | 用 VS Code / PyCharm / Bash `printf` 写配置文件 |
| `git auth` 不是 Git 命令 | 搞混了 `git` 和 `gh`（GitHub CLI） | `git` = 版本控制，`gh` = GitHub 操作 |

## 八、工具分工

| 做什么 | 用什么 |
|--------|--------|
| 写代码、改文件 | PyCharm / VS Code |
| Git 命令 | 终端（PowerShell） |
| .gitignore、配置文件 | VS Code / PyCharm（别用 PowerShell echo） |

---

*第一个仓库：https://github.com/hanli1001/study-roadmap*
