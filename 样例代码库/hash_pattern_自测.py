"""哈希表模式 · 四道变式的自测文件（你写完函数，跑这个自动判对错）

用法：
    1. 在下面 4 个函数体里写你的实现（把 raise NotImplementedError 删掉）
    2. 运行：python 样例代码库/hash_pattern_自测.py
    3. 看输出：绿的 ✅ 是过了，红的 ❌ 会告诉你"用哪个输入、期望什么、你给的是什么"
    4. 全绿就算这个模式过关（L2：不看示例独立写出来并跑通）

为什么给你自测文件而不是我来批改：
    能自己验证对错，比"等人批改"快得多 —— 这是你做完 pytest 收尾后该拿到的能力。
    （4 道题的参考答案在文件最后，**先自己写再看**）

⚠️ 只用你学过的东西：字典、集合、enumerate、for、if。不用任何第三方库。
"""


# ══════════════════════════════════════════════════════════
# 题 1：判断数组里有没有重复元素
# ══════════════════════════════════════════════════════════
def has_duplicate(nums):
    """有重复元素返回 True，否则 False。

    例：has_duplicate([1,2,3,1]) → True
        has_duplicate([1,2,3])   → False
        has_duplicate([])        → False

    提示：你只需要知道"这个东西见过没有" —— 用 set 最省，用 dict 也行。
    """
    if len(nums) != len(set(nums)):
        return True
    return False


# ══════════════════════════════════════════════════════════
# 题 2：统计每个元素出现几次
# ══════════════════════════════════════════════════════════
def count_items(nums):
    """返回一个字典：元素 → 出现次数。

    例：count_items(["a","b","a"]) → {"a": 2, "b": 1}
        count_items([])           → {}

    提示：d[x] = d.get(x, 0) + 1   ← 这一行是"计数"的标准写法，记牢
    """
    b = {}
    for i in nums:
        b[i] = b.get(i, 0) + 1
    return b




# ══════════════════════════════════════════════════════════
# 题 3：两数之差等于 k（找出这样的一对下标）
# ══════════════════════════════════════════════════════════
def two_diff(nums, k):
    """找出两个不同位置 i、j，使 nums[i] - nums[j] == k（**前减后**，k ≥ 0）；没有返回 [].

    ⚠️ **规格已锁死，不再改**（上一版我在这里来回换过方向，是我的错）：
       要求 前 - 后 = k。也就是说：**较大/靠后的那个在前面时**，才用 x+k；
       两种情形都要覆盖，所以最稳的写法是**两个方向都查一遍**：

           for i, x in enumerate(nums):
               for need in (x - k, x + k):      # x 可能是"大的那个"，也可能是"小的那个"
                   if need in seen:
                       return [seen[need], i]
               seen[x] = i

       为什么两个都要？举例 nums = [1, 5, 2]，k = 3：
           · 走到 x=5 时：5 - 2 还没出现，但 5 可能是"大的那个" → 查 x-k=2（还没见过）
           · 走到 x=2 时：2 是"小的那个"，而大的 5 已经在字典里 → 查 x+k=5 → 命中 [1, 2] ✅
       只查一个方向，上面两种情形里就会漏掉一种。

    例：two_diff([5, 1, 3], 2) → [0, 2]   （5 - 3 = 2）
        two_diff([1, 5, 2], 3) → [1, 2]   （5 - 2 = 3）
        two_diff([1, 2], 5)    → []
        two_diff([3, 3], 0)    → [0, 1]   （k=0 时两数相等）

    提示：这就是"两数之和"换了张皮 —— 和是 target - x，差是 x ± k。
    """

    seen = {}
    for i, x in enumerate(nums):

        for need in (x - k, x + k):
            if need in seen:
                return [seen[need], i]
        seen[x] = i
    return []


# ══════════════════════════════════════════════════════════
# 题 4：第一个只出现一次的字符
# ══════════════════════════════════════════════════════════
def first_unique(s):
    """返回第一个"只出现一次"的字符；没有这样的字符就返回 None。

    例：first_unique("aabbc") → "c"
        first_unique("aabb")  → None
        first_unique("abc")   → "a"

    提示：这次要**两遍**：
          第一遍数每个字符出现几次（就是题 2）
          第二遍按原顺序找第一个次数为 1 的 —— 为什么不能一遍搞定？想想看。
    """
    seed = {}
    for i in s:
        seed[i] = seed.get(i, 0) + 1
    for i in s:
       if seed[i] == 1:
           return i
    return None


# ══════════════════════════════════════════════════════════
# 下面是自动判分，不用改
# ══════════════════════════════════════════════════════════
CASES = {
    "has_duplicate": [
        (([1, 2, 3, 1],), True),
        (([1, 2, 3],), False),
        (([],), False),
        (([7],), False),
        ((["a", "b", "a"],), True),
    ],
    "count_items": [
        ((["a", "b", "a"],), {"a": 2, "b": 1}),
        (([],), {}),
        (([1, 1, 1, 2],), {1: 3, 2: 1}),
        (([0, 0],), {0: 2}),
    ],
    # ⚠️ two_diff 可能有多个合法答案（[5,1,3] 里 5-3 和 3-1 都等于 2），
    #    所以不判"等于某个数组"，而是判"你返回的这一对，本身成不成立"。
    #    格式：((nums, k), 校验函数)  —— 校验函数返回 True 才算过
    "two_diff": [
        (([5, 1, 3], 2), lambda r, n=[5, 1, 3], k=2: _valid_pair(r, n, k)),
        (([1, 2], 5),    lambda r, n=[1, 2], k=5: r == []),          # 无解必须返回 []
        (([3, 3], 0),    lambda r, n=[3, 3], k=0: _valid_pair(r, n, k)),
        (([10, 4, 7], 3), lambda r, n=[10, 4, 7], k=3: _valid_pair(r, n, k)),
        (([1, 5, 2], 3), lambda r, n=[1, 5, 2], k=3: _valid_pair(r, n, k)),
        (([1, 1], 0),    lambda r, n=[1, 1], k=0: _valid_pair(r, n, k)),
        (([9, 1, 4], 5), lambda r, n=[9, 1, 4], k=5: _valid_pair(r, n, k)),
    ],
    "first_unique": [
        (("aabbc",), "c"),
        (("aabb",), None),
        (("abc",), "a"),
        (("",), None),
        (("aad",), "d"),
        (("bbac",), "a"),              # ← 修正：这里 a 只出现一次，所以第一个唯一字符就是 a
        (("aab",), "b"),               # ← 这才是"'b' 是唯一且唯一字符只有一个"的情形
    ],
}


def _valid_pair(r, nums, k):
    """校验 two_diff 的返回值：只要"两个不同位置 + 差正好等于 k"就算对（不限定是哪一对）。"""
    if not isinstance(r, (list, tuple)) or len(r) != 2:
        return False
    i, j = r
    if i == j:
        return False                                  # 必须是两个不同位置
    if not (0 <= i < len(nums) and 0 <= j < len(nums)):
        return False                                  # 下标必须在范围内
    return abs(nums[i] - nums[j]) == abs(k)           # 差对得上就算对（两个方向都算）



def _norm(v):
    """把结果规范一下，让 [0,2] 和 (0,2) 都算对；列表顺序不同则算错。"""
    if isinstance(v, (list, tuple)):
        return list(v)
    return v


def main():
    print("=" * 70)
    print("哈希表模式 · 自测（4 道题）")
    print("=" * 70)
    total_pass = total_all = 0

    for name, cases in CASES.items():
        fn = globals()[name]
        print(f"\n【{name}】")
        for args, expected in cases:
            total_all += 1
            shown = ", ".join(repr(a) for a in args)
            try:
                got = _norm(fn(*args))
            except NotImplementedError:
                print(f"  ⏭️  {name}({shown})  —— 还没写")
                total_all -= 1
                continue
            except Exception as e:
                print(f"  ❌ {name}({shown})  抛异常：{type(e).__name__}: {e}")
                continue
            if callable(expected):                     # 多解题目：用校验函数判"这一对成不成立"
                ok = bool(expected(got))
                if ok:
                    total_pass += 1
                    print(f"  ✅ {name}({shown}) = {got!r}   （校验通过：是一对合法答案）")
                else:
                    print(f"  ❌ {name}({shown})")
                    print(f"       你返回：{got!r} —— 这不是一对合法答案")
                    print(f"       （要两个不同位置的下标，且两数之差等于 k）")
            elif got == expected:
                total_pass += 1
                print(f"  ✅ {name}({shown}) = {got!r}")
            else:
                print(f"  ❌ {name}({shown})")
                print(f"       期望：{expected!r}")
                print(f"       实际：{got!r}")

    print("\n" + "=" * 70)
    if total_all == 0:
        print("四道题都还没写 —— 从题 1 开始（先把 raise NotImplementedError 删掉）")
    elif total_pass == total_all:
        print(f"🎉 全绿！{total_pass}/{total_all} —— 哈希表模式过关（L2）")
        print("   下一步：模式 ② 双指针（有序数组 / 移动零 / 两数之和-有序版）")
    else:
        print(f"进度：{total_pass}/{total_all} 通过 —— 红的那些看提示再改一版")
    print("=" * 70)
    print("""
卡住时按这个顺序自救（不要立刻看答案）：
  1. 先把输入手写在一张纸上，自己按代码走一遍（当自己是 Python）
  2. 问自己："我现在缺的是'某个数出现过没有'，还是'它出现过几次'？"
  3. 还卡 → 看题目下面的提示（每道题都给了）
  4. 最后才看文件末尾的参考答案，而且看完要**关掉重写一遍**
""")


# ══════════════════════════════════════════════════════════
# 参考答案（先自己写！写完再对）
# ══════════════════════════════════════════════════════════
"""
def has_duplicate(nums):
    seen = set()
    for x in nums:
        if x in seen:
            return True
        seen.add(x)
    return False


def count_items(nums):
    d = {}
    for x in nums:
        d[x] = d.get(x, 0) + 1
    return d


def two_diff(nums, k):
    # 一边走一边记"见过的值 → 位置"
    seen = {}
    for i, x in enumerate(nums):
        # 两种可能：x 是较大的那个（need = x - k），或 x 是较小的那个（need = x + k）
        for need in (x - k, x + k):
            if need in seen:
                return [seen[need], i]
        seen[x] = i
    return []


def first_unique(s):
    count = {}
    for ch in s:
        count[ch] = count.get(ch, 0) + 1
    for ch in s:                    # 第二遍按"原顺序"找 —— 这是关键
        if count[ch] == 1:
            return ch
    return None
"""

if __name__ == "__main__":
    main()
