import sqlite3
from config import DB_FILE

def create_table(db_name=DB_FILE):
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_tokens (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                tts_symbols INTEGER,
                stt_blocks INTEGER,
                gpt_tokens INTEGER)
            ''')
            conn.commit()
    except Exception:
        pass

def insert_data(user_id):
    con = sqlite3.connect('ЭТО_БАЗА.sqlite')
    cur = con.cursor()
    cur.execute(f'''INSERT INTO users_tokens(user_id, tts_symbols, stt_blocks, gpt_tokens) VALUES({user_id}, 0, 0, 0);''')
    con.commit()
    con.close()

def update_data(user_id, column, value):
    con = sqlite3.connect('ЭТО_БАЗА.sqlite')
    cur = con.cursor()
    sql_query = f"UPDATE users_tokens SET {column} = ? WHERE user_id = ?;"
    cur.execute(sql_query, (value, user_id))
    con.commit()
    con.close()

def collect_users_data(column):
    con = sqlite3.connect('ЭТО_БАЗА.sqlite')
    cur = con.cursor()
    sql_query = f"SELECT {column} FROM users_tokens ORDER BY id DESC;"
    res = [i[0] for i in cur.execute(sql_query)]
    con.commit()
    con.close()
    return res

def collect_user_data(user_id, column):
    con = sqlite3.connect('ЭТО_БАЗА.sqlite')
    cur = con.cursor()
    sql_query = f"SELECT {column} FROM users_tokens WHERE user_id = {user_id} ORDER BY id DESC;"
    res = [i[0] for i in cur.execute(sql_query)]
    con.commit()
    con.close()
    return res[0]

print(collect_users_data('gpt_tokens'))
