import os
from _envs import *

USERS_TXT = './users.txt'
# DATABASE_PATH = './data.sqlite3'
# For hosting on Heroku
DATABASE_PATH = os.environ.get('DATABASE_URL')
DATE_FORMAT = '%d/%m/%Y'
TIME_FORMAT = '%H:%M:%S'
BOT_NAME = 'InventreeBot'
PORT = int(os.environ.get('PORT', 5000))
TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
STATE_ADD_ITEMS, = range(1)
WEBAPP = WEBAPP