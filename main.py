import os
import asyncio
import asyncpg

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = "8812668856:AAFNy6Fn1G_2aOKXum5vXyWmRLJX_ECjDAA"
ADMIN_ID = "5700067864"

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ---------------- DB ----------------
DB = None

async def init_db():
    global DB
    DB = await asyncpg.create_pool(os.getenv("DATABASE_URL"))

# ---------------- FSM ----------------
class Order(StatesGroup):
    size = State()
    count = State()
    address = State()
    phone = State()

# ---------------- KEYBOARD ----------------
menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("💧 Заказать воду")

sizes = types.ReplyKeyboardMarkup(resize_keyboard=True)
sizes.add("0.5 л", "1 л", "5 л", "19 л")

district = types.ReplyKeyboardMarkup(resize_keyboard=True)
district.add("Ростов-на-Дону")

times = types.ReplyKeyboardMarkup(resize_keyboard=True)
times.add("09:00-12:00", "12:00-16:00", "16:00-20:00")

# ---------------- START ----------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🚀 Быстрый бот доставки воды", reply_markup=menu)

# ---------------- ORDER ----------------
@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    await Order.size.set()
    await message.answer("Выберите объём:", reply_markup=sizes)

@dp.message_handler(state=Order.size)
async def size(message: types.Message, state: FSMContext):
    await state.update_data(size=message.text)
    await Order.next()
    await message.answer("Сколько бутылок?")

@dp.message_handler(state=Order.count)
async def count(message: types.Message, state: FSMContext):
    await state.update_data(count=message.text)
    await Order.next()
    await message.answer("Адрес в Ростове-на-Дону:")

@dp.message_handler(state=Order.address)
async def address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await Order.next()
    await message.answer("Введите телефон:")

@dp.message_handler(state=Order.phone)
async def phone(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await DB.execute("""
        INSERT INTO orders(user_id, size, count, address, phone, status)
        VALUES($1,$2,$3,$4,$5,'new')
    """, message.from_user.id,
         data['size'],
         data['count'],
         data['address'],
         message.text)

    await message.answer("✅ Заказ принят!")

    await bot.send_message(
        ADMIN_ID,
        f"""
🧾 НОВЫЙ ЗАКАЗ

📦 {data['size']}
📦 {data['count']}
🏠 {data['address']}
📞 {message.text}

📊 Статус: NEW
"""
    )

    await state.finish()

# ---------------- STATUS ----------------
@dp.message_handler(commands=['orders'])
async def orders(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    rows = await DB.fetch("SELECT * FROM orders ORDER BY id DESC LIMIT 10")

    text = "📦 Последние заказы:\n\n"
    for r in rows:
        text += f"#{r['id']} | {r['size']} | {r['status']}\n"

    await message.answer(text)

# ---------------- START BOT ----------------
async def on_startup(_):
    await init_db()

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
