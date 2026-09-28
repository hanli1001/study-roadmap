import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path(__file__).with_name("D8.db"))

cur = conn.cursor()

cur.execute('''
CREATE TABLE students(
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
name TEXT NOT NULL)''')

cur.execute('''
CREATE TABLE course(
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
name TEXT NOT NULL)''')

cur.execute('''
CREATE TABLE student_course(
course_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
student_id INTEGER NOT NULL REFERENCES students(id),
class TEXT NOT NULL REFERENCES course(id),
primary key (course_id, student_id))''')

student = [('张三',), ('李四',), ('牛二',),('李三',),('张贾瑞',)]
course = [('语文' ,), ('数学',),('英语',),('物理',),('化学',),('生物',)]

cur.executemany('INSERT INTO students(name) VALUES (?,)', student)
cur.executemany('INSERT INTO course(name) VALUES (?)', course)




