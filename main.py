import os

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8812668856:AAFNy6Fn1G_2aOKXum5vXyWmRLJX_ECjDAA"
ADMIN_ID = "5700067864"

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ---------------- TEMP STORAGE ----------------
orders = {}

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

# ---------------- ADMIN BUTTONS ----------------
def admin_kb(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Принять", callback_data=f"ok_{user_id}"),
        InlineKeyboardButton("🚚 В доставке", callback_data=f"del_{user_id}")
    )
    kb.add
