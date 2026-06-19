from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = "8812668856:AAETsHrAB0cObkYon2JAAcOll0qAp1KHsWY"
ADMIN_ID = "5700067864"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}
order_status = {}

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💧 Заказать воду"))
menu.add(KeyboardButton("📦 Статус заказа"))

sizes = ReplyKeyboardMarkup(resize_keyboard=True)
sizes.row("0.5 л", "1 л")
sizes.row("5 л", "19 л")

after_order = ReplyKeyboardMarkup(resize_keyboard=True)
after_order.add("🔄 Новый заказ")
after_order.add("❌ Отменить заказ")
after_order.add("📦 Статус заказа")


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "💧 Доставка воды по Ростову-на-Дону",
        reply_markup=menu
    )


@dp.message_handler(lambda m: m.text == "💧 Заказать воду")
async def order_start(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "Выберите объём воды:",
        reply_markup=sizes
    )


@dp.message_handler(lambda m: m.text in ["0.5 л", "1 л", "5 л", "19 л"])
async def get_size(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    user_data[uid]["size"] = message.text
    await message.answer("Введите количество бутылок:")


@dp.message_handler(lambda m: m.text.isdigit())
async def get_count(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        return

    if "count" not in user_data[uid]:
        user_data[uid]["count"] = message.text
        await message.answer("Введите адрес доставки:")
        return


@dp.message_handler(commands=["done"])
async def complete_order(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        client_id = int(message.get_args())

        order_status[client_id] = "✅ Доставлен"

        await bot.send_message(
            client_id,
            "🎉 Ваш заказ успешно доставлен!"
        )

        await message.answer("Заказ закрыт.")

    except:
        await message.answer("Пример: /done 123456789")


@dp.message_handler(lambda m: m.text == "📦 Статус заказа")
async def status(message: types.Message):
    st = order_status.get(
        message.from_user.id,
        "❌ Активных заказов нет"
    )

    await message.answer(f"Статус заказа:\n{st}")


@dp.message_handler(lambda m: m.text == "🔄 Новый заказ")
async def new_order(message: types.Message):
    user_data[message.from_user.id] = {}

    await message.answer(
        "Выберите объём воды:",
        reply_markup=sizes
    )


@dp.message_handler(lambda m: m.text == "❌ Отменить заказ")
async def cancel_order(message: types.Message):
    user_data.pop(message.from_user.id, None)
    order_status.pop(message.from_user.id, None)

    await message.answer(
        "❌ Заказ отменён",
        reply_markup=menu
    )


@dp.message_handler()
async def process(message: types.Message):
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

        order_status[uid] = "📦 Принят"

        text = f"""
🧾 НОВЫЙ ЗАКАЗ

💧 Объём: {data['size']}
📦 Количество: {data['count']}
🏠 Адрес: {data['address']}
📞 Телефон: {data['phone']}

👤 @{message.from_user.username}
🆔 {uid}

Статус: ПРИНЯТ
"""

        await bot.send_message(ADMIN_ID, text)

        await message.answer(
            "✅ Заказ принят!\n\nОператор скоро свяжется с вами.",
            reply_markup=after_order
        )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)