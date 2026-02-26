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

# --- ПОДРОБНЫЕ ОПИСАНИЯ РАНГОВ ---
RANK_DETAILS = {
    "5": "<b>Ранг 5: Консильери (Советник)</b>\n\nТы — официальный представитель банды. Ведешь переговоры с лидерами других банд (строго с предупреждения Босса). Управляешь рангами 4, 3, 2, 1. Твоя обязанность — координировать общие действия.",
    "4": "<b>Ранг 4: Бригадир</b>\n\nТы управляешь рангами 3, 2 и 1. Твоя обязанность — выполнять указания Босса и Зама, контролировать выполнение правил и дисциплину в полевых условиях.",
    "3": "<b>Ранг 3: Управляющий</b>\n\nТы управляешь рангами 2 и 1. Обязан соблюдать все правила, выполнять указания старших и контролировать работу нижестоящих.",
    "2": "<b>Ранг 2: Образованный</b>\n\nТы управляешь рангом 1. Твоя обязанность — выполнять приказы рангов 3, 4 и 5. Должен знать устав и следить за действиями новичков.",
    "Страж": "<b>Ранг: Наблюдатель (Страж)</b>\n\nТвоё место — высоты (горы, крыши). Ты имеешь право первым подать сигнал тревоги. Твоя обязанность — охрана периметра и доклад о перемещениях врагов.",
    "1": "<b>Ранг 1: Новичок (Рекрут)</b>\n\nТвои возможности ограничены. Обязан соблюдать правила, выполнять черновую работу и любые приказы старших."
}

# --- ПАМЯТЬ (JSON) ---
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

# --- ВЕБ-СЕРВЕР ДЛЯ 24/7 (АНТИ-СОН) ---
async def handle(request):
    return web.Response(text="Westbound Bot is Alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# --- КЛАВИАТУРА И МЕНЮ ---
async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/my_rank", description="Мои обязанности"),
        BotCommand(command="/members", description="Список всей банды"),
        BotCommand(command="/alarm", description="🔴 ТРЕВОГА (Для Стражей)"),
        BotCommand(command="/set_rank", description="Дать ранг (Босс)")
    ]
    await bot.set_my_commands(commands)

def get_keyboard():
    buttons = [
        [KeyboardButton(text="📜 Иерархия и Устав")],
        [KeyboardButton(text="👤 Мой Ранг"), KeyboardButton(text="📊 Все игроки")],
        [KeyboardButton(text="💀 Зал Позора")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- ЛОГИКА КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Приветствую в Westbound, {message.from_user.first_name}!", reply_markup=get_keyboard())

@dp.message(Command("set_rank"))
async def set_rank(message: types.Message):
    if message.from_user.id != BOSS_ID:
        await message.reply("❌ Доступ только для Босса Абу!")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение бойца этой командой!")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Укажи ранг (1-5 или Страж).")
        return
    
    rank_val = " ".join(args[1:])
    target = message.reply_to_message.from_user
    user_ranks[str(target.id)] = {"name": target.first_name, "rank": rank_val}
    save_ranks(user_ranks)
    await message.answer(f"✅ <b>{target.first_name}</b> теперь <b>{rank_val}</b>", parse_mode="HTML")

@dp.message(F.text == "📊 Все игроки")
@dp.message(Command("members"))
async def show_members(message: types.Message):
    if not user_ranks:
        await message.answer("В банде пока нет бойцов.")
        return
    table = "<b>📊 СПИСОК WESTBOUND:</b>\n\n<code>Имя        | Ранг</code>\n<code>----------------------</code>\n"
    for uid, data in user_ranks.items():
        name = data.get('name', 'Боец')[:10]
        rank = data.get('rank', '???')
        table += f"<code>{name:<10} | {rank}</code>\n"
    table += "\n👑 <b>Босс: Абу</b>"
    await message.answer(table, parse_mode="HTML")

@dp.message(F.text == "👤 Мой Ранг")
@dp.message(Command("my_rank"))
async def my_rank(message: types.Message):
    uid = str(message.from_user.id)
    if message.from_user.id == BOSS_ID:
        await message.answer("👑 <b>Ты Босс Абу.</b>\nТвое слово — закон.", parse_mode="HTML")
    elif uid in user_ranks:
        r = user_ranks[uid].get('rank')
        desc = RANK_DETAILS.get(r, f"Твой ранг: {r}")
        await message.answer(desc, parse_mode="HTML")
    else:
        await message.answer("У тебя нет ранга. Слушайся Босса!")

@dp.message(Command("alarm"))
async def alarm(message: types.Message):
    uid = str(message.from_user.id)
    is_straj = uid in user_ranks and user_ranks[uid].get('rank') == "Страж"
    if message.from_user.id == BOSS_ID or is_straj:
        await message.answer("🚨 <b>ТРЕВОГА! ВСЕМ В СТРОЙ!</b> 🚨", parse_mode="HTML")

@dp.message(F.text == "📜 Иерархия и Устав")
async def hierarchy(message: types.Message):
    text = "<b>ИЕРАРХИЯ:</b>\n👑 Босс (Абу)\n5️⃣ Консильери\n4️⃣ Бригадир\n3️⃣ Управляющий\n2️⃣ Образованный\n👁 Страж\n1️⃣ Новичок"
    await message.answer(text, parse_mode="HTML")

# --- ЗАПУСК ---
async def main():
    asyncio.create_task(start_webserver()) # Для анти-сна
    await set_main_menu(bot)
    print("Westbound Bot запущен 24/7!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
