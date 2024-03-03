from aiogram import types, Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import TOKEN_API
import sqlite3 as sq
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

async def db_start():
    global con, cur
    con = sq.connect(database = BASE_DIR + "\\test.db")
    print("database ishga tushdi")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS profile (id TEXT, name TEXT, photo TEXT, age TEXT, decription TEXT)")
    con.commit()

async def create_profile(user_id):
    user = cur.execute("SELECT 1 FROM profile WHERE id='{}'".format(user_id)).fetchone()
    print(user, "user")
    if not user:
        cur.execute("INSERT INTO profile VALUES(?,?,?,?,?)",
            (user_id, "", "", "","")
            )
        con.commit()
    cur.execute("INSERT INTO profile VALUES(?,?,?,?,?)",
            (user_id, "", "", "","")
            )
    con.commit()

storage = MemoryStorage()

bot = Bot(token=TOKEN_API)
dp = Dispatcher(bot=bot, storage=storage)

async def on_startup(_):
    await db_start() 
   

class UserStatesGroup(StatesGroup):
    name = State()
    photo = State()
    age = State()
    description = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    await message.reply("Botni ishga tushirish uchun ro'yxatdan o'ting, /create ustiga bosing",
                        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                            [KeyboardButton(text="/create")]
                        ]))

@dp.message_handler(commands=['create'])
async def cmd_create(message: types.Message) ->None:
    await message.reply(text="Ismingizni yuboring yuboring")
    await create_profile(user_id=message.from_user.id)
    await UserStatesGroup.name.set()

@dp.message_handler(state=UserStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply("Profil uchun rasm yuboring")
    await UserStatesGroup.next()

@dp.message_handler(lambda message: not message.photo, state=UserStatesGroup.photo)
async def check_photo(message: types.Message) -> None:
    await message.answer("Bu rasm emas")

@dp.message_handler(content_types=['photo'], state=UserStatesGroup.photo)
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await message.reply("Hozirgi yoshingizni yuboring")
    await UserStatesGroup.next()


@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text)<8 , state=UserStatesGroup.age)
async def check_age(message: types.Message) -> None:
    await message.answer("Bu yosh emas")

@dp.message_handler(state=UserStatesGroup.age)
async def load_age(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['age'] = message.text
    await message.reply("Profil uchun izoh yuboring")
    await UserStatesGroup.next()

@dp.message_handler(state=UserStatesGroup.description)
async def load_description(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['description'] = message.text
        print(data)
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup
                           )