import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = "8812668856:AAFNy6Fn1G_2aOKXum5vXyWmRLJX_ECjDAA"
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
PORT = int(os.getenv("PORT", "10000"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💧 Заказать воду"))

sizes = ReplyKeyboardMarkup(resize_keyboard=True)
sizes.add("0.5 л", "1 л")
sizes.add("5 л", "19 л")

districts = ReplyKeyboardMarkup(resize_keyboard=True)
districts.add("Центр", "Север")
districts.add("Юг", "Запад", "Восток")

times = ReplyKeyboardMarkup(resize_keyboard=True)
times.add("09:00-12:00")
times.add("12:00-16:00")
times.add("16:00-20:00")


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Добро пожаловать!\n💧 Закажите доставку воды", reply_markup=menu)


@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Выберите объём воды:", reply_markup=sizes)


@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def size(message: types.Message):
    user_data[message.from_user.id]["size"] = message.text
    await message.answer("Сколько бутылок нужно?")


@dp.message_handler(lambda m: m.text.isdigit())
async def count(message: types.Message):
    user_data[message.from_user.id]["count"] = message.text
    await message.answer("Выберите район доставки:", reply_markup=districts)


@dp.message_handler(lambda m: m.text in ["Центр", "Север", "Юг", "Запад", "Восток"])
async def district(message: types.Message):
    user_data[message.from_user.id]["district"] = message.text
    await message.answer("Выберите время доставки:", reply_markup=times)


@dp.message_handler(lambda m: "09:" in m.text or "12:" in m.text or "16:" in m.text)
async def time(message: types.Message):
    user_data[message.from_user.id]["time"] = message.text
    await message.answer("Введите адрес доставки:")


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

    order_text = f"""
🧾 НОВЫЙ ЗАКАЗ

💧 Объём: {data['size']}
📦 Кол-во: {data['count']}
📍 Район: {data['district']}
⏰ Время: {data['time']}
🏠 Адрес: {data['address']}
📞 Телефон: {data['phone']}
"""

    await message.answer("✅ Заказ принят!")
    await bot.send_message(ADMIN_ID, order_text)

    user_data.pop(user_id, None)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
