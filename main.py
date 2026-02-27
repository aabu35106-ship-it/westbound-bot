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

# --- ФУНКЦИИ ПАМЯТИ ---
def load_ranks():
    if os.path.exists(RANKS_FILE):
        try:
            with open(RANKS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                return json.loads(content) if content else {}
        except: return {}
    return {}

def save_ranks(ranks):
    with open(RANKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ranks, f, ensure_ascii=False, indent=4)

user_ranks = load_ranks()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Westbound Bot is Alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# --- МЕНЮ КОМАНД ---
async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/rules", description="Устав и Кодекс"),
        BotCommand(command="/members", description="Список банды"),
        BotCommand(command="/warn", description="Дать выговор (Босс)"),
        BotCommand(command="/set_rank", description="Дать ранг (Босс)")
    ]
    await bot.set_my_commands(commands)

def get_keyboard():
    buttons = [
        [KeyboardButton(text="📜 Устав и Кодекс")],
        [KeyboardButton(text="👤 Мой Профиль"), KeyboardButton(text="📊 Список банды")],
        [KeyboardButton(text="🚨 ТРЕВОГА")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- ЛОГИКА БОТА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Приветствую в Westbound, {message.from_user.first_name}!", reply_markup=get_keyboard())

@dp.message(F.text == "📜 Устав и Кодекс")
async def show_rules(message: types.Message):
    text = (
        "<b>🔴 УСТАВ WESTBOUND:</b>\n1. Своих не бить.\n2. Босса слушать.\n3. Уважать банду.\n4. Без читов.\n\n"
        "<b>⚖️ ДУЭЛИ:</b>\n- Спина к спине.\n- Старт по взрыву ТНТ.\n- Только огнестрел."
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("warn"))
async def give_warn(message: types.Message):
    if message.from_user.id != BOSS_ID: return
    if not message.reply_to_message: return
    target = message.reply_to_message.from_user
    uid = str(target.id)
    if uid not in user_ranks: user_ranks[uid] = {"name": target.first_name, "rank": "1", "warns": 0}
    user_ranks[uid]["warns"] += 1
    save_ranks(user_ranks)
    await message.answer(f"⚠️ <b>{target.first_name}</b> получил выговор! ({user_ranks[uid]['warns']}/3)", parse_mode="HTML")

@dp.message(F.text == "📊 Список банды")
async def show_members(message: types.Message):
    if not user_ranks:
        await message.answer("Банда пуста.")
        return
    res = "<b>📊 СОСТАВ WESTBOUND:</b>\n\n"
    for uid, data in user_ranks.items():
        res += f"• {data['name']} — [{data['rank']}] | ⚠️ Выговоры: {data['warns']}\n"
    await message.answer(res, parse_mode="HTML")

@dp.message(F.text == "🚨 ТРЕВОГА")
async def alarm(message: types.Message):
    if message.from_user.id == BOSS_ID:
        await message.answer("🚨 <b>ТРЕВОГА! ВСЕМ В СТРОЙ!</b> 🚨", parse_mode="HTML")

# === ЗАПУСК ===
async def main():
    asyncio.create_task(start_webserver())
    await set_main_menu(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
