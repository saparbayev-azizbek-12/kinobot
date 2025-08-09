import asyncio
import logging
from bot import dp, bot
from database import initialize_database
from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat
from config import ADMIN_ID
from bot_commands import user_commands, admin_commands

logging.basicConfig(level=logging.INFO)

async def on_startup():
    # Ma'lumotlar bazasini ishga tushiramiz
    initialize_database()

    # Foydalanuvchi buyruqlari
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Admin buyruqlari
    for admin in ADMIN_ID:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin))

async def main():
    await on_startup()
    # Botni polling orqali ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
