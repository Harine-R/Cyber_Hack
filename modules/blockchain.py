import sqlite3

def log_hash(file_hash):
    conn = sqlite3.connect("data/mock_db.sqlite")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS blockchain (hash TEXT)")
    cursor.execute("INSERT INTO blockchain (hash) VALUES (?)", (file_hash,))
    conn.commit()
    conn.close()
