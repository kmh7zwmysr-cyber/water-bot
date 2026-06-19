from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = "8812668856:AAETsHrAB0cObkYon2JAAcOll0qAp1KHsWY"
ADMIN_ID = "5700067864"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}

# ---------------- КЛАВИАТУРЫ ----------------

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💧 Заказать воду"))

sizes = ReplyKeyboardMarkup(resize_keyboard=True)
sizes.row("0.5 л", "1 л")
sizes.row("5 л", "19 л")

after_order = ReplyKeyboardMarkup(resize_keyboard=True)
after_order.add(
    KeyboardButton("🔄 Новый заказ"),
    KeyboardButton("❌ Отменить заказ")
)
after_order.add(KeyboardButton("📦 Статус заказа"))

# ---------------- START ----------------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "💧 Доставка воды по Ростову-на-Дону",
        reply_markup=menu
    )

# ---------------- НАЧАТЬ ЗАКАЗ ----------------

@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Выберите объём:", reply_markup=sizes)

# ---------------- ВЫБОР ОБЪЁМА ----------------

@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def size(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        return

    user_data[uid]["size"] = message.text
    await message.answer("Сколько бутылок нужно?")

# ---------------- КОЛИЧЕСТВО ----------------

@dp.message_handler(lambda m: m.text.isdigit())
async def count(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        return

    data = user_data[uid]

    if "count" not in data:
        data["count"] = message.text
        await message.answer("Введите адрес доставки:")
        return

# ---------------- АДРЕС + ТЕЛЕФОН ----------------

@dp.message_handler()
async def finish(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    data = user_data[uid]

    if "address" not in data:
        data["address"] = message.text
        await message.answer("Введите номер телефона:")
        return

    if "phone" not in data:
        data["phone"] = message.text

        text = f"""
🧾 НОВЫЙ ЗАКАЗ

💧 Объём: {data['size']}
📦 Кол-во: {data['count']}
🏠 Адрес: {data['address']}
📞 Телефон: {data['phone']}

👤 @{message.from_user.username or "нет username"}
🆔 {uid}
📍 Ростов-на-Дону
"""

        await bot.send_message(ADMIN_ID, text)

        await message.answer(
            "✅ Заказ принят!\nВыберите действие:",
            reply_markup=after_order
        )

        user_data.pop(uid, None)

# ---------------- НОВЫЙ ЗАКАЗ ----------------

@dp.message_handler(lambda m: m.text == "🔄 Новый заказ")
async def new_order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Выберите объём:", reply_markup=sizes)

# ---------------- ОТМЕНА ----------------

@dp.message_handler(lambda m: m.text == "❌ Отменить заказ")
async def cancel(message: types.Message):
    user_data.pop(message.from_user.id, None)
    await message.answer("❌ Заказ отменён", reply_markup=menu)

# ---------------- СТАТУС ----------------

@dp.message_handler(lambda m: m.text == "📦 Статус заказа")
async def status(message: types.Message):
    if message.from_user.id in user_data:
        await message.answer("📦 У вас есть незавершённый заказ")
    else:
        await message.answer("❌ Активных заказов нет")

# ---------------- RUN ----------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)