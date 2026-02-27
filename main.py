import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiohttp import web

# === НАСТРОЙКИ ===
TOKEN = '8603676379:AAFy5l6IzXimtUU96S431mecSPXdj9TH1vQ'
BOSS_ID = 5119763247 
RANKS_FILE = 'ranks.json'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ОПИСАНИЯ РАНГОВ ---
RANK_DETAILS = {
    "5": "<b>Ранг 5: Консильери</b>\n\nПредставитель банды. Ведет переговоры.",
    "4": "<b>Ранг 4: Бригадир</b>\n\nКонтролирует дисциплину и ранги 3-1.",
    "3": "<b>Ранг 3: Управляющий</b>\n\nСледит за выполнением приказов.",
    "2": "<b>Ранг 2: Образованный</b>\n\nСледит за новичками.",
    "Страж": "<b>Ранг: Страж</b>\n\nОхрана периметра и сигнал тревоги.",
    "1": "<b>Ранг 1: Новичок</b>\n\nВыполняет черновую работу."
}

# --- ПАМЯТЬ ---
def load_ranks():
    if os.path.exists(RANKS_FILE):
        try:
            with open(RANKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_ranks(ranks):
    with open(RANKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ranks, f, ensure_ascii=False, indent=4)

user_ranks = load_ranks()

# --- ВЕБ-СЕРВЕР ---
async def handle(request):
    return web.Response(text="Westbound Bot is Alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# --- КНОПКИ ---
async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/rules", description="Устав"),
        BotCommand(command="/members", description="Список банды"),
        BotCommand(command="/warn", description="Выговор (Босс)"),
        BotCommand(command="/set_rank", description="Дать ранг (Босс)")
    ]
    await bot.set_my_commands(commands)

def get_keyboard():
    buttons = [
        [KeyboardButton(text="📜 Устав и Кодекс")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📊 Список банды")],
        [KeyboardButton(text="🚨 ТРЕВОГА")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- ЛОГИКА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Westbound приветствует тебя, {message.from_user.first_name}!", reply_markup=get_keyboard())

@dp.message(F.text == "📜 Устав и Кодекс")
async def show_rules(message: types.Message):
    text = "<b>🔴 УСТАВ:</b>\n1. Своих не бить.\n2. Босса слушать.\n3. Без читов!\n\n<b>⚖️ ДУЭЛИ:</b>\n- Спина к спине.\n- По взрыву ТНТ."
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("warn"))
async def give_warn(message: types.Message):
    if message.from_user.id != BOSS_ID: return
    if not message.reply_to_message: return
    uid = str(message.reply_to_message.from_user.id)
    if uid not in user_ranks: user_ranks[uid] = {"name": message.reply_to_message.from_user.first_name, "rank": "1", "warns": 0}
    user_ranks[uid]["warns"] += 1
    save_ranks(user_ranks)
    await message.answer(f"⚠️ {user_ranks[uid]['name']} получил выговор! ({user_ranks[uid]['warns']}/3)")

@dp.message(F.text == "📊 Список банды")
async def show_members(message: types.Message):
    if not user_ranks: return await message.answer("Банда пуста.")
    res = "<b>📊 СОСТАВ:</b>\n\n"
    for uid, data in user_ranks.items():
        res += f"• {data['name']} — [{data['rank']}] | ⚠️ {data['warns']}/3\n"
    await message.answer(res, parse_mode="HTML")

async def main():
    asyncio.create_task(start_webserver())
    await set_main_menu(bot)
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
