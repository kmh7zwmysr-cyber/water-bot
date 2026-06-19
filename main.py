from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = "8812668856:AAETsHrAB0cObkYon2JAAcOll0qAp1KHsWY"
ADMIN_ID = 5700067864

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💧 Заказать воду"))

sizes = ReplyKeyboardMarkup(resize_keyboard=True)
sizes.row("0.5 л", "1 л")
sizes.row("5 л", "19 л")


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "💧 Доставка воды по Ростову-на-Дону\n\n"
        "Нажмите кнопку ниже для оформления заказа.",
        reply_markup=menu
    )


@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Выберите объём воды:", reply_markup=sizes)


@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def select_size(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    user_data[uid]["size"] = message.text
    await message.answer("Введите количество бутылок:")


@dp.message_handler(lambda m: m.text.isdigit())
async def select_count(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    user_data[uid]["count"] = message.text
    await message.answer("Введите адрес доставки:")


@dp.message_handler()
async def process_order(message: types.Message):
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

        order_text = (
            "🧾 НОВЫЙ ЗАКАЗ\n\n"
            f"💧 Объём: {data['size']}\n"
            f"📦 Количество: {data['count']}\n"
            f"🏠 Адрес: {data['address']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"👤 Клиент: @{message.from_user.username or 'нет username'}\n"
            f"🆔 ID: {message.from_user.id}\n"
            "📍 Город: Ростов-на-Дону"
        )

        await message.answer(
            "✅ Ваш заказ успешно принят!\n\n"
            "Наш оператор свяжется с вами."
        )

        await bot.send_message(ADMIN_ID, order_text)

        user_data.pop(uid, None)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
