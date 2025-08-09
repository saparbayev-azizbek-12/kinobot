from aiogram.types import BotCommand

# Commands for regular users
user_commands = [
    BotCommand(command="start", description="🚀 Botni ishga tushirish"),
    BotCommand(command="help", description="ℹ️ Yordam menyusini ko'rsatish"),
]

# Commands for administrators
admin_commands = [
    BotCommand(command="start", description="🚀 Botni ishga tushirish"),
    BotCommand(command="help", description="ℹ️ Yordam menyusini ko'rsatish"),
    BotCommand(command="stat", description="📊 Foydalanuvchilar statistikasi"),
    BotCommand(command="homiy_qosh", description="➕ Homiy kanal qo'shish"),
    BotCommand(command="homiy_olib_tashla", description="🗑 Homiy kanalni o'chirish"),
    BotCommand(command="homiylar", description="📋 Homiylar ro'yxati"),
    BotCommand(command="xabar_yubor", description="✉️ Barcha foydalanuvchilarga xabar yuborish"),
    BotCommand(command="cancel", description="❌ Joriy amalni bekor qilish")
]
