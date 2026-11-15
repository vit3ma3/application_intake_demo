"""Секреты и параметры окружения из .env."""

import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Переменная {name} не задана в .env")
    return value


BOT_TOKEN = _require("BOT_TOKEN")
# ID личного чата или группы (у групп ID отрицательный, например -1001234567890)
ADMIN_CHAT_ID = int(_require("ADMIN_CHAT_ID"))
DB_PATH = os.getenv("DB_PATH", "requests.db")
