from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import ADMINS, TOKEN_API
import sqlite3
import os, datetime, logging, sys, asyncio
from sqlitedb import db_start, create_profile, edit_profile, check_user_registered,  func_one_hour_later, create_book_instance
from apscheduler.schedulers.asyncio import AsyncIOScheduler


bot = Bot(token=TOKEN_API, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
scheduler = AsyncIOScheduler()


async def on_startup(_):
    await db_start()
    # schedule_jobs()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_dir = (BASE_DIR + '\\new.db')
conn = sqlite3.connect(database=db_dir)
cur = conn.cursor()

# user-profile creation
class ProfileStatesGroup(StatesGroup): #1)name, 2)photo, 3)age, 4)description
    name = State()
    photo = State()
    age = State()
    phone = State()

class BookStatesGroup(StatesGroup):
    book = State()
    destination = State()
    grade = State()
    
class VideoStatesGroup(StatesGroup):
    category = State()
    topic = State()
    video = State()

# cancel button
def get_cancel_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(text="/cancel")]
    ])
def get_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(text="/create")]
    ])


@dp.message_handler(commands=['cancel'], state="*")
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    if state is None:
        return
    await state.finish()
    await message.reply("Siz obyekt yaratish jarayonini bekor qildingiz", 
                        reply_markup=get_keyboard())
# start handler, works when '/start' is typed  //lambda message: message.text == "Asosiy menu",
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    user = cur.execute("SELECT * FROM users WHERE id = '{user_id}' and photo IS NOT NULL and name IS NOT NULL and phone IS NOT NULL".format(user_id=message.from_user.id)).fetchone()
    print(user)
    if user:
        await message.reply("""<b>Menyudan istalgan bo'limni tanlashingiz mumkin!</b>""",
                        parse_mode="HTML",
                        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True,keyboard=[
                            [types.KeyboardButton(text="Maxsus testlar 💸"), types.KeyboardButton(text="Olimpiada testlari 🧑‍💻"), types.KeyboardButton(text="Video darsliklar 🎞")],
                            [types.KeyboardButton(text="Math books pdf 📘"), types.KeyboardButton(text="Online kurslarga qatnashish 💠"), types.KeyboardButton(text="Kod bo'yicha tekshirish ✅")],
                            [types.KeyboardButton(text="Mening profilim  👤")]
                        ]))
    else:
        await message.reply("Assalomu alaykum foydalanuvchi, botdan foydalanish uchun ro'yxatdan o'tishingiz kerak!, /create tugmasi ustiga bosing!",
                        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                            [types.KeyboardButton(text='/create')]
                        ])) 
        # await create_profile(user_id=message.from_user.id)




"""USER PROFILE CREATE"""
# create handler, begins user creation process
@dp.message_handler(commands=['create'])
async def cmd_create(message: types.Message) -> None:
    await message.reply("Ro'yxatdan o'tish uchun, ism-familiyangizni yuboring",
                    reply_markup=get_cancel_keyboard())
    await ProfileStatesGroup.name.set()

@dp.message_handler(lambda message: message.text in ["/start", "/create"], state=ProfileStatesGroup.name)
async def check_name(message: types.Message)->None:
    await message.reply("Ism-familiyangizni to'g'ri yuboring!")
# user name handler
@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply("Profil uchun rasmingizni yuboring!")
    await ProfileStatesGroup.next()

# no image handler
@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.photo)
async def check_photo(message: types.Message):
    await message.reply("Bu rasm emas 🤨!")

# image handler
@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.photo)
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await message.reply("Endi yoshingizni yuboring!")
    await ProfileStatesGroup.next()

# check-user-age handler
@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) < 8 or float(message.text) > 100, state=ProfileStatesGroup.age)
async def check_age(message: types.Message):
    await message.reply("Bu yoshingiz emas 🤨. Haqiqiy yoshingizni kiriting")

# user age handler
@dp.message_handler(state= ProfileStatesGroup.age)
async def load_age(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['age'] = message.text
    await message.reply("Telefon raqamingizni kiriting", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton("Jo'natish", request_contact=True)]
    ]))
    await ProfileStatesGroup.next()

# save all data to database
@dp.message_handler(content_types=['contact'], state=ProfileStatesGroup.phone)
async def load_description(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['phone'] = message.contact.phone_number
        data['username'] = message.contact.first_name
        data['user_id'] = message.contact.user_id
    print(message.contact)
    await  message.reply("Profilingiz muvaffaqiyatli yaratildi. Menyulardan birini tanlashingiz mumkin",
                            parse_mode="HTML",
                    reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True,keyboard=[
                        [types.KeyboardButton(text="Maxsus testlar"), types.KeyboardButton(text="Olimpiada testlari"), types.KeyboardButton(text="Video darsliklar")],
                        [types.KeyboardButton(text="Math books pdf"), types.KeyboardButton(text="Online kurslarga qatnashish"), types.KeyboardButton(text="Kod bo'yicha tekshirish")],
                        [types.KeyboardButton(text="Mening profilim")]
                    ]))
    await edit_profile(state, user_id=message.from_user.id)
    await state.finish()

"""USER PROFILE CREATION END"""
   
"""MAXSUS TESTLAR: BEGIN"""
# special tests(pro_1)
@dp.message_handler(lambda message: message.text == "Maxsus testlar 💸")
async def check_authenticated_user(message: types.Message, state: FSMContext) -> None:
    member = await bot.get_chat_member("-1002098994434  ", message.from_user.id)
    print(message.chat.id)
    await message.answer(text="Testni boshlash uchun kerakli mavzuni tanlang!!!", reply_markup=types.ReplyKeyboardRemove())
    if not member.is_chat_member():
        await message.reply("Siz guruhga a'zo emassiz!",
                            reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                                [types.InlineKeyboardButton(text="Guruhga qo'shilish", url="https://t.me/+2hmwl23svbVlZDQy")]
                            ]))  
    else:
        db = cur.execute("SELECT * FROM topics ORDER BY topic ASC")
        db1 = [x for x in db]
        if len(db1) >= 10:
            c = db1[:10]
            async with state.proxy() as data:
                data['page'] = 0 
                data['topics'] =  db1
            await message.answer(text=f"""
                                        1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()} \n4. {c[3][1].capitalize()} \n5. {c[4][1].capitalize()}\n6. {c[5][1].capitalize()} \n7. {c[6][1].capitalize()} \n8. {c[7][1].capitalize()} \n9. {c[8][1].capitalize()} \n10. {c[9][1].capitalize()}
                                        \nMavzuni tanlang.""",
                            reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                              types.InlineKeyboardButton(text="4", callback_data=f"check_{c[3][0]}"),
                              types.InlineKeyboardButton(text="5", callback_data=f"check_{c[4][0]}"),
                              ],
                             [
                              types.InlineKeyboardButton(text="6", callback_data=f"check_{c[5][0]}"),
                              types.InlineKeyboardButton(text="7", callback_data=f"check_{c[6][0]}"),
                              types.InlineKeyboardButton(text="8", callback_data=f"check_{c[7][0]}"),
                              types.InlineKeyboardButton(text="9", callback_data=f"check_{c[8][0]}"),
                              types.InlineKeyboardButton(text="10", callback_data=f"check_{c[9][0]}"),
                              ],
                            [
                             types.InlineKeyboardButton(text="➡️", callback_data="page_1"),
                              ]
                         ]), 
                         parse_mode="HTML")
        else:
            await message.answer("Maxsus testlar uchun bo'limlar mavjud emas.")

# "maxsus testlar"'s topics
@dp.callback_query_handler(lambda x: x.data.startswith('page_'))
async def paginate_data(callback: types.CallbackQuery, state: FSMContext) -> None:
    upcoming_page = int(callback.data[callback.data.find('_')+1:])
    async with state.proxy() as data:
        previous_page = data['page']
        db1 = data['topics']
        data['page'] = upcoming_page
    # db = cur.execute("SELECT * FROM topics")
    # db1 = [x for x in db]
    print(upcoming_page)
    if upcoming_page == 0 or upcoming_page == (len(db1)//10 - 1):
        # async with state.proxy() as data:
        #  data['page'] = upcoming_page
        if upcoming_page == 0:
            print(f"{upcoming_page} -- 1 st page")
            c = db1[upcoming_page*10:upcoming_page*10+10]
            if len(c) == 10:
                await callback.message.edit_text(text=f"""1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()} \n4. {c[3][1].capitalize()} \n5. {c[4][1].capitalize()}\n6. {c[5][1].capitalize()} \n7. {c[6][1].capitalize()} \n8. {c[7][1].capitalize()} \n9. {c[8][1].capitalize()} \n10. {c[9][1].capitalize()} \nMavzuni tanlang.""",
                                      reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                              types.InlineKeyboardButton(text="4", callback_data=f"check_{c[3][0]}"),
                              types.InlineKeyboardButton(text="5", callback_data=f"check_{c[4][0]}"),
                              ],
                             [
                              types.InlineKeyboardButton(text="6", callback_data=f"check_{c[5][0]}"),
                              types.InlineKeyboardButton(text="7", callback_data=f"check_{c[6][0]}"),
                              types.InlineKeyboardButton(text="8", callback_data=f"check_{c[7][0]}"),
                              types.InlineKeyboardButton(text="9", callback_data=f"check_{c[8][0]}"),
                              types.InlineKeyboardButton(text="10", callback_data=f"check_{c[9][0]}"),
                              ],
                            [
                             types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
                              ]
                         ]))
        else:
            print(f"{upcoming_page} - last page")
            c = db1[upcoming_page*10:upcoming_page*10+10]
            print(len(c))
            if len(c) == 10:
                await callback.message.edit_text(text=f"""1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()} \n4. {c[3][1].capitalize()} \n5. {c[4][1].capitalize()}\n6. {c[5][1].capitalize()} \n7. {c[6][1].capitalize()} \n8. {c[7][1].capitalize()} \n9. {c[8][1].capitalize()} \n10. {c[9][1].capitalize()}\nMavzuni tanlang.""",
                                                 reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                                                            [
                                                             types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                                                             types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                                                             types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                                                             types.InlineKeyboardButton(text="4", callback_data=f"check_{c[3][0]}"),
                                                              types.InlineKeyboardButton(text="5", callback_data=f"check_{c[4][0]}"),
                                                              ],
                                                             [
                                                              types.InlineKeyboardButton(text="6", callback_data=f"check_{c[5][0]}"),
                                                              types.InlineKeyboardButton(text="7", callback_data=f"check_{c[6][0]}"),
                                                              types.InlineKeyboardButton(text="8", callback_data=f"check_{c[7][0]}"),
                                                              types.InlineKeyboardButton(text="9", callback_data=f"check_{c[8][0]}"),
                                                              types.InlineKeyboardButton(text="10", callback_data=f"check_{c[9][0]}"),
                                                              ],
                                                            [
                                                             types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page-1}"),
                                                                                                                         ]
                                                         ]))
                                
    elif upcoming_page > previous_page or upcoming_page < previous_page:
        print(f"{upcoming_page} > {previous_page}")
        # async with state.proxy() as data:
        #  data['page'] = upcoming_page
        # db = cur.execute("SELECT * FROM topics")
        # db1 = [x for x in db]
        c = db1[upcoming_page*10:upcoming_page*10+10]
        if len(c) == 10:
            await callback.message.edit_text(text=f"""1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()} \n4. {c[3][1].capitalize()} \n5. {c[4][1].capitalize()}\n6. {c[5][1].capitalize()} \n7. {c[6][1].capitalize()} \n8. {c[7][1].capitalize()} \n9. {c[8][1].capitalize()} \n10. {c[9][1].capitalize()}\nMavzuni tanlang.""",
                                      reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                                         [
                                          types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                                          types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                                          types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                                          types.InlineKeyboardButton(text="4", callback_data=f"check_{c[3][0]}"),
                                          types.InlineKeyboardButton(text="5", callback_data=f"check_{c[4][0]}"),
                                          ],
                                         [
                                          types.InlineKeyboardButton(text="6", callback_data=f"check_{c[5][0]}"),
                                          types.InlineKeyboardButton(text="7", callback_data=f"check_{c[6][0]}"),
                                          types.InlineKeyboardButton(text="8", callback_data=f"check_{c[7][0]}"),
                                          types.InlineKeyboardButton(text="9", callback_data=f"check_{c[8][0]}"),
                                          types.InlineKeyboardButton(text="10", callback_data=f"check_{c[9][0]}"),
                                          ],
                                        [
                                         types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page-1}"),
                                         types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
                                          ]
                                        ]))
        else:
            await callback.answer("Keyingi sahifa mavjud emas")
    # elif upcoming_page < previous_page:
    #     print(f"{upcoming_page} < {previous_page}")
    #     async with state.proxy() as data:
    #      data['page'] = upcoming_page
    #     db = cur.execute("SELECT * FROM topics")
    #     db1 = [x for x in db]
    #     c = db1[upcoming_page*3:upcoming_page*3+3]
    #     if len(c) == 3:
    #         await callback.message.edit_text(text = f"1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()}",
    #                                   reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    #                          [
    #                           types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
    #                           types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
    #                           types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}")
    #                         ],
    #                         [
    #                          types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page-1}"),
    #                          types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
    #                           ]
    #                      ]), 
    #                                   )
    # else:
    #         1/0


# special test(pro_1)   
@dp.callback_query_handler(lambda callback: callback.data.startswith("check_"))
async def special_tests_section(callback: types.CallbackQuery , state: FSMContext) -> None:
    topic_id = int(callback.data[str(callback.data).find("_")+1:])
    cur.execute(f"SELECT * FROM tests WHERE topic_id={topic_id}")# topic_id=11// butun sonlar
    tests = [x for x in cur] if cur else "ee"
    async with state.proxy() as data:
        data["page1"] = 0
        data['tests'] = tests
    if len(tests) >= 10:
        await callback.message.answer(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]}\n4. {tests[3][3]}\n5. {tests[4][3]}\n6. {tests[5][3]}\n7. {tests[6][3]}\n8. {tests[7][3]}\n9. {tests[8][3]}\n10. {tests[9][3]}",
                                  reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                                [
                                                 types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                 types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                 types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                                 types.InlineKeyboardButton(text="4", callback_data=f"check1_{tests[3][0]}"),
                                                 types.InlineKeyboardButton(text="5", callback_data=f"check1_{tests[4][0]}"),
                                                ],
                                                [
                                                 types.InlineKeyboardButton(text="6", callback_data=f"check1_{tests[5][0]}"),
                                                 types.InlineKeyboardButton(text="7", callback_data=f"check1_{tests[6][0]}"),
                                                 types.InlineKeyboardButton(text="8", callback_data=f"check1_{tests[7][0]}"),
                                                 types.InlineKeyboardButton(text="9", callback_data=f"check1_{tests[8][0]}"),
                                                 types.InlineKeyboardButton(text="10", callback_data=f"check1_{tests[9][0]}"),
                                                ],
                                                [
                                                 types.InlineKeyboardButton(text="➡️", callback_data=f"page1_1"),
                                                ]

                                  ]))
    else:
        await callback.answer("Sahifa mavjud emas")
     

# paginate test list for topic
@dp.callback_query_handler(lambda callback: callback.data.startswith("page1_"))
async def paginate_special_tests(callback: types.CallbackQuery, state: FSMContext) -> None:
    upcoming_page = int(callback.data[callback.data.find("_")+1:])
    async with  state.proxy() as data:
        previous_page = data['page1']
        test_list = data['tests']
        data['page1'] = upcoming_page
    # cur.execute("SELECT * FROM tests")
    # test_list = [test for test in cur]
    print(upcoming_page, len(test_list)//10-1)
    tests = test_list[upcoming_page*10:upcoming_page*10+10]
    if (upcoming_page == 0 or upcoming_page == len(test_list)//10-1) and len(tests) == 10:          
        if upcoming_page == 0:
            await callback.message.edit_text(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]} \n4. {tests[3][3]}\n5. {tests[4][3]}\n6. {tests[5][3]}\n7. {tests[6][3]}\n8. {tests[7][3]}\n9. {tests[8][3]}\n10. {tests[9][3]}",
                                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                                types.InlineKeyboardButton(text="4", callback_data=f"check1_{tests[3][0]}"),
                                                types.InlineKeyboardButton(text="5", callback_data=f"check1_{tests[4][0]}"),
                                                ],
                                                [
                                                 types.InlineKeyboardButton(text="6", callback_data=f"check1_{tests[5][0]}"),
                                                 types.InlineKeyboardButton(text="7", callback_data=f"check1_{tests[6][0]}"),
                                                 types.InlineKeyboardButton(text="8", callback_data=f"check1_{tests[7][0]}"),
                                                 types.InlineKeyboardButton(text="9", callback_data=f"check1_{tests[8][0]}"),
                                                 types.InlineKeyboardButton(text="10", callback_data=f"check1_{tests[9][0]}"),
                                                ],
                                             [
                                                
                                                types.InlineKeyboardButton(text="➡️", callback_data=f"page1_{upcoming_page+1}"),
                                            
                                         ]]))
        elif upcoming_page == len(test_list)//10-1:
            await callback.message.edit_text(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]}\n4. {tests[3][3]}\n5. {tests[4][3]}\n6. {tests[5][3]}\n7. {tests[6][3]}\n8. {tests[7][3]}\n9. {tests[8][3]}\n10. {tests[9][3]}",
                                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                                types.InlineKeyboardButton(text="4", callback_data=f"check1_{tests[3][0]}"),
                                                types.InlineKeyboardButton(text="5", callback_data=f"check1_{tests[4][0]}"),
                                                ],
                                                [
                                                 types.InlineKeyboardButton(text="6", callback_data=f"check1_{tests[5][0]}"),
                                                 types.InlineKeyboardButton(text="7", callback_data=f"check1_{tests[6][0]}"),
                                                 types.InlineKeyboardButton(text="8", callback_data=f"check1_{tests[7][0]}"),
                                                 types.InlineKeyboardButton(text="9", callback_data=f"check1_{tests[8][0]}"),
                                                 types.InlineKeyboardButton(text="10", callback_data=f"check1_{tests[9][0]}"),
                                                ],
                                             [
                                                types.InlineKeyboardButton(text="⬅️", callback_data=f"page1_{upcoming_page-1}"),
                                         ]]))
            
        
    elif (upcoming_page > previous_page or previous_page >upcoming_page) and len(tests) == 10:
        print(upcoming_page, "upcoming page")
        async with state.proxy() as data:
            data['page1'] = upcoming_page
        # tests = test_list[upcoming_page*10:upcoming_page*10+10]
        await callback.message.edit_text(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]}\n4. {tests[3][3]}\n5. {tests[4][3]}\n6. {tests[5][3]}\n7. {tests[6][3]}\n8. {tests[7][3]}\n9. {tests[8][3]}\n10. {tests[9][3]}",
                                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                                types.InlineKeyboardButton(text="4", callback_data=f"check1_{tests[3][0]}"),
                                                 types.InlineKeyboardButton(text="5", callback_data=f"check1_{tests[4][0]}"),
                                                ],
                                                [
                                                 types.InlineKeyboardButton(text="6", callback_data=f"check1_{tests[5][0]}"),
                                                 types.InlineKeyboardButton(text="7", callback_data=f"check1_{tests[6][0]}"),
                                                 types.InlineKeyboardButton(text="8", callback_data=f"check1_{tests[7][0]}"),
                                                 types.InlineKeyboardButton(text="9", callback_data=f"check1_{tests[8][0]}"),
                                                 types.InlineKeyboardButton(text="10", callback_data=f"check1_{tests[9][0]}"),
                                                ],
                                             [
                                                types.InlineKeyboardButton(text="⬅️", callback_data=f"page1_{upcoming_page-1}"),
                                                types.InlineKeyboardButton(text="➡️", callback_data=f"page1_{upcoming_page+1}"),
                                            
                                         ]]))
    else:
        await callback.answer("Testlar mavjud emas")
        
    
 

@dp.callback_query_handler(lambda callback: callback.data.startswith('check1_'))
async def start_test(callback: types.CallbackQuery, state: FSMContext) -> None:
    eachtest_id = int(callback.data[callback.data.find("_")+1:])
    cur.execute(f"SELECT * FROM each_tests WHERE tests_id={eachtest_id}")
    q_l  = [quest  for quest in cur] #question_list
    time = datetime.datetime.now().time()
    current_time = time.strftime("%H:%M:%S")
    end_time = (await func_one_hour_later(time)).strftime("%H:%M:%S")
    async with state.proxy() as data:
        data['page2'] = 0
        data['ql'] = q_l # question list
        data['start-time'] = time.strftime("%H:%M:%S")
        data['end-time'] = end_time
    await callback.message.answer(text=f"<em>Test boshlangan vaqt</em> : <b>{current_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n1. { q_l[0][2]}?\na) {q_l[0][3]}\nb) {q_l[0][4]}\nc) {q_l[0][5]}\nd) {q_l[0][6]}",
                          reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                              [types.InlineKeyboardButton(text="➡️", callback_data=f"page2_1")]
                          ]))


@dp.callback_query_handler(lambda callback: callback.data.startswith("page2_"))
async def paginate_test_questions(callback: types.CallbackQuery, state: FSMContext) -> None:
    upcoming_page = int(callback.data[callback.data.find("_")+1:]) 
    async with state.proxy() as data:
        previous_page = data['page2'] 
        ql = data['ql']
        data['page2'] == upcoming_page
        start_time = data['start-time']
        end_time = data['end-time']
    current_time = datetime.datetime.now().time().strftime("%H:%M:%S")
    # await asyncio.sleep(10)
    if end_time <= current_time:
        try:
            await callback.message.answer("Test yakunlandi. \n\n Testni tekshirish uchun, javoblarni — 'answers_abcdaacd...'shaklida yuboring",
                                      reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True,  keyboard=[
                                          [types.KeyboardButton(text="Asosiy menu", request_contact=True)]
                                      ]))
        except Exception as e:
            print(e)
            
        finally:
            print("tugadi...")
    else:
        if upcoming_page == 0 or upcoming_page == len(ql)-1:
            if upcoming_page == 0:
                test = ql[upcoming_page]
                await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}). {test[2]}?\nVariantlardan birini tanlang.\na) {test[3]}\nb) {test[4]}\nc) {test[5]}\nd) {test[6]}",
                                                 reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                                     [types.InlineKeyboardButton(text="➡️", callback_data=f"page2_{upcoming_page+1}")]
                                                 ]),
                                                 parse_mode="HTML")
            elif upcoming_page == len(ql)-1:
                print(upcoming_page, "max")


                test = ql[upcoming_page]
                await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}). {test[2]}?\nVariantlardan birini tanlang.\na) {test[3]}\nb) {test[4]}\nc) {test[5]}\nd) {test[6]}",
                                                 reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                                     [types.InlineKeyboardButton(text="⬅️", callback_data=f"page2_{upcoming_page-1}")]
                                                 ]),
                                                 parse_mode="HTML")
            else:
                1/0
        elif upcoming_page > previous_page or previous_page > upcoming_page:
            test = ql[upcoming_page]
            await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}).{test[2]}?\nVariantlardan birini tanlang.\na) {test[3]}\nb) {test[4]}\nc) {test[5]}\nd) {test[6]}",
                                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                                [
                                                    types.InlineKeyboardButton(text="⬅️", callback_data=f"page2_{upcoming_page-1}"),
                                                    types.InlineKeyboardButton(text="➡️", callback_data=f"page2_{upcoming_page+1}"),
                                                ]
                                             ]),
                                             parse_mode="HTML")

    
    

"""MAXSUS TESTLAR: END"""
"""OLIMPIADA TESTLARI: BEGIN"""
@dp.message_handler(lambda message: message.text == "Olimpiada testlari 🧑‍💻")
async def begin_contest_test(message: types.Message) -> None:
    await message.answer("Olimpiyada testlarini yechishni boshlash uchun sinfni tanlang", 
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [
                                 types.InlineKeyboardButton(text="1", callback_data="contest_1"),
                                 types.InlineKeyboardButton(text="2", callback_data="contest_2"),
                                 types.InlineKeyboardButton(text="3", callback_data="contest_3"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="4", callback_data="contest_4"),
                                 types.InlineKeyboardButton(text="5", callback_data="contest_5"),
                                 types.InlineKeyboardButton(text="6", callback_data="contest_6"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="7", callback_data="contest_7"),
                                 types.InlineKeyboardButton(text="8", callback_data="contest_8"),
                                 types.InlineKeyboardButton(text="9", callback_data="contest_9"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="10", callback_data="contest_10"),
                                 types.InlineKeyboardButton(text="11", callback_data="contest_11"),
                                 
                              ]
                         ]))

@dp.callback_query_handler(lambda callback: callback.data.startswith("contest_"))
async def send_test_id(callback: types. CallbackQuery) -> None:
    await callback.message.answer("Olimpiada testini boshlash uchun, identifikatsiya raqamini — 'id2_464546' shaklida yuboring")

@dp.message_handler(lambda message: message.text.startswith("id2_"))
async def start_contest_test(message: types.Message, state: FSMContext) -> None:
    contest_id = message.text[message.text.find("_")+1:]
    cur.execute(f"SELECT * FROM contest_tests WHERE contest_id={contest_id}")
    contest_tests = [test for test in cur]
    time = datetime.datetime.now().time()
    current_time = time.strftime("%H:%M:%S")
    end_time = (await func_one_hour_later(time)).strftime("%H:%M:%S")
    async with state.proxy() as data:
        data['contest_tests'] = contest_tests
        data['pagec'] = 0
        data['start-time1'] = time.strftime("%H:%M:%S")
        data['end-time1'] = end_time

    await message.answer(text=f"<em>Test boshlangan vaqt</em> : <b>{current_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n1.{contest_tests[0][2]}?\n\n\nVariantlardan birini tanlang.\na) {contest_tests[0][3]}\nb) {contest_tests[0][4]}\nc) {contest_tests[0][5]}\nd) {contest_tests[0][6]}",
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [types.InlineKeyboardButton(text="➡️", callback_data=f"contestpage_1")]
                         ]),
                         parse_mode="HTML")
    print(contest_id)


@dp.callback_query_handler(lambda callback: callback.data.startswith("contestpage_"))
async def start_contest_test(callback: types.CallbackQuery, state: FSMContext):
    print("blabla bla")
    upcoming_page = int(callback.data[callback.data.find("_")+1:])
    async with state.proxy() as data:
        tests = data['contest_tests']
        previous_page = data['pagec']
        data['pagec'] = upcoming_page
        start_time = data['start-time1']
        end_time = data['end-time1']
    if upcoming_page == 0 or upcoming_page == len(tests)-1:
        if upcoming_page == 0:
            await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}.{tests[upcoming_page][2]}?\n\n\nVariantlardan birini tanlang.\na) {tests[upcoming_page][3]}\nb) {tests[upcoming_page][4]}\nc) {tests[upcoming_page][5]}\nd) {tests[upcoming_page][6]}",
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [
                                  types.InlineKeyboardButton(text="➡️", callback_data=f"contestpage_{upcoming_page+1}"),
                                 ]
                         ]))
        elif upcoming_page == len(tests)-1:
            await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}.{tests[upcoming_page][2]}?\n\n\nVariantlardan birini tanlang.\na) {tests[upcoming_page][3]}\nb) {tests[upcoming_page][4]}\nc) {tests[upcoming_page][5]}\nd) {tests[upcoming_page][6]}",
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [
                                 types.InlineKeyboardButton(text="⬅️", callback_data=f"contestpage_{upcoming_page-1}"),
                                  ]
                         ]))
    elif upcoming_page > previous_page or previous_page > upcoming_page:
        await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}.{tests[upcoming_page][2]}?\n\n\nVariantlardan birini tanlang.\na) {tests[upcoming_page][3]}\nb) {tests[upcoming_page][4]}\nc) {tests[upcoming_page][5]}\nd) {tests[upcoming_page][6]}",
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [
                                 types.InlineKeyboardButton(text="⬅️", callback_data=f"contestpage_{upcoming_page-1}"),
                                 types.InlineKeyboardButton(text="➡️", callback_data=f"contestpage_{upcoming_page+1}"),
                                 ]
                         ]))
        
"""OLIMPIADA TESTLARI: END"""

"""MATH_BOOKS: BEGIN"""
@dp.message_handler(lambda message: message.text == "Math books pdf 📘")
async def get_grade_number(message: types.Message) -> None:
    await message.answer("Kitoblarni yuklab olish uchun sinfingizni tanlang.",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [
                                 types.InlineKeyboardButton(text="1", callback_data="grade_1"),
                                 types.InlineKeyboardButton(text="2", callback_data="grade_2"),
                                 types.InlineKeyboardButton(text="3", callback_data="grade_3"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="4", callback_data="grade_4"),
                                 types.InlineKeyboardButton(text="5", callback_data="grade_5"),
                                 types.InlineKeyboardButton(text="6", callback_data="grade_6"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="7", callback_data="grade_7"),
                                 types.InlineKeyboardButton(text="8", callback_data="grade_8"),
                                 types.InlineKeyboardButton(text="9", callback_data="grade_9"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="10", callback_data="grade_10"),
                                 types.InlineKeyboardButton(text="11", callback_data="grade_11"),
                                 
                              ]]))
    
@dp.callback_query_handler(lambda callback: callback.data.startswith('grade_'))
async def get_books_list(callback: types.CallbackQuery, state: FSMContext) ->None:
    grade_id = int(callback.data[callback.data.find("_")+1:])
    cur.execute(f"SELECT * FROM books WHERE grade_id={grade_id}")
    books = [book for book in cur]
    async with state.proxy() as data:
        data['book-list'] = books
        data['book-page'] = 0
    if len(books) > 3:
        await callback.message.edit_text(f"{books[0][0]}. {books[0][1]}\n{books[1][0]}. {books[1][1]}\n{books[2][0]}. {books[2][1]}",
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                         [
                                             types.InlineKeyboardButton(f"{books[0][1]}", callback_data=f"bookid_{books[0][0]}"),
                                             types.InlineKeyboardButton(f"{books[1][1]}", callback_data=f"bookid_{books[1][0]}"),
                                             types.InlineKeyboardButton(f"{books[2][1]}", callback_data=f"bookid_{books[2][0]}")
                                             ],
                                         [
                                             types.InlineKeyboardButton("➡️", callback_data="bookpage_1")
                                             ]]) )
    else:
        await callback.answer("Bu sinfda boshqa kitoblar mavjud emas.")

                                                                                                                     
    
@dp.callback_query_handler(lambda callback: callback.data.startswith("bookpage_"))
async def paginate_books(callback: types.CallbackQuery, state: FSMContext) -> None:
    upcoming_page = int(callback.data[callback.data.find("_")+1:])
    async with state.proxy() as data:
        previous_page = data['book-page']
        book_list = data['book-list']
        data['book-page'] = upcoming_page
    books = book_list[upcoming_page*3:upcoming_page*3+3]
    if (upcoming_page == 0 or upcoming_page == len(book_list)//3-1) and len(books)>3:
        if upcoming_page == 0:
            await callback.message.edit_text(f"{books[0][0]}. {books[0][1]}\n{books[1][0]}. {books[1][1]}\n{books[2][0]}. {books[2][1]}",
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                         [
                                             types.InlineKeyboardButton(f"{books[0][1]}", callback_data=f"bookid_{books[0][0]}"),
                                             types.InlineKeyboardButton(f"{books[1][1]}", callback_data=f"bookid_{books[1][0]}"),
                                             types.InlineKeyboardButton(f"{books[2][1]}", callback_data=f"bookid_{books[2][0]}")
                                             ],
                                         [                                            
                                             types.InlineKeyboardButton("➡️", callback_data=f"bookpage_{upcoming_page+1}")
                                             ]]) )
        elif upcoming_page == len(book_list)//3-1:
            await callback.message.edit_text(f"{books[0][0]}. {books[0][1]}\n{books[1][0]}. {books[1][1]}\n{books[2][0]}. {books[2][1]}",
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                         [
                                             types.InlineKeyboardButton(f"{books[0][1]}", callback_data=f"bookid_{books[0][0]}"),
                                             types.InlineKeyboardButton(f"{books[1][1]}", callback_data=f"bookid_{books[1][0]}"),
                                             types.InlineKeyboardButton(f"{books[2][1]}", callback_data=f"bookid_{books[2][0]}")
                                             ],
                                         [
                                             types.InlineKeyboardButton("⬅️", callback_data=f"bookpage_{upcoming_page-1}"),
                                            
                                             ]]) )
    elif (upcoming_page > previous_page or previous_page > upcoming_page) and len(books)>3:
        await callback.message.edit_text(f"{books[0][0]}. {books[0][1]}\n{books[1][0]}. {books[1][1]}\n{books[2][0]}. {books[2][1]}",
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                         [
                                             types.InlineKeyboardButton(f"{books[0][1]}", callback_data=f"bookid_{books[0][0]}"),
                                             types.InlineKeyboardButton(f"{books[1][1]}", callback_data=f"bookid_{books[1][0]}"),
                                             types.InlineKeyboardButton(f"{books[2][1]}", callback_data=f"bookid_{books[2][0]}")
                                             ],
                                         [
                                             types.InlineKeyboardButton("⬅️", callback_data=f"bookpage_{upcoming_page-1}"),
                                             types.InlineKeyboardButton("➡️", callback_data=f"bookpage_{upcoming_page+1}")
                                             ]]) )
    else:
        await callback.answer("Boshqa kitoblar mavjud emas.")
    


@dp.callback_query_handler(lambda callback: callback.data.startswith("bookid_"))
async def get_book(callback: types.CallbackQuery, state: FSMContext) -> None:
    book_id = int(callback.data[callback.data.find("_")+1:])
    try:
        book = cur.execute(f"SELECT * FROM books WHERE id={book_id}").fetchone()
        print(book)
        # await callback.message.delete()
        await bot.send_document(chat_id=callback.from_user.id,
                            document=book[3],
                            caption=f"{book[4]} - sinf {book[1]} darslik")
    except NameError:
        print("557.qator--book obyekti bo'sh", book, 5*"\n")

"""MATH_BOOKS: END"""
"""VIDEO_LESSONS:BEGIN"""
@dp.message_handler(lambda message: message.text == "Video darsliklar 🎞")
async def get_category_videolesson(message: types.Message) -> None:
    await message.answer(text="Kategoriyani tanlang", 
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [types.InlineKeyboardButton(text="Olimpiada", callback_data="categoryname_olimpiada")], 
                             [types.InlineKeyboardButton(text="Attestatsiya", callback_data="categoryname_attestatsiya")], 
                         ]))
    
@dp.callback_query_handler(lambda callback: callback.data.startswith("categoryname_"))
async def get_topic_video(callback: types.CallbackQuery, state:FSMContext)-> None:
    category = callback.data[callback.data.find("_")+1:]
    topics = [topic for topic in cur.execute(f"SELECT * FROM videos WHERE category='{category}' ORDER BY topic DESC")]
    async with state.proxy() as data:
        data['video_topic'] = topics
    if len(topics) >= 3:
        await callback.message.edit_text(f"1. {topics[0][2]}\n2. {topics[1][2]}\n3. {topics[2][2]}",
                                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                 types.InlineKeyboardButton(text="1", callback_data=f"videotopicid_{topics[0][0]}"),
                                                 types.InlineKeyboardButton(text="2", callback_data=f"videotopicid_{topics[1][0]}"),
                                                 types.InlineKeyboardButton(text="3", callback_data=f"videotopicid_{topics[2][0]}"),
                                              ]
                                         ]))
    else:
        await callback.answer("Bu kategoriya bo'yicha videodarsliklar mavjud emas")   
    print(category, topics)
    

@dp.callback_query_handler(lambda callback: callback.data.startswith("videotopicid_"))
async def get_videolesson(callback: types.CallbackQuery) -> None:
    topic_id = int(callback.data[callback.data.find("_")+1:])
    video = cur.execute(f"SELECT * FROM videos WHERE id={topic_id}").fetchone()
    print(f"SELECT 1 FROM videos WHERE id={topic_id}", topic_id, video)
    await bot.send_video(chat_id=callback.from_user.id,
                         video=video[1],
                         caption=f"{video}")
"""VIDEO_LESSONS:END"""

"""ADD BOOK TO DB: BEGIN"""
@dp.message_handler(commands=['add_book'])
async def start_add_book(message: types.Message):
    await message.answer("📗 Kitob qo'shish uchun, fan nomini yuboring! ",
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                             [
                                 types.InlineKeyboardButton(text="Matematika 📊"),
                                 types.InlineKeyboardButton(text="Geometriya 📐"),
                                 types.InlineKeyboardButton(text="Fizika 🌡"),  
                             ],
                             [
                                 types.InlineKeyboardButton(text="Kimyo 🧪"),
                                 types.InlineKeyboardButton(text="Biologiya 🧬"),
                                 types.InlineKeyboardButton(text="Tarix ⚔️"),  
                             ],
                             [
                                 types.InlineKeyboardButton(text="Ona tili ✏️"),
                                 types.InlineKeyboardButton(text="Rus tili 🖌"),
                                 types.InlineKeyboardButton(text="Ingliz tili 🖍"),  
                             ],
                         ]) )
    await BookStatesGroup.book.set()

@dp.message_handler(state=BookStatesGroup.book)
async def book_name_handler(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['book_name'] = message.text
    await message.reply("📥 Endi kitob faylini yuborishingiz mumkin")
    await BookStatesGroup.next()

@dp.message_handler(lambda message: not message.document, state=BookStatesGroup.destination)
async def check_book(message: types.Message):
    await message.reply("Bu kitob emas! Kitobning .pdf yoki .doc formatdagi faylini yuboring!")

@dp.message_handler(content_types=['document'], state=BookStatesGroup.destination)
async def get_book_id(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['book_id'] = message.document.file_id
    # print(message.document.file_id)
    # print(data)
    await message.reply("👨‍👦‍👦 Endi kitob qaysi sinf uchun ekanligini belgilang",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [
                                 types.InlineKeyboardButton(text="1", callback_data="bookgrade_1"),
                                 types.InlineKeyboardButton(text="2", callback_data="bookgrade_2"),
                                 types.InlineKeyboardButton(text="3", callback_data="bookgrade_3"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="4", callback_data="bookgrade_4"),
                                 types.InlineKeyboardButton(text="5", callback_data="bookgrade_5"),
                                 types.InlineKeyboardButton(text="6", callback_data="bookgrade_6"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="7", callback_data="bookgrade_7"),
                                 types.InlineKeyboardButton(text="8", callback_data="bookgrade_8"),
                                 types.InlineKeyboardButton(text="9", callback_data="bookgrade_9"),
                              ],
                             [
                                 types.InlineKeyboardButton(text="10", callback_data="bookgrade_10"),
                                 types.InlineKeyboardButton(text="11", callback_data="bookgrade_11"),
                                 
                              ]
                        ]))
    await BookStatesGroup.next()


@dp.callback_query_handler(lambda callback: callback.data.startswith("bookgrade_"), state=BookStatesGroup.grade)
async def get_book_grade(callback: types.CallbackQuery, state: FSMContext) -> None:
    grade = int(callback.data[callback.data.find("_")+1:])
    async with state.proxy() as data:
        data['book_grade_id'] = grade
        # print(data)
    await callback.message.reply("Kitob saqlandi, botdan foydalanishni davom etishingiz mumkin.\nYana kitob qo'shish uchun /add_book ustiga bosing.")
    await create_book_instance(state)
    await state.finish()
"""ADD BOOK TO DB: END"""

"""ADD VIDEO TO DB: BEGIN"""
@dp.message_handler(commands=['add_video'])
async def start_sending_video(message: types.Message) -> None:
    await message.answer("Videodarsliklar uchun kategoriya tanlang", 
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [types.InlineKeyboardButton(text="Olimpiada", callback_data="categoryname_olimpiada")], 
                             [types.InlineKeyboardButton(text="Attestatsiya", callback_data="categoryname_attestatsiya")], 
                         ]))
    await VideoStatesGroup.category.set()
    

@dp.callback_query_handler(lambda callback: callback.data.startswith("categoryname_"), state=VideoStatesGroup.category)
async def get_category_name(callback: types.CallbackQuery, state: FSMContext) -> None:
    category = callback.data[callback.data.find("_")+1:]
    async with state.proxy() as data:
        data['video_category'] = category
    await callback.message.reply("Videodarslik uchun mavzu nomini yozing")
    await VideoStatesGroup.next()

@dp.message_handler(state=VideoStatesGroup.topic)
async def get_video_topic(message: types.Message, state: FSMContext) -> None:
    topic  = message.text[message.text.find("_")+1:]
    async with state.proxy() as data:
        data['video_topic'] = topic
    await message.reply("Endi videodarslikni yuborishingiz mumkin")
    await VideoStatesGroup.next()

@dp.message_handler(content_types=['video'], state=VideoStatesGroup.video)
async def get_video_from_user(message: types.Message, state: FSMContext) -> None:
    video_id = message.video.file_id
    print(video_id)
    async with state.proxy() as data:
        data["video_id"] = video_id

    cur.execute("INSERT INTO videos VALUES(?,?,?,?)", (None, data["video_id"], data["video_topic"], data["video_category"]))
    conn.commit()
    await bot.send_video(chat_id=message.from_user.id,
                         video=data['video_id'],
                         caption=f" Videodarslik saqlandi. \n{data['video_category']} : {data['video_topic']} ")
    await state.finish()

"""ADD VIDEO TO DB: END"""

if __name__ == "__main__":
    logging.basicConfig(format=" %(asctime)s - %(name)s - %(levelname)s - %(message)s ", level=logging.INFO, stream=sys.stdout)
    # scheduler.start()
    executor.start_polling(dispatcher=dp,
                           on_startup=on_startup,
                           skip_updates=True,
                           )
