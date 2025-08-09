import asyncio
import logging

from aiohttp import web
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import API_TOKEN, ADMIN_ID, MEDIA_CHANNEL_ID, WEBHOOK_HOST, WEBHOOK_PATH, WEBHOOK_URL
from bot_commands import user_commands, admin_commands
from database import (
    initialize_database,
    add_user,
    get_all_users,
    add_sponsor,
    remove_sponsor,
    get_all_sponsors,
    add_video,
    get_video_message_id,
    check_subscriptions
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# States for FSM
class BroadcastState(StatesGroup):
    waiting_for_message = State()

class SponsorState(StatesGroup):
    adding = State()
    removing = State()

# Command handlers
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)

    if not await check_subscriptions(bot, user_id):
        sponsors = get_all_sponsors()
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

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    text = "ℹ️ **Mavjud buyruqlar:**\n\n"
    commands = admin_commands if message.from_user.id in ADMIN_ID else user_commands
    for cmd in commands:
        text += f"/{cmd.command} - {cmd.description}\n"
    await message.answer(text)

@dp.callback_query(F.data == "check_subs")
async def check_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscriptions(bot, user_id):
        await callback.answer("✅ Obuna tasdiqlandi!")
        await callback.message.answer("🎬 Endi raqam yuboring (masalan: 12), filmni jo'nataman.")
    else:
        await callback.answer("🚫 Obuna hali to'liq emas!", show_alert=True)

@dp.message(Command("stat"))
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        return

    users = get_all_users()
    total_users = len(users)

    text = f"📊 Foydalanuvchilar statistikasi:\n\n"
    text += f"👥 Umumiy foydalanuvchilar soni: <b>{total_users}</b>\n"

    # Agar siz foydalanuvchilar ro'yxatini ham ko'rsatmoqchi bo'lsangiz:
    # text += "\n🧾 Foydalanuvchilar ID ro'yxati:\n"
    # text += "\n".join(str(uid) for uid in users)

    await message.reply(text)

@dp.message(F.content_type == "video")
async def save_video(message: types.Message):
    if message.forward_from_chat and message.forward_from_message_id:
        if message.forward_from_chat.id == MEDIA_CHANNEL_ID:
            caption = message.caption or ""
            numbers = [word for word in caption.split() if word.isdigit()]
            if numbers:
                number = numbers[0]
                add_video(number, message.forward_from_message_id)
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
        sponsors = get_all_sponsors()
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

    video_code = message.text.strip()
    message_id = get_video_message_id(video_code)

    if not message_id:
        await message.reply("❌ Bu raqamga mos film topilmadi.")
        return

    try:
        post = await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=MEDIA_CHANNEL_ID,
            message_id=message_id
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
async def add_sponsor_command_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return

    args = message.text.split()
    if len(args) > 1:
        sponsor = args[1]
        add_sponsor(sponsor)
        await message.reply(f"✅ Homiy kanal ({sponsor}) qo'shildi.")
    else:
        await message.reply("➕ Qo'shiladigan homiy kanalning username'ini yuboring (masalan, @kanal_nomi):")
        await state.set_state(SponsorState.adding)

@dp.message(SponsorState.adding)
async def add_sponsor_state_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return
    
    sponsor = message.text
    add_sponsor(sponsor)
    await state.clear()
    await message.reply(f"✅ Homiy kanal ({sponsor}) qo'shildi.")


@dp.message(Command("homiy_olib_tashla"))
async def remove_sponsor_command_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return

    args = message.text.split()
    if len(args) > 1:
        sponsor = args[1]
        if remove_sponsor(sponsor):
            await message.reply(f"🗑 Homiy kanal ({sponsor}) o'chirildi.")
        else:
            await message.reply(f"❌ Bunday kanal ({sponsor}) topilmadi.")
    else:
        await message.reply("🗑 O'chiriladigan homiy kanalning username'ini yuboring (masalan, @kanal_nomi):")
        await state.set_state(SponsorState.removing)

@dp.message(SponsorState.removing)
async def remove_sponsor_state_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return
        
    sponsor = message.text
    if remove_sponsor(sponsor):
        await message.reply(f"🗑 Homiy kanal ({sponsor}) o'chirildi.")
    else:
        await message.reply(f"❌ Bunday kanal ({sponsor}) topilmadi.")
    await state.clear()

@dp.message(Command("homiylar"))
async def list_sponsors(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        return
    
    sponsors = get_all_sponsors()
    if sponsors:
        await message.reply("📋 Homiylar ro'yxati:\n" + "\n".join(sponsors))
    else:
        await message.reply("🚫 Hech qanday homiy kanal yo'q.")

@dp.message(Command("cancel"), StateFilter("*"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.reply("❌ Amal bekor qilindi.")

@dp.message(Command("xabar_yubor"))
async def broadcast_command_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return
    
    text = message.text.replace("/xabar_yubor", "").strip()
    if not text:
        await message.reply("✉️ Yuboriladigan xabar matnini kiriting:")
        await state.set_state(BroadcastState.waiting_for_message)
        return
    
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except:
            continue
    await message.reply(f"📬 {sent} ta foydalanuvchiga xabar yuborildi.")

@dp.message(BroadcastState.waiting_for_message)
async def broadcast_message_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return

    await state.clear()
    text = message.text
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except:
            continue
    await message.reply(f"📬 {sent} ta foydalanuvchiga xabar yuborildi.")
