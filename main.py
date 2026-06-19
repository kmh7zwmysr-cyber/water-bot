import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = "8812668856:AAFNy6Fn1G_2aOKXum5vXyWmRLJX_ECjDAA"
ADMIN_ID = int(os.getenv("ADMIN_ID", "5700067864"))
PORT = int(os.getenv("PORT", "10000"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}
orders = {}

# ---------- USER MENU ----------
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💧 Заказать воду"))

sizes = ReplyKeyboardMarkup(resize_keyboard=True)
sizes.add("0.5 л", "1 л")
sizes.add("5 л", "19 л")

districts = ReplyKeyboardMarkup(resize_keyboard=True)
districts.add("Ростов-на-Дону")

times = ReplyKeyboardMarkup(resize_keyboard=True)
times.add("09:00-12:00")
times.add("12:00-16:00")
times.add("16:00-20:00")


# ---------- ADMIN INLINE BUTTONS ----------
def admin_kb(order_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{order_id}"),
        InlineKeyboardButton("🚚 В доставке", callback_data=f"delivery_{order_id}")
    )
    kb.add(
        InlineKeyboardButton("📦 Доставлен", callback_data=f"done_{order_id}")
    )
    return kb


# ---------- START ----------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Закажите воду в Ростове-на-Дону", reply_markup=menu)


# ---------- ORDER FLOW ----------
@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Выберите объём воды:", reply_markup=sizes)


@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def size(message: types.Message):
    if message.from_user.id not in user_data:
        return
    user_data[message.from_user.id]["size"] = message.text
    await message.answer("Сколько бутылок нужно?")


@dp.message_handler(lambda m: m.text.isdigit())
async def count(message: types.Message):
    if message.from_user.id not in user_data:
        return
    user_data[message.from_user.id]["count"] = message.text
    await message.answer("Город: Ростов-на-Дону", reply_markup=districts)


@dp.message_handler(lambda m: m.text == "Ростов-на-Дону")
async def district(message: types.Message):
    if message.from_user.id not in user_data:
        return
    user_data[message.from_user.id]["district"] = message.text
    await message.answer("Выберите время доставки:", reply_markup=times)


@dp.message_handler(lambda m: m.text in ["09:00-12:00", "12:00-16:00", "16:00-20:00"])
async def time(message: types.Message):
    if message.from_user.id not in user_data:
        return
    user_data[message.from_user.id]["time"] = message.text
    await message.answer("Введите адрес доставки:")


# ---------- FINAL STEP ----------
@dp.message_handler()
async def final(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        return

    data = user_data[user_id]

    if "address" not in data:
        data["address"] = message.text
        await message.answer("Введите номер телефона:")
        return

    data["phone"] = message.text

    order_id = str(user_id)

    text = f"""
🧾 НОВЫЙ ЗАКАЗ

💧 Объём: {data['size']}
📦 Кол-во: {data['count']}
📍 Город: Ростов-на-Дону
⏰ Время: {data['time']}
🏠 Адрес: {data['address']}
📞 Телефон: {data['phone']}

📊 Статус: ⏳ Новый заказ
"""

    orders[order_id] = text

    await message.answer("✅ Ваша заявка принята!")

    await bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=admin_kb(order_id)
    )

    user_data.pop(user_id, None)


# ---------- STATUS UPDATES ----------
@dp.callback_query_handler(lambda c: c.data.startswith("confirm_"))
async def confirm(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]
    await bot.send_message(call.message.chat.id, "✅ Статус: Заказ подтверждён")
    await call.answer("Подтверждено")


@dp.callback_query_handler(lambda c: c.data.startswith("delivery_"))
async def delivery(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]
    await bot.send_message(call.message.chat.id, "🚚 Статус: Заказ в доставке")
    await call.answer("В доставке")

    # уведомление клиенту
    try:
        await bot.send_message(int(order_id), "🚚 Ваш заказ в пути!")
    except:
        pass


@dp.callback_query_handler(lambda c: c.data.startswith("done_"))
async def done(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]
    await bot.send_message(call.message.chat.id, "📦 Статус: Заказ доставлен")
    await call.answer("Доставлен")

    try:
        await bot.send_message(int(order_id), "📦 Ваш заказ доставлен. Спасибо!")
    except:
        pass


# ---------- HEALTH ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass


def run_health():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=run_health, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
