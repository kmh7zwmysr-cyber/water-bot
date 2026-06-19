import os
import threading
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ---------------- CONFIG ----------------
TOKEN = "8812668856:AAFNy6Fn1G_2aOKXum5vXyWmRLJX_ECjDAA"
ADMIN_ID = "5700067864"
PORT = int(os.getenv("PORT", "10000"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    size TEXT,
    count TEXT,
    address TEXT,
    phone TEXT,
    status TEXT
)
""")
conn.commit()

# ---------------- KEYBOARDS ----------------
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

repeat_kb = ReplyKeyboardMarkup(resize_keyboard=True)
repeat_kb.add(KeyboardButton("🔁 Повторить заказ"))


# ---------------- ADMIN PANEL ----------------
def admin_kb(order_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{order_id}"),
        InlineKeyboardButton("🚚 В доставке", callback_data=f"delivery_{order_id}")
    )
    kb.add(
        InlineKeyboardButton("📦 Завершить", callback_data=f"done_{order_id}")
    )
    return kb


# ---------------- START ----------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Закажите воду в Ростове-на-Дону", reply_markup=menu)


# ---------------- ORDER START ----------------
@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    cursor.execute("INSERT INTO orders (user_id, status) VALUES (?, ?)",
                   (message.from_user.id, "new"))
    conn.commit()

    message.answer("Выберите объём:", reply_markup=sizes)


# ---------------- SIZE ----------------
@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def size(message: types.Message):
    cursor.execute("SELECT id FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 1",
                   (message.from_user.id,))
    order_id = cursor.fetchone()[0]

    cursor.execute("UPDATE orders SET size=? WHERE id=?", (message.text, order_id))
    conn.commit()

    await message.answer("Сколько бутылок нужно?")


# ---------------- COUNT ----------------
@dp.message_handler(lambda m: m.text.isdigit())
async def count(message: types.Message):
    cursor.execute("SELECT id FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 1",
                   (message.from_user.id,))
    order_id = cursor.fetchone()[0]

    cursor.execute("UPDATE orders SET count=? WHERE id=?", (message.text, order_id))
    conn.commit()

    await message.answer("Город: Ростов-на-Дону", reply_markup=districts)


# ---------------- ADDRESS ----------------
@dp.message_handler(lambda m: m.text == "Ростов-на-Дону")
async def district(message: types.Message):
    await message.answer("Выберите время доставки:", reply_markup=times)


@dp.message_handler(lambda m: m.text in ["09:00-12:00", "12:00-16:00", "16:00-20:00"])
async def time(message: types.Message):
    await message.answer("Введите адрес:")


@dp.message_handler()
async def final(message: types.Message):
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 1",
                   (user_id,))
    order = cursor.fetchone()

    if not order:
        return

    order_id = order[0]

    if order[3] is None:
        cursor.execute("UPDATE orders SET address=? WHERE id=?", (message.text, order_id))
        conn.commit()
        await message.answer("Введите телефон:")
        return

    if order[4] is None:
        cursor.execute("UPDATE orders SET phone=?, status=? WHERE id=?",
                       (message.text, "new", order_id))
        conn.commit()

        text = f"""
🧾 НОВЫЙ ЗАКАЗ #{order_id}

📦 Объём: {order[2]}
📦 Кол-во: {order[3]}
🏠 Адрес: {order[4]}
📞 Телефон: {message.text}

📊 Статус: ⏳ Новый
"""

        await message.answer("✅ Заказ принят!", reply_markup=repeat_kb)

        await bot.send_message(
            ADMIN_ID,
            text,
            reply_markup=admin_kb(order_id)
        )

        return


# ---------------- REPEAT ORDER ----------------
@dp.message_handler(lambda m: m.text == "🔁 Повторить заказ")
async def repeat(message: types.Message):
    cursor.execute("""
        SELECT size, count, address, phone FROM orders
        WHERE user_id=? ORDER BY id DESC LIMIT 1
    """, (message.from_user.id,))

    last = cursor.fetchone()

    if not last:
        await message.answer("Нет предыдущих заказов")
        return

    size, count, address, phone = last

    await message.answer(f"""
🔁 Повтор заказа:

📦 {size}
📦 {count}
🏠 {address}
📞 {phone}
""")

    await message.answer("Нажмите 💧 Заказать воду для подтверждения")


# ---------------- STATUS CONTROL ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("confirm_"))
async def confirm(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
    conn.commit()

    await bot.send_message(ADMIN_ID, f"✅ Заказ #{order_id} подтверждён")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("delivery_"))
async def delivery(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='delivery' WHERE id=?", (order_id,))
    conn.commit()

    await bot.send_message(ADMIN_ID, f"🚚 Заказ #{order_id} в доставке")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("done_"))
async def done(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='done' WHERE id=?", (order_id,))
    conn.commit()

    await bot.send_message(ADMIN_ID, f"📦 Заказ #{order_id} завершён")
    await call.answer()


# ---------------- HEALTH ----------------
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


# ---------------- RUN ----------------
if __name__ == "__main__":
    threading.Thread(target=run_health, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
