# core/logger.py
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("slack_kudos_bot")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)