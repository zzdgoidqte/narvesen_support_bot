import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))  
    DB_USER = os.getenv("DB_USER", "user")
    DB_PASS = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "mydb")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))  
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))  

    SUPPORT_ADMIN_USERNAME = 'guncha420' # @guncha420 for testing

    NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")

    IPROYAL_PROXY_AUTH = os.getenv("IPROYAL_PROXY_AUTH")

    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE") == "true"