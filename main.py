from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = "8812668856:AAH8ICErERpTfML_SGuy28pmVhqiZ_DKZBU"
ADMIN_ID = 5700067864

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}
order_status = {}

# ---------- КЛАВИАТУРЫ ----------

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💧 Заказать воду"))
menu.add(KeyboardButton("📦 Статус заказа"))

sizes = ReplyKeyboardMarkup(resize_keyboard=True)
sizes.row("0.5 л", "1 л")
sizes.row("5 л", "19 л")

after_order = ReplyKeyboardMarkup(resize_keyboard=True)
after_order.add(KeyboardButton("🔄 Новый заказ"))
after_order.add(KeyboardButton("❌ Отменить заказ"))
after_order.add(KeyboardButton("🏠 Главное меню"))
after_order.add(KeyboardButton("📦 Статус заказа"))

# ---------- START ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "💧 Доставка воды по Ростову-на-Дону\n\nВыберите действие:",
        reply_markup=menu
    )

# ---------- ГЛАВНОЕ МЕНЮ ----------

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def home(message: types.Message):
    await message.answer(
        "Главное меню",
        reply_markup=menu
    )

# ---------- НОВЫЙ ЗАКАЗ ----------

@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "Выберите объём воды:",
        reply_markup=sizes
    )

@dp.message_handler(lambda m: m.text == "🔄 Новый заказ")
async def new_order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "Выберите объём воды:",
        reply_markup=sizes
    )

# ---------- ОБЪЁМ ----------

@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def select_size(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    user_data[uid]["size"] = message.text
    await message.answer("Введите количество бутылок:")

# ---------- КОЛИЧЕСТВО ----------

@dp.message_handler(lambda m: m.text.isdigit())
async def select_count(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    if "count" not in user_data[uid]:
        user_data[uid]["count"] = message.text
        await message.answer("Введите адрес доставки:")

# ---------- ОТМЕНА ----------

@dp.message_handler(lambda m: m.text == "❌ Отменить заказ")
async def cancel_order(message: types.Message):
    uid = message.from_user.id

    user_data.pop(uid, None)
    order_status.pop(uid, None)

    await message.answer(
        "❌ Заказ отменён",
        reply_markup=menu
    )

# ---------- СТАТУС ----------

@dp.message_handler(lambda m: m.text == "📦 Статус заказа")
async def status(message: types.Message):
    uid = message.from_user.id

    if uid in order_status:
        await message.answer(
            f"📦 Статус заказа:\n{order_status[uid]}"
        )
    else:
        await message.answer(
            "❌ Активных заказов нет"
        )

# ---------- АДРЕС И ТЕЛЕФОН ----------

@dp.message_handler()
async def finish_order(message: types.Message):
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

        order_status[uid] = "✅ Заказ принят"

        text = (
            "🧾 НОВЫЙ ЗАКАЗ\n\n"
            f"💧 Объём: {data['size']}\n"
            f"📦 Количество: {data['count']}\n"
            f"🏠 Адрес: {data['address']}\n"
            f"📞 Телефон: {data['phone']}\n\n"
            f"👤 @{message.from_user.username or 'нет username'}\n"
            f"🆔 ID: {uid}\n"
            f"📍 Ростов-на-Дону"
        )

        await bot.send_message(ADMIN_ID, text)

        await message.answer(
            "✅ Ваш заказ принят!\n\nМы свяжемся с вами.",
            reply_markup=after_order
        )

        user_data.pop(uid, None)

# ---------- ЗАПУСК ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    