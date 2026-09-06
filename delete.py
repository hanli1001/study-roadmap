import sqlite3
conn = sqlite3.connect('prescriptions.db')

cx_1=conn.execute('''select * from prescription_ingredients''').fetchall()
cx_2=conn.execute('''select * from prescriptions''').fetchall()
cx_3=conn.execute('''select * from ingredients''').fetchall()


print(cx_1,"\n")
print(cx_2,"\n")
print(cx_3,"\n")

conn.execute('''delete from prescriptions where name = "001"''')
conn.commit()