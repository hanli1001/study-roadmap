"""样例代码库 · len() —— 「数一数里面有多少个」

一句话：len(x) 返回 x 的长度（元素个数）。
用法：python 样例代码库/len用法.py
配套交互卡片：还没做（下一个陌生函数就是你最常忘的那个 —— 告诉我，我给你做一张）
"""

print("=" * 58)
print("① 最小可运行：它到底数什么")
print("=" * 58)
print('len("abc")        =', len("abc"))          # 字符串 → 字符个数
print('len("你好")        =', len("你好"))          # 中文：一个字算 1
print('len([1,2,3])      =', len([1, 2, 3]))      # 列表 → 元素个数
print('len({"a":1,"b":2}) =', len({"a": 1, "b": 2}))  # 字典 → 键的个数
print('len((1,2))        =', len((1, 2)))        # 元组
print("len(range(5))     =", len(range(5)))      # range 也能数（它有明确长度）
print()
print("⚠️ 规律：**能数的东西才有 len**。单个数字、True/False 没有长度。")

print("\n" + "=" * 58)
print("② 改参数看变化 —— 输入不同，输出怎么变")
print("=" * 58)
for s in ["", "a", "ab", "abc", "abcd"]:
    print(f'  len("{s}")'.ljust(16), "=", len(s))
print("  ↑ 空字符串长度是 0（不是报错）—— 这就是判断'用户没填'的常用写法：")
print('     if len(name) == 0:  →  等价于 if not name:')

print("\n" + "=" * 58)
print("③ 边界情况（最容易踩的 4 个）")
print("=" * 58)
print("① len(123)        → TypeError: object of type 'int' has no len()")
print("   数字没有「长度」这个概念，要数先转字符串：len(str(123)) =", len(str(123)))
print("② len(None)       → TypeError（None 也没有长度）")
print("③ len(生成器)     → TypeError（它不知道后面还有多少个，是一次性的）")
print('④ len("a b")      =', len("a b"), "→ 空格也算一个字符（别以为它不算）")

print("\n" + "=" * 58)
print("④ 轮到你了（写不出来就先猜，再跑）")
print("=" * 58)
todo = "张三"
print(f'  a) len("{todo}") = ?        # 先猜：____  再取消下一行的注释看答案')
# print("     答案：", len(todo))

print("  b) 一个列表里有 5 个名字，怎么判断它是空的？写一行 if：")
print("     if ____:  print('没有人')")

print("  c) 下面哪个会报错？先猜再试：len(3.14) / len([[]]) / len({'x': 1})")
# 提示：[[]] 是一个"里面装着一个空列表"的列表，它自己有 1 个元素
