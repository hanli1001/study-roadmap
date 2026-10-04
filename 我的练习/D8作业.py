import sqlite3
from pathlib import Path
import random as rnd

conn = sqlite3.connect(Path(__file__).with_name("D8.db"))

cur = conn.cursor()
cur.execute("PRAGMA foreign_keys = ON")

cur.execute("DROP TABLE IF EXISTS student_course")
cur.execute("DROP TABLE IF EXISTS students")
cur.execute("DROP TABLE IF EXISTS course")



cur.execute('''
CREATE TABLE students(
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
name TEXT NOT NULL,
class_name TEXT NOT NULL)''')


cur.execute('''
CREATE TABLE course(
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
name TEXT NOT NULL)''')

cur.execute('''
CREATE TABLE student_course(
course_id INTEGER  NOT NULL REFERENCES course(id),
student_id INTEGER  NOT NULL REFERENCES students(id),
primary key (course_id, student_id))''')

student = [('张三','高一'), ('李四','高三'), ('牛二','高三'),('李三','高一'),('张贾瑞','高二')]
course = [('语文' ,), ('数学',),('英语',),('物理',),('化学',),('生物',)]

cur.executemany('INSERT INTO students(name,class_name) VALUES (?,?)',student)
cur.executemany('INSERT INTO course(name) VALUES (?)', course)

def link(student_name, course_name):
    cur.execute('''
    SELECT id FROM students WHERE name = ?''', (student_name,))
    sid = cur.fetchone()[0]
    for i in course_name:
        cur.execute('''
        SELECT id FROM course WHERE name = ?''',(i,))
        course_id = cur.fetchone()[0]
        cur.execute('''
        INSERT INTO student_course(course_id, student_id) VALUES (?,?)'''
                    ,(course_id,sid))
    conn.commit()

link("张三",["语文","数学","英语"])
link("李四",["语文","数学","物理"])
link("牛二",["数学","物理","化学"])
link("李三",["数学","生物","化学"])
link("张贾瑞",["语文","数学","化学"])




query_s = '''SELECT * FROM students'''
cur.execute(query_s)
print(cur.fetchall())

print("="*30)
query_c = '''SELECT * FROM course'''
print(cur.execute(query_c).fetchall())

print("="*30)
query_s_c = '''SELECT * FROM student_course'''
print(cur.execute(query_s_c).fetchall())

# query = '''
# SELECT c.name ,s.name ,s.class_name
# FROM course c
#         JOIN student_course s_c ON c.id = s_c.course_id
#         JOIN students s ON s_c.student_id = s.id
#         WHERE c.name = "数学"'''

query = '''
SELECT c.name ,s.name ,s.class_name
FROM course c 
        JOIN student_course s_c ON c.id = s_c.course_id
        JOIN students s ON s_c.student_id = s.id'''

print(cur.execute(query).fetchall())
conn.close()
