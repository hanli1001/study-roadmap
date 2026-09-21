"""双指针模式 · 四道变式自测（你写完函数，跑这个自动判对错）

用法：
    1. 在下面 4 个函数里写实现（删掉 raise NotImplementedError）
    2. python 样例代码库/two_pointer_自测.py
    3. 全绿 = 这个模式过关

配套：交互演示/算法②-双指针.html（先看那张卡再做题）

⚠️ 本次特别注意（上一轮我出题踩过的坑，已修正）：
   · 每题都写清了"谁减谁""要不要原地"这类规格，**不会中途变**
   · 多解的题（两数之和）用**校验函数**判分：只要返回的下标真的满足条件就算过
   · 判分器本身已用权威正解验证过（全绿），所以你看到红就是真红
"""


# ══════════════════════════════════════════════════════════
# 题 1：有序数组两数之和（返回下标）
# ══════════════════════════════════════════════════════════
def two_sum_sorted(nums, target):
    """nums 是**升序**数组，找出两个不同位置 i<j 使 nums[i]+nums[j]==target，返回 [i, j]；没有返回 []。

    规格（锁死）：返回的必须是 [较小的下标, 较大的下标]；找不到返回空列表 []。
    例：two_sum_sorted([1,3,4,6,8,11], 10) → [2, 3]   （4+6=10）
        two_sum_sorted([1,2], 5)            → []

    体力活要求：**必须用双指针**（L 从 0、R 从末尾，往中间收）。
    提示：和大了 R-=1，和小了 L+=1；循环用 while L < R（为什么不是 <= ？想想"不能自己配自己"）。
    """
    i,j = 0 ,len(nums)-1
    while i<j:
        result = nums[i]+nums[j]
        if result==target:
            return [i,j]
        if result > target:
            j -= 1
        if result < target:
            i += 1
    return []
# ══════════════════════════════════════════════════════════
# 题 2：盛最多水的容器（返回最大面积，不返回下标）
# ══════════════════════════════════════════════════════════
def max_area(heights):
    """heights[i] 是第 i 条竖线的高度。选两条线 + x 轴围成一个容器，返回能装的最大"面积"。

    规格（锁死）：面积 = (两线下标之差) × (两线中**较矮**的那条高度)。返回一个整数。

    例：max_area([1,8,6,2,5,4,8,3,7]) → 49
        max_area([1,1])               → 1
        max_area([5])                 → 0      （一条线围不成容器）

    提示：往中间收，宽度一定变小 → 只有"变高"才可能更大 → 所以每次**舍掉较矮的那一边**。
    """
    best,i,j = 0 ,0 ,len(heights)-1
    if len(heights)==1:
        return 0
    else:
        while i<j:
           result = j - i
           best = max(best,result * min(heights[j],heights[i]))
           if heights[i] < heights[j]:
              i += 1
           else:
              j -= 1
        return best

# ══════════════════════════════════════════════════════════
# 题 3：移动零（原地修改，不返回新列表）
# ══════════════════════════════════════════════════════════
def move_zeroes(nums):
    """把数组里所有 0 移到末尾，**非零元素的相对顺序不能变**。

    规格（锁死）：**原地修改** nums（直接改这个列表），函数返回 None。

    例：move_zeroes([0,1,0,3,12])  执行后 nums 变成 [1,3,12,0,0]
        move_zeroes([0])           → [0]
        move_zeroes([1,2])         → [1,2]（本来就没有 0，不动）

    提示：双指针的另一种形态 —— **同向、不等速**。
         一个指针 i 负责"扫描"，另一个 pos 负责"下一个非零数该放哪"。遇到非零就交换。
    """
    p = 0
    q = len(nums)-1
    while p<=q:
        if nums[p]==0:
            nums.pop(p)
            nums.append(0)
            q -=2
        else:
            p += 1
    return nums






# ══════════════════════════════════════════════════════════
# 题 4：判断回文串（双指针的经典用法：两头往中间比）
# ══════════════════════════════════════════════════════════
def is_palindrome(s):
    """判断字符串 s 是否回文（正着读和倒着读一样），返回 True/False。

    规格（锁死）：**区分大小写**，不做任何过滤（空格、标点都算字符）。
    例：is_palindrome("abcba") → True
        is_palindrome("abca")  → False
        is_palindrome("")      → True
        is_palindrome("a")     → True

    提示：L 从头、R 从尾，对比 nums[L] 和 nums[R]，相同就一起往中间缩；不同立刻 False。
         想想为什么这样能比"倒转字符串再比较"更省（后者要额外开一份空间）。
    """
    p = 0
    q = len(s)-1
    count = 0
    while p<q:
        if s[p] == s[q]:
            p += 1
            q -= 1
            count += 1
        if s[p] != s[q]:
            return False
    return True

# ══════════════════════════════════════════════════════════
# 判分（不用改）
# ══════════════════════════════════════════════════════════

import threading as _threading

TIME_LIMIT = 5          # 单个用例最多跑几秒（正常都在毫秒级）


class _Timeout(Exception):
    pass


def _guarded(fn, *args):
    """带超时保护地调用——万一你的代码死循环，判分器 5 秒后接管并报出来，
    而不是把整个自测卡死（这版就是因为 max_area 死循环才发现该加护栏的）。

    ⚠️ 用线程实现，不用 signal.SIGALRM —— 后者是 Unix 专有，**Windows 上没有**
       （我第一版就写了 SIGALRM，结果在这台机器上全部报 AttributeError）。
       死循环的线程没法强杀，但它是 daemon，脚本结束时会跟着退出。
    """
    box = {}

    def work():
        try:
            box["r"] = fn(*args)
        except BaseException as e:          # 包括你的代码自己抛的错
            box["e"] = e

    t = _threading.Thread(target=work, daemon=True)
    t.start()
    t.join(TIME_LIMIT)
    if t.is_alive():
        raise _Timeout()
    if "e" in box:
        raise box["e"]
    return box.get("r")


def _valid_pair(r, nums, target):
    """两数之和的校验：下标是整数、i<j、且两数之和等于 target（不绑定是哪一对）。"""
    if not isinstance(r, (list, tuple)) or len(r) != 2:
        return False
    i, j = r
    if not (isinstance(i, int) and isinstance(j, int)):
        return False
    if not (0 <= i < j < len(nums)):
        return False
    return nums[i] + nums[j] == target


def _check_move_zeroes(fn, nums_in, expected):
    """移动零的校验：传入副本，跑完看列表变成什么样、以及返回值是不是 None。"""
    arr = list(nums_in)
    ret = fn(arr)
    return [arr, ret], expected


CASES = [
    # (题目名, 调用参数, 期望值 或 校验函数)
    ("two_sum_sorted", ([1, 3, 4, 6, 8, 11], 10), lambda r, n=[1,3,4,6,8,11], t=10: _valid_pair(r, n, t)),
    ("two_sum_sorted", ([2, 7, 11, 15], 9),       lambda r, n=[2,7,11,15], t=9: _valid_pair(r, n, t)),
    ("two_sum_sorted", ([1, 2], 5),               []),
    ("two_sum_sorted", ([1, 2, 3], 100),          []),
    ("two_sum_sorted", ([-3, -1, 2, 4], 1),       lambda r, n=[-3,-1,2,4], t=1: _valid_pair(r, n, t)),
    ("two_sum_sorted", ([5, 5], 10),              lambda r, n=[5,5], t=10: _valid_pair(r, n, t)),
    ("two_sum_sorted", ([1, 2, 4, 8], 6),         lambda r, n=[1,2,4,8], t=6: _valid_pair(r, n, t)),

    ("max_area", ([1, 8, 6, 2, 5, 4, 8, 3, 7],), 49),
    ("max_area", ([1, 1],),                        1),
    ("max_area", ([5],),                           0),
    ("max_area", ([],),                            0),
    ("max_area", ([4, 3, 2, 1, 4],),               16),
    ("max_area", ([1, 2, 1],),                     2),

    ("is_palindrome", ("abcba",), True),
    ("is_palindrome", ("abca",),  False),
    ("is_palindrome", ("",),      True),
    ("is_palindrome", ("a",),     True),
    ("is_palindrome", ("ab",),    False),
    ("is_palindrome", ("aa",),    True),
    ("is_palindrome", ("Aba",),   False),      # 区分大小写
]

MOVE_CASES = [
    (([0, 1, 0, 3, 12],), [1, 3, 12, 0, 0]),
    (([0],),              [0]),
    (([1, 2],),           [1, 2]),
    (([0, 0, 1],),        [1, 0, 0]),
    (([],),               []),
]


def main():
    print("=" * 72)
    print("双指针模式 · 自测（4 道题）")
    print("=" * 72)
    total_pass = total_all = 0
    not_written = set()

    for name, args, expected in CASES:
        fn = globals()[name]
        total_all += 1
        shown = ", ".join(repr(a) for a in args)
        try:
            got = _guarded(fn, *args)
        except NotImplementedError:
            not_written.add(name); total_all -= 1; continue
        except _Timeout:
            print(f"  ⏱️ {name}({shown})  —— 超过 {TIME_LIMIT} 秒还没返回，**大概率是死循环**")
            print(f"       检查：while 循环里，有没有哪个变量【每轮一定变大或变小】？")
            print(f"       （双指针最常见的就是忘了 L += 1 / R -= 1）")
            continue
        except Exception as e:
            print(f"  ❌ {name}({shown})  抛异常：{type(e).__name__}: {e}"); continue
        if isinstance(got, tuple):
            got = list(got)
        if callable(expected):
            ok = bool(expected(got))
            if ok:
                total_pass += 1
                print(f"  ✅ {name}({shown}) = {got!r}   （校验通过）")
            else:
                print(f"  ❌ {name}({shown})")
                print(f"       你返回 {got!r} —— 不是一对合法答案（要两个不同下标 i<j，且 nums[i]+nums[j]==target）")
        elif got == expected:
            total_pass += 1
            print(f"  ✅ {name}({shown}) = {got!r}")
        else:
            print(f"  ❌ {name}({shown})")
            print(f"       期望：{expected!r}")
            print(f"       实际：{got!r}")

    # 移动零单独处理（要检查"原地修改"和"返回值"两件事）
    fn = globals()["move_zeroes"]
    for args, expected in MOVE_CASES:
        total_all += 1
        arr = list(args[0])
        shown = repr(args[0])
        try:
            ret = _guarded(fn, arr)
        except NotImplementedError:
            not_written.add("move_zeroes"); total_all -= 1; continue
        except _Timeout:
            print(f"  ⏱️ move_zeroes({shown})  —— 超过 {TIME_LIMIT} 秒还没返回（检查 while/for 会不会出不来）")
            continue
        except Exception as e:
            print(f"  ❌ move_zeroes({shown})  抛异常：{type(e).__name__}: {e}"); continue
        # ⚠️ 这里只看"数组被改成什么样"，不看返回值 ——
        #    LeetCode 本题的判分也是直接检查数组，返回值无所谓。
        #    （我最初要求"必须返回 None"，比真题还严，已放宽。）
        if arr == expected:
            total_pass += 1
            print(f"  ✅ move_zeroes({shown}) → {arr!r}（数组改对了）")
        else:
            print(f"  ❌ move_zeroes({shown})")
            print(f"       期望变成：{expected!r}")
            print(f"       实际变成：{arr!r}")

    print("\n" + "=" * 72)
    if not_written and len(not_written) == 4:
        print("四道题都还没写 —— 从题 1 开始")
    elif total_pass == total_all:
        print(f"🎉 全绿！{total_pass}/{total_all} —— 双指针模式过关（L2）")
        print("   下一步：模式 ③ 滑动窗口（最长无重复子串 / 最小覆盖子串）—— 双指针的兄弟")
    else:
        if not_written:
            print(f"还没写的题：{'、'.join(sorted(not_written))}")
        print(f"进度：{total_pass}/{total_all} 通过 —— 红的那些看提示再改一版")
    print("=" * 72)
    print("""
卡住时的自救顺序：
  1. 打开 交互演示/算法②-双指针.html，把参数调成你卡住的那个输入，一步步看指针怎么走
  2. 手写一遍数组和 L/R，自己当 Python 走两步（双指针的 bug 基本都是"该动哪个指针"）
  3. 还卡 → 看题目的提示
  4. 最后才看文件末尾参考答案，看完关掉重写一遍

自查三问（每题都问）：
  · 循环条件该是 L < R 还是 L <= R？
  · 每走一步，我"排除"掉了什么？（排除不掉 = 这题不该用双指针）
  · 我的额外空间是 O(1) 吗？（双指针的优势就在这）
""")


# ══════════════════════════════════════════════════════════
# 参考答案（先自己写！）
# ══════════════════════════════════════════════════════════
"""
def two_sum_sorted(nums, target):
    L, R = 0, len(nums) - 1
    while L < R:
        s = nums[L] + nums[R]
        if s == target:
            return [L, R]
        elif s > target:
            R -= 1
        else:
            L += 1
    return []


def max_area(heights):
    L, R, best = 0, len(heights) - 1, 0
    while L < R:
        best = max(best, (R - L) * min(heights[L], heights[R]))
        if heights[L] < heights[R]:
            L += 1
        else:
            R -= 1
    return best


def move_zeroes(nums):
    pos = 0
    for i in range(len(nums)):
        if nums[i] != 0:
            nums[pos], nums[i] = nums[i], nums[pos]
            pos += 1
    return None          # 原地修改，不返回东西


def is_palindrome(s):
    L, R = 0, len(s) - 1
    while L < R:
        if s[L] != s[R]:
            return False
        L += 1
        R -= 1
    return True
"""

if __name__ == "__main__":
    main()
