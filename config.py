from environs import Env

env = Env()
env.read_env()

# Bot settings
API_TOKEN = env.str("API_TOKEN")
ADMIN_ID = env.list("ADMIN_ID", subcast=int)
MEDIA_CHANNEL_ID = env.int("MEDIA_CHANNEL_ID")

# Webhook settings
WEBHOOK_HOST = 'https://kinobot.pythonanywhere.com'
WEBHOOK_PATH = f'/{API_TOKEN}'
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH
