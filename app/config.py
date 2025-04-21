from os import getenv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Configuration class for database credentials.
    Values are read from environment variables.
    
    Required .env variables:
    - DB_NAME: Database name
    - DB_READ_ONLY_USER: Read-only username
    - DB_READ_ONLY_USER_PASSWORD: Read-only user password
    - DB_HOST: Database host address
    - DB_PORT: Database port
    """
    DB_NAME = getenv('DB_NAME')
    DB_READ_ONLY_USER = getenv('DB_READ_ONLY_USER')
    DB_READ_ONLY_USER_PASSWORD = getenv('DB_READ_ONLY_USER_PASSWORD')
    DB_HOST = getenv('DB_HOST')
    DB_PORT = getenv('DB_PORT')
