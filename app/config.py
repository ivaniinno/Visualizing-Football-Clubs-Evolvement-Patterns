import os
from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_NAME = getenv('DB_NAME')
    DB_READ_ONLY_USER = getenv('DB_READ_ONLY_USER')
    DB_READ_ONLY_USER_PASSWORD = getenv('DB_READ_ONLY_USER_PASSWORD')
    DB_HOST = getenv('DB_HOST')
    DB_PORT = getenv('DB_PORT')
