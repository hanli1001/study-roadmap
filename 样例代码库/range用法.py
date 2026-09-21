"""样例代码库 · range() —— 「生成一串数字」

一句话：range(...) 造出一串数字，常用来「重复 N 次」或「走一遍下标」。
用法：python 样例代码库/range用法.py
关键在于它的三种形态 —— 记住"起点、终点、步长"，且**终点取不到**。
"""

print("=" * 58)
print("① 最小可运行：三种形态")
print("=" * 58)
print("range(5)        →", list(range(5)), "  # 只给终点：从 0 开始")
print("range(2, 6)     →", list(range(2, 6)), "  # 起点, 终点")
print("range(0, 10, 3) →", list(range(0, 10, 3)), "  # 起点, 终点, 步长")
print()
print("⚠️ 铁律：**终点取不到**（左闭右开）。range(5) 里没有 5。")

print("\n" + "=" * 58)
print("② 改参数看变化")
print("=" * 58)
print("步长为负 = 倒着数：")
print("  range(5, 0, -1) →", list(range(5, 0, -1)))
print("  range(3, -1, -1) →", list(range(3, -1, -1)))
print()
print("一个参数的常见用途（重复 3 次）：")
for i in range(3):
    print(f"  第 {i + 1} 次循环（i = {i}）—— 注意 i 从 0 开始")
print()
print("for i in range(1, 4) 就是「从 1 数到 3」（人话版）：")
for i in range(1, 4):
    print(f"  i = {i}")

print("\n" + "=" * 58)
print("③ 边界情况")
print("=" * 58)
print("range(0)        →", list(range(0)), "  空！循环体一次都不执行")
print("range(5, 5)     →", list(range(5, 5)), "  空！（起点==终点）")
print("range(5, 1)     →", list(range(5, 1)), "  空！（正步长但起点>终点，不会自动倒过来）")
print("range(0, 10, 3) →", list(range(0, 10, 3)), "  最后一步是 9，跳过 10（终点取不到）")
print()
print("⚠️ 和 len 一起用的经典写法：")
data = ["甲", "乙", "丙", "丁"]
for i in range(len(data)):
    print(f"  下标 {i} → {data[i]}")

print("\n" + "=" * 58)
print("④ 轮到你了")
print("=" * 58)
print("  a) 打印 1~10 的所有偶数（用 range 的步长）")
print("  b) 打印 10~1 的倒计时")
print("  c) 猜：list(range(2, 10, 2)) 结果是？先写下来再跑")
print("     （参考答案写在文件最后一行注释里，别提前看）")

# 参考答案：c) [2, 4, 6, 8]
