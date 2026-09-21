"""样例代码库 · enumerate() —— 「一边数序号一边取东西」

一句话：enumerate(可迭代) 每次给你"序号 + 元素"，省掉手动维护计数器的麻烦。
用法：python 样例代码库/enumerate用法.py
痛点对照：以前写 for i in range(len(x)): x[i] —— enumerate 把这个写法废掉了。
"""

print("=" * 58)
print("① 先看「没有它」有多烦（旧写法）")
print("=" * 58)
names = ["小明", "小红", "小刚"]
for i in range(len(names)):
    print(f"  {i + 1}. {names[i]}   ← 靠下标去取，容易错")

print("\n用 enumerate 之后：")
for i, name in enumerate(names):
    print(f"  {i + 1}. {name}   ← 序号和名字一起给")

print("\n" + "=" * 58)
print("② 改参数看变化")
print("=" * 58)
print("默认从 0 数（编程惯例）：")
for i, name in enumerate(names):
    print(f"  i={i}  name={name}")
print()
print("想从 1 数（人话版）—— 加 start：")
for i, name in enumerate(names, start=1):
    print(f"  第 {i} 名：{name}")
print()
print("也能数别的：")
for i, ch in enumerate("abc"):
    print(f"  enumerate(\"abc\") 的第 {i} 项 = {ch}")

print("\n" + "=" * 58)
print("③ 边界情况")
print("=" * 58)
print("空列表 → 循环体一次都不执行：")
for i, x in enumerate([]):
    print("  这行永远不会打印")
print("  （已跳过，说明确实没执行）")
print()
print("序号从 0 开始是「坑」的高发区：")
print("  要给人看的名次 → 必须 start=1 或自己 +1")
print("  要给列表取值 → 下标必须从 0，别 +1")

print("\n" + "=" * 58)
print("④ 轮到你了")
print("=" * 58)
scores = [88, 92, 75]
print("  a) 打印成「第1名：88」这种格式（用 enumerate + start）")
print("  b) 找出最高分是第几名（提示：max(scores) 拿到最高分，再配合 enumerate 找它在哪）")
print("  c) 猜：下面的输出是什么？")
print("       for i, x in enumerate([10, 20], start=5): print(i, x)")
print("     （参考答案在文件最后一行，别提前看）")

# 参考答案：c) 5 10 / 6 20
