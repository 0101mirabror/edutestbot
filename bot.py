from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import ADMINS, TOKEN_API
import sqlite3
import os, datetime, logging, sys  
from sqlitedb import db_start, create_profile, edit_profile, check_user_registered,  func_one_hour_later
from apscheduler.schedulers.asyncio import AsyncIOScheduler

k = ADMINS
bot = Bot(token=TOKEN_API)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
scheduler = AsyncIOScheduler()

async def on_startup(_):
    await db_start()
    schedule_jobs()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_dir = (BASE_DIR + '\\new.db')
conn = sqlite3.connect(database=db_dir)
cur = conn.cursor()

# user-profile creation
class ProfileStatesGroup(StatesGroup): #1)name, 2)photo, 3)age, 4)description
    name = State()
    photo = State()
    age = State()
    description = State()

# cancel button
def get_cancel_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(text="/cancel")]
    ])

# start handler, works when '/start' is typed  //lambda message: message.text == "Asosiy menu",
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    # await bot.send_message(chat_id=ADMINS[0], text="Taymer xabari")
    user = cur.execute("SELECT 1 FROM users WHERE id = '{user_id}'".format(user_id=message.from_user.id)).fetchone()
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
        await create_profile(user_id=message.from_user.id)


def schedule_jobs():
    scheduler.add_job(paginate_test_questions, "interval", minutes=1, args=(dp,))

"""USER PROFILE CREATE"""
# create handler, begins user creation process
@dp.message_handler(commands=['create'])
async def cmd_create(message: types.Message) -> None:
    await message.reply("Ro'yxatdan o'tish uchun, ism-familiyangizni yuboring",
                    reply_markup=get_cancel_keyboard())
    await ProfileStatesGroup.name.set()

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
    await message.reply("Profil uchun izoh yozing")
    await ProfileStatesGroup.next()

# save all data to database
@dp.message_handler(state=ProfileStatesGroup.description)
async def load_description(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['description'] = message.text
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
   

# special tests(pro_1)
@dp.message_handler(lambda message: message.text == "Maxsus testlar 💸")
async def check_authenticated_user(message: types.Message, state: FSMContext) -> None:
    member = await bot.get_chat_member("-4161593971", message.from_user.id)
    print(message.chat.id)
    await message.answer(text="Testni boshlash uchun kerakli mavzuni tanlang!!!", reply_markup=types.ReplyKeyboardRemove())
    async with state.proxy() as data:
        data['page'] = 0  
    if not member.is_chat_member():
        await message.reply("Siz guruhga a'zo emassiz!",
                            reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                                [types.InlineKeyboardButton(text="Guruhga qo'shilish", url="https://t.me/+2hmwl23svbVlZDQy")]
                            ]))  
    else:
        db = cur.execute("SELECT * FROM topics")
        db1 = [x for x in db]
        c = db1[:5]
        await message.answer(text=f"""1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()} \n4. {c[3][1].capitalize()} \n5. {c[4][1].capitalize()}\nMavzuni tanlang.""",
                            reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                              types.InlineKeyboardButton(text="4", callback_data=f"check_{c[3][0]}"),
                              types.InlineKeyboardButton(text="5", callback_data=f"check_{c[4][0]}"),
                              ],
                            [
                            #  types.InlineKeyboardButton(text="⬅️", callback_data="page_0"),
                             types.InlineKeyboardButton(text="➡️", callback_data="page_1"),
                              ]
                         ]), 
                         parse_mode="HTML")

# special test(pro_1)   
@dp.callback_query_handler(lambda callback: callback.data.startswith("check_"))
async def special_tests_section(callback: types.CallbackQuery , state: FSMContext) -> None:
    topic_id = int(callback.data[str(callback.data).find("_")+1:])
    cur.execute(f"SELECT * FROM tests WHERE topic_id={topic_id}")# topic_id=11// butun sonlar
    tests = [x for x in cur] if cur else "ee"
    async with state.proxy() as data:
        data["page1"] = 0
    await callback.message.answer(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]}",
                                  reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                      [
                                                 types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                 types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                 types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                              ],
                                    # [types.InlineKeyboardButton(text="⬅️", callback_data=f"page1_"),
                                    [types.InlineKeyboardButton(text="➡️", callback_data=f"page1_1"),]

                                  ]))
import asyncio

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
    # await asyncio.sleep(10)
    await callback.message.answer(text=f"<em>Test boshlangan vaqt</em> : <b>{current_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n1. { q_l[0][2]}?\na) {q_l[0][3]}\nb) {q_l[0][4]}\nc) {q_l[0][5]}\nd) {q_l[0][6]}",
                          reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                              [types.InlineKeyboardButton(text="➡️", callback_data=f"page2_1")]
                          ]),
                          parse_mode="HTML")


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
                                                    #  [
                                                    #     types.InlineKeyboardButton(text="A", callback_data="answer_1"),
                                                    #     types.InlineKeyboardButton(text="B", callback_data="answer_2"),
                                                    #     types.InlineKeyboardButton(text="C", callback_data="answer_3"),
                                                    #     types.InlineKeyboardButton(text="D", callback_data="answer_4"),
                                                    #     ],
                                                     [types.InlineKeyboardButton(text="⬅️", callback_data=f"page2_{upcoming_page-1}")]
                                                 ]),
                                                 parse_mode="HTML")
            else:
                1/0
        elif upcoming_page > previous_page or previous_page > upcoming_page:
            test = ql[upcoming_page]
            await callback.message.edit_text(text=f"<em>Test boshlangan vaqt</em> : <b>{start_time}</b>\n<em>Test tugash vaqti</em> : <b>{end_time}</b>\n\n{upcoming_page+1}).{test[2]}?\nVariantlardan birini tanlang.\na) {test[3]}\nb) {test[4]}\nc) {test[5]}\nd) {test[6]}",
                                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                                #  [
                                                #     types.InlineKeyboardButton(text="A", callback_data="answer_1"),
                                                #     types.InlineKeyboardButton(text="B", callback_data="answer_2"),
                                                #     types.InlineKeyboardButton(text="C", callback_data="answer_3"),
                                                #     types.InlineKeyboardButton(text="D", callback_data="answer_4"),
                                                #     ],
                                                [
                                                    types.InlineKeyboardButton(text="⬅️", callback_data=f"page2_{upcoming_page-1}"),
                                                    types.InlineKeyboardButton(text="➡️", callback_data=f"page2_{upcoming_page+1}"),
                                                ]
                                             ]),
                                             parse_mode="HTML")

    
# paginate test list for topic
@dp.callback_query_handler(lambda callback: callback.data.startswith("page1_"))
async def paginate_special_tests(callback: types.CallbackQuery, state: FSMContext) -> None:
    upcoming_page = int(callback.data[callback.data.find("_")+1:])
    async with  state.proxy() as data:
        previous_page = data['page1']
    cur.execute("SELECT * FROM tests")
    test_list = [test for test in cur]
    print(upcoming_page, len(test_list)//3-1)
    if upcoming_page == 0 or upcoming_page == len(test_list)//3-1:
        async with state.proxy() as data:
            data['page1'] = upcoming_page
        tests = test_list[upcoming_page*3:upcoming_page*3+3]
        if upcoming_page == 0:
            await callback.message.edit_text(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]}",
                                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                              ],
                                             [
                                                
                                                types.InlineKeyboardButton(text="➡️", callback_data=f"page1_{upcoming_page+1}"),
                                            
                                         ]]))
        elif upcoming_page == len(test_list)//3-1:
            await callback.message.edit_text(text=f"1. {tests[0][3]}\n2. {tests[1][3]}\n3. {tests[2][3]}",
                                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                              ],
                                             [
                                                types.InlineKeyboardButton(text="⬅️", callback_data=f"page1_{upcoming_page-1}"),
                                         ]]))
            
        
    elif upcoming_page > previous_page or previous_page >upcoming_page:
        print(upcoming_page, "upcoming page")
        async with state.proxy() as data:
            data['page1'] = upcoming_page
        tests = test_list[upcoming_page*3:upcoming_page*3+3]
        await callback.message.edit_text(text=f"1. {tests[0][3]} \n2. {tests[1][3]} \n3. {tests[2][3]}",
                                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                             [
                                                types.InlineKeyboardButton(text="1", callback_data=f"check1_{tests[0][0]}"),
                                                types.InlineKeyboardButton(text="2", callback_data=f"check1_{tests[1][0]}"),
                                                types.InlineKeyboardButton(text="3", callback_data=f"check1_{tests[2][0]}"),
                                              ],
                                             [
                                                types.InlineKeyboardButton(text="⬅️", callback_data=f"page1_{upcoming_page-1}"),
                                                types.InlineKeyboardButton(text="➡️", callback_data=f"page1_{upcoming_page+1}"),
                                            
                                         ]]))
        
        
# "maxsus testlar"'s topics
@dp.callback_query_handler(lambda x: x.data.startswith('page_'))
async def paginate_data(callback: types.CallbackQuery, state: FSMContext) -> None:
    upcoming_page = int(callback.data[callback.data.find('_')+1:])
    async with state.proxy() as data:
        previous_page = data['page']
    db = cur.execute("SELECT * FROM topics")
    db1 = [x for x in db]
    print(upcoming_page)
    if upcoming_page == 0 or upcoming_page == (len(db1)//3 - 1):
        async with state.proxy() as data:
         data['page'] = upcoming_page
        if upcoming_page == 0:
            print(f"{upcoming_page} -- 1 st page")
            c = db1[upcoming_page*3:upcoming_page*3+3]
            if len(c) == 3:
                await callback.message.edit_text(text = f"1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()}",
                                      reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                              ],
                            #   types.InlineKeyboardButton(text="4", callback_data="check_(question_id)"),
                            #   types.InlineKeyboardButton(text="5", callback_data="check_(question_id)"),
                            #   ],
                            #  [types.InlineKeyboardButton(text="6", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="7", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="8", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="9", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="10",callback_data='check_2'),
                            #   ],
                            [
                            #  types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page}"),
                             types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
                              ]
                         ]), 
                          parse_mode="HTML" )
        else:
            print(f"{upcoming_page} - last page")
            c = db1[upcoming_page*3:upcoming_page*3+3]
            print(len(c))
            if len(c) == 3:
                await callback.message.edit_text(text = f"1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()}",
                                      reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                              ],
                            #   types.InlineKeyboardButton(text="4", callback_data="check_(question_id)"),
                            #   types.InlineKeyboardButton(text="5", callback_data="check_(question_id)"),
                            #   ],
                            #  [types.InlineKeyboardButton(text="6", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="7", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="8", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="9", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="10",callback_data='check_2'),
                            #   ],
                            [
                             types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page-1}"),
                            #  types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
                              ]
                         ]), 
                          parse_mode="HTML" )

    elif upcoming_page > previous_page:
        print(f"{upcoming_page} > {previous_page}")
        async with state.proxy() as data:
         data['page'] = upcoming_page
        db = cur.execute("SELECT * FROM topics")
        db1 = [x for x in db]
        c = db1[upcoming_page*3:upcoming_page*3+3]
        if len(c) == 3:
            await callback.message.edit_text(text = f"1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()}",
                                      reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}"),
                              ],
                            #   types.InlineKeyboardButton(text="4", callback_data="check_(question_id)"),
                            #   types.InlineKeyboardButton(text="5", callback_data="check_(question_id)"),
                            #   ],
                            #  [types.InlineKeyboardButton(text="6", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="7", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="8", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="9", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="10",callback_data='check_2'),
                            #   ],
                            [
                             types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page-1}"),
                             types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
                              ]
                         ]), 
                          parse_mode="HTML" )
    elif upcoming_page < previous_page:
        print(f"{upcoming_page} < {previous_page}")
        async with state.proxy() as data:
         data['page'] = upcoming_page
        db = cur.execute("SELECT * FROM topics")
        db1 = [x for x in db]
        c = db1[upcoming_page*3:upcoming_page*3+3]
        if len(c) == 3:
            await callback.message.edit_text(text = f"1. {c[0][1].capitalize()} \n2. {c[1][1].capitalize()} \n3. {c[2][1].capitalize()}",
                                      reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                             [
                              types.InlineKeyboardButton(text="1", callback_data=f"check_{c[0][0]}"),
                              types.InlineKeyboardButton(text="2", callback_data=f"check_{c[1][0]}"),
                              types.InlineKeyboardButton(text="3", callback_data=f"check_{c[2][0]}")
                            ],
                            #   types.InlineKeyboardButton(text="4", callback_data="check_(question_id)"),
                            #   types.InlineKeyboardButton(text="5", callback_data="check_(question_id)"),
                            #   ],
                            #  [types.InlineKeyboardButton(text="6", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="7", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="8", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="9", callback_data='check_2'),
                            #   types.InlineKeyboardButton(text="10",callback_data='check_2'),
                            #   ],
                            [
                             types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{upcoming_page-1}"),
                             types.InlineKeyboardButton(text="➡️", callback_data=f"page_{upcoming_page+1}"),
                              ]
                         ]), 
                                      )
        else:
            1/0
     
  
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    scheduler.start()
    executor.start_polling(dispatcher=dp,
                           on_startup=on_startup,
                           skip_updates=True,
                           )
