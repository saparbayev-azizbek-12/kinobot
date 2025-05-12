from environs import Env

env = Env()
env.read_env()

API_TOKEN = env.str("API_TOKEN")
print(env.str("ADMIN_ID"))
ADMIN_ID = env.list("ADMIN_ID")
MEDIA_CHANNEL_ID = env.int("MEDIA_CHANNEL_ID")
