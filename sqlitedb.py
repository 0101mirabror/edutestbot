import sqlite3
import os, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_dir = (BASE_DIR + '\\new.db')

con = sqlite3.connect(database=db_dir)
cur = con.cursor()
async def func_one_hour_later(current_time):
    current_datetime = datetime.datetime.combine(datetime.date.today(), current_time)
    delta = datetime.timedelta(seconds=10)
    new_datetime = current_datetime + delta
    return new_datetime.time()

async def check_user_registered(user_id):
    user = cur.execute("SELECT 1 FROM users WHERE id='{}'".format(user_id)).fetchone()
    print("user:", user)
    # if user:
    #     return True
    # return False

async def db_start():
    global cur, db
    db = sqlite3.connect('new.db')
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id TEXT, photo TEXT, description TEXT, age TEXT, name TEXT)")
    print("Database muvaffaqiyatli ulandi")
    db.commit()

async def create_profile(user_id):
    user  = cur.execute("SELECT 1 FROM users WHERE id = {}".format(user_id)).fetchone()
    print(cur.execute("SELECT 1 FROM users WHERE id = {}".format(user_id)))
    if not user:
        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, "", "", "", ""))
        print("user_yaratildi_create_profile")
        db.commit()


async def edit_profile(state, user_id):
    async with state.proxy() as data:
        cur.execute("""UPDATE users SET photo="{}", name="{}" , age="{}", description="{}"  WHERE id = {}""".format(
        data['photo'], data['name'], data['age'], data['description'],   user_id))
        db.commit()


