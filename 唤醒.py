from fastapi import FastAPI
import sqlite3

app = FastAPI(title="prescription AND ingredients",version="1.0",description="prescription AND ingredients table")

def get_db():
    conn = sqlite3.connect("prescriptions.db")
    conn.row_factory=sqlite3.Row
    return conn

@app.get("/prescriptions/herbs")
def reback_all_list():
    conn=get_db()
    rows = conn.execute("select * from ingredients").fetchall()
    conn.close()
    return [dict(r) for r in rows]
