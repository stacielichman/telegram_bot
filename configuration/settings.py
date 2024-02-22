import os

import telebot
from dotenv import load_dotenv
from loguru import logger
import mysql
from mysql.connector import connect


logger.add(
    "../logs/log.log",
    rotation="1 day",
    level="INFO",
    format="{time}{level}{message}",
    backtrace=True,
    diagnose=True,
)

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
TOKEN = os.getenv('TOKEN')

HISTORY_DB = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        database=DB_NAME)
history_db = HISTORY_DB
cursor = history_db.cursor()

bot = telebot.TeleBot(TOKEN)
