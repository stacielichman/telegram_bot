import mysql
from mysql.connector import connect

HISTORY_DB = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="01579639909075zZ!",
        database="history_base")
