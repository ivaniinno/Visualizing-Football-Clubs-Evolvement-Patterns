import psycopg2
from config import Config

conn = psycopg2.connect(
    database=Config.DB_NAME,
    user=Config.DB_READ_ONLY_USER,
    password=Config.DB_READ_ONLY_USER_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT
)

cur = conn.cursor()
