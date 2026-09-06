a = [1,2,3,4,5]
b = [i**2 for i in a if i%2==0]
print(b)

dosages = ["三两", "", "五两", "", "一两"]
c = [i for i in dosages if i!=""]
print(c)