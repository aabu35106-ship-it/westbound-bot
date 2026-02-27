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
    "5": "<b>Ранг 5: Консильери (Советник)</b>\n\nТы — представитель банды. Ведешь переговоры. Управляешь рангами 4-1.",
    "4": "<b>Ранг 4: Бригадир</b>\n\nУправляешь рангами 3-1. Контролируешь дисциплину.",
    "3": "<b>Ранг 3: Управляющий</b>\n\nУправляешь рангами 2-1. Следишь за выполнением приказов.",
    "2": "<b>Ранг 2: Образованный</b>\n\nСледишь за новичками. Управляешь рангом 1.",
    "Страж": "<b>Ранг: Наблюдатель (Страж)</b>\n\nОхрана периметра и сигнал тревоги.",
    "1": "<b>Ранг 1: Новичок (Рекрут)</b>\n\nВыполняешь приказы старших и черновую работу."
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

# --- МЕНЮ ---
async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/rules", description="Устав и Кодекс"),
        BotCommand(command="/members", description="Список банды"),
        BotCommand(command="/warn", description="Дать выговор (Босс)"),
        BotCommand(command="/unwarn", description="Снять выговор (Босс)"),
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

# --- ЛОГИКА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Приветствую в Westbound, {message.from_user.first_name}!", reply_markup=get_keyboard())

@dp.message(F.text == "📜 Устав и Кодекс")
@dp.message(Command("rules"))
async def show_rules(message: types.Message):
    text = (
        "<b>🔴 УСТАВ:</b>\n1. Своих не бить.\n2. Босса слушать.\n3. Уважать банду.\n4. Дресс-код.\n5. Только русский.\n6. БЕЗ ЧИТОВ.\n\n"
        "<b>⚖️ ДУЭЛИ:</b>\n- Спина к спине.\n- Старт по взрыву ТНТ.\n- Только огнестрел.\n- Без укрытий."
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("set_rank"))
async def set_rank(message: types.Message):
    if message.from_user.id != BOSS_ID: return
    if not message.reply_to_message: return
    args = message.text.split()
    rank_val = " ".join(args[1:]) if len(args) > 1 else "1"
    target = message.reply_to_message.from_user
    uid = str(target.id)
    if uid not in user_ranks: user_ranks[uid] = {"name": target.first_name, "rank": rank_val, "warns": 0}
    else: user_ranks[uid]["rank"] = rank_val
    save_ranks(user_ranks)
    await message.answer(f"✅ {target.first_name} теперь <b>{rank_val}</b>", parse_mode="HTML")

Abu, [27.02.2026 14:53]
@dp.message(Command("warn"))
async def give_warn(message: types.Message):
    if message.from_user.id != BOSS_ID: return
    if not message.reply_to_message: return
    target = message.reply_to_message.from_user
    uid = str(target.id)
    if uid not in user_ranks: user_ranks[uid] = {"name": target.first_name, "rank": "1", "warns": 0}
    user_ranks[uid]["warns"] += 1
    w_count = user_ranks[uid]["warns"]
    save_ranks(user_ranks)
    msg = f"⚠️ <b>{target.first_name}</b> получил выговор! ({w_count}/3)"
    if w_count >= 3: msg += "\n❌ <b>ДОСТИГНУТ ЛИМИТ! ИСКЛЮЧИТЬ ИЗ БАНДЫ!</b>"
    await message.answer(msg, parse_mode="HTML")

@dp.message(Command("unwarn"))
async def remove_warn(message: types.Message):
    if message.from_user.id != BOSS_ID: return
    if not message.reply_to_message: return
    uid = str(message.reply_to_message.from_user.id)
    if uid in user_ranks and user_ranks[uid]["warns"] > 0:
        user_ranks[uid]["warns"] -= 1
        save_ranks(user_ranks)
        await message.answer(f"✅ Выговор снят. Текущий счет: {user_ranks[uid]['warns']}/3")

@dp.message(F.text == "📊 Список банды")
@dp.message(Command("members"))
async def show_members(message: types.Message):
    if not user_ranks:
        await message.answer("Банда пуста.")
        return
    res = "<b>📊 СОСТАВ WESTBOUND:</b>\n\n"
    for uid, data in user_ranks.items():
        res += f"• {data['name']} — [{data['rank']}] | ⚠️ Выговоры: {data['warns']}\n"
    await message.answer(res, parse_mode="HTML")

@dp.message(F.text == "👤 Мой Профиль")
async def my_profile(message: types.Message):
    uid = str(message.from_user.id)
    if uid in user_ranks:
        d = user_ranks[uid]
        await message.answer(f"👤 <b>Профиль:</b> {d['name']}\n🎖 <b>Ранг:</b> {d['rank']}\n⚠️ <b>Выговоры:</b> {d['warns']}/3", parse_mode="HTML")
    else: await message.answer("Тебя нет в базе. Обратись к Боссу!")

@dp.message(F.text == "🚨 ТРЕВОГА")
async def alarm(message: types.Message):
    uid = str(message.from_user.id)
    if message.from_user.id == BOSS_ID or (uid in user_ranks and user_ranks[uid]["rank"] == "Страж"):
        await message.answer("🚨 <b>ТРЕВОГА! ВСЕМ В СТРОЙ!</b> 🚨", parse_mode="HTML")

async def main():
    asyncio.create_task(start_webserver())
    await set_main_menu(bot)
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
