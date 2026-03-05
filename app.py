from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os
import time

app = FastAPI()

# Database connection configuration from environment variables 
DB_HOST = os.getenv('DB_HOST', 'database-container')
DB_NAME = os.getenv('DB_NAME', 'user_db')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASS', 'password123')

def get_db_connection():
    # Retry logic for the database to finish booting 
    for _ in range(5):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except Exception:
            time.sleep(5)
    return None

# Initialize Database Table 
@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY, name varchar(100));')
        conn.commit()
        cur.close()
        conn.close()

class User(BaseModel):
    name: str

@app.get("/health")
def health():
    return {"status": "healthy"} 

@app.get("/users")
def get_users():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cur = conn.cursor()
    cur.execute('SELECT name FROM users;')
    users = cur.fetchall()
    cur.close()
    conn.close()
    return [user[0] for user in users] 

@app.post("/users")
def add_user(user: User):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cur = conn.cursor()
    cur.execute('INSERT INTO users (name) VALUES (%s)', (user.name,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "User added"} 