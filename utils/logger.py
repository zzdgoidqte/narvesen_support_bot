import logging
import sys
from logging.handlers import RotatingFileHandler

# Silence unnecessary loggers
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('asyncpg').setLevel(logging.WARNING)

# Configure logger
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)

# Create formatters
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_formatter = logging.Formatter(
    '%(name)s - %(levelname)s - %(message)s'
)

# File handler (rotating logs)
file_handler = RotatingFileHandler(
    'bot.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)