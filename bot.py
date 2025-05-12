import asyncio
import json
import logging
import os
from typing import List

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import API_TOKEN, ADMIN_ID, MEDIA_CHANNEL_ID
from utils import load_sponsors, load_users, save_user, check_subscriptions, save_sponsors

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Constants
DATA_FILE = "videos.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data() -> dict:
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Command handlers
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    save_user(user_id)

    if not await check_subscriptions(bot, user_id):
        sponsors = load_sponsors()
        builder = InlineKeyboardBuilder()

        for ch in sponsors:
            username = ch.strip('@')
            builder.add(InlineKeyboardButton(
                text=f"➕ {username}",
                url=f"https://t.me/{username}"
            ))

        builder.add(InlineKeyboardButton(
            text="✅ Obuna bo'ldim",
            callback_data="check_subs"
        ))
        builder.adjust(1)

        await message.answer(
            "📛 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=builder.as_markup()
        )
        return

    await message.answer("🎬 Qaysi film kerak? Raqam yuboring (masalan: 12)")

@dp.callback_query(F.data == "check_subs")
async def check_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscriptions(bot, user_id):
        await callback.answer("✅ Obuna tasdiqlandi!")
        await callback.message.answer("🎬 Endi raqam yuboring (masalan: 12), filmni jo'nataman.")
    else:
        await callback.answer("🚫 Obuna hali to'liq emas!", show_alert=True)


@dp.message(F.content_type == "video")
async def save_video(message: types.Message):
    print(message)
    print(message.forward_from_chat)
    print(message.forward_from_message_id)
    if message.forward_from_chat and message.forward_from_message_id:
        print("Chat ID:", message.forward_from_chat.id)
        print("Caption:", message.caption)
        if message.forward_from_chat.id == MEDIA_CHANNEL_ID:
            caption = message.caption or ""
            numbers = [word for word in caption.split() if word.isdigit()]
            if numbers:
                number = numbers[0]
                data = load_data()
                data[number] = message.forward_from_message_id
                save_data(data)
                await message.reply(f"✅ {number}-raqamli video saqlandi.")
            else:
                await message.reply("⚠️ Izohda raqam topilmadi.")
        else:
            await message.reply("⚠️ Videoni noto'g'ri kanaldan forward qildingiz.")
    elif message.forward_from_chat:
        await message.reply(f"📢 Kanal ID: `{message.forward_from_chat.id}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("⚠️ Videoni forward qiling. Yuklab emas!")

@dp.message(lambda msg: msg.text.isdigit())
async def send_video(message: types.Message):
    user_id = message.from_user.id

    if not await check_subscriptions(bot, user_id):
        sponsors = load_sponsors()
        builder = InlineKeyboardBuilder()

        for ch in sponsors:
            username = ch.strip('@')
            builder.add(InlineKeyboardButton(
                text=f"➕ {username}",
                url=f"https://t.me/{username}"
            ))

        builder.add(InlineKeyboardButton(
            text="✅ Obuna bo'ldim",
            callback_data="check_subs"
        ))
        builder.adjust(1)

        await message.answer(
            "📛 Filmni olishdan oldin quyidagi kanallarga obuna bo'ling:",
            reply_markup=builder.as_markup()
        )
        return

    msg_id = message.text.strip()
    data = load_data()

    if msg_id not in data:
        await message.reply("❌ Bu raqamga mos film topilmadi.")
        return

    try:
        post = await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=MEDIA_CHANNEL_ID,
            message_id=data[msg_id]
        )
        await bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=post.message_id,
            caption="🎬 Filmni bot orqali oldingiz: @Top_kinouz_bot"
        )
    except Exception as e:
        await message.reply("❌ Video yuborishda xatolik yuz berdi.")

# Admin commands
@dp.message(Command("homiy_qosh"))
async def add_sponsor(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.split()
    if len(text) < 2:
        await message.reply("❗ Foydalanish: /homiy_qosh @kanal_username")
        return
    
    sponsor = text[1]
    sponsors = load_sponsors()
    if sponsor not in sponsors:
        sponsors.append(sponsor)
        save_sponsors(sponsors)
        await message.reply("✅ Homiy kanal qo'shildi.")
    else:
        await message.reply("🔁 Bu kanal ro'yxatda bor.")

@dp.message(Command("homiy_olib_tashla"))
async def remove_sponsor(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.split()
    if len(text) < 2:
        await message.reply("❗ Foydalanish: /homiy_olib_tashla @kanal_username")
        return
    
    sponsor = text[1]
    sponsors = load_sponsors()
    if sponsor in sponsors:
        sponsors.remove(sponsor)
        save_sponsors(sponsors)
        await message.reply("🗑 Homiy kanal o'chirildi.")
    else:
        await message.reply("❌ Bunday kanal topilmadi.")

@dp.message(Command("homiylar"))
async def list_sponsors(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        return
    
    sponsors = load_sponsors()
    if sponsors:
        await message.reply("📋 Homiylar ro'yxati:\n" + "\n".join(sponsors))
    else:
        await message.reply("🚫 Hech qanday homiy kanal yo'q.")

@dp.message(Command("xabar_yubor"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace("/xabar_yubor", "").strip()
    if not text:
        await message.reply("✉️ Xabar yuborish uchun matn kiriting:\n/xabar_yubor Salom!")
        return
    
    users = load_users()
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except:
            continue
    await message.reply(f"📬 {sent} ta foydalanuvchiga xabar yuborildi.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
