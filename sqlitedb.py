import sqlite3
import os, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_dir = (BASE_DIR + '\\new.db')

con = sqlite3.connect(database=db_dir)
cur = con.cursor()
async def func_one_hour_later(current_time):
    current_datetime = datetime.datetime.combine(datetime.date.today(), current_time)
    delta = datetime.timedelta(hours=1)
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
        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (user_id, None, None, None, None, None))
        print("user_yaratildi_create_profile")
        db.commit()


# async def edit_profile(state, user_id):
#     async with state.proxy() as data:
#         cur.execute("""UPDATE users SET photo="{}", name="{}" , age="{}", phone="{}"  WHERE id = {}""".format(
#         data['photo'], data['name'], data['age'], data['phone'],   user_id))
#         db.commit()
async def edit_profile(state, user_id):
    async with state.proxy() as data:
        cur.execute("""INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",(
        user_id, data['photo'], data['phone'], data['age'], data['name'], " ", data['username'], data['user_id']))
        db.commit()


async def create_book_instance(state):
    async with state.proxy() as data:
        name = data['book_name']
        destination = data['book_id']
        grade = data['book_grade_id']
    print(f"SELECT 1 FROM books WHERE name='{name}'and grade_id={grade}")
    book = cur.execute(f"SELECT 1 FROM books WHERE name='{name}' and grade_id={grade}").fetchone()
    if not book:
        query = "INSERT INTO books VALUES (?, ?, ?, ?, ?)"
        cur.execute(query, (None, name, 1, destination, grade))
        print("book is saved")
        db.commit()

