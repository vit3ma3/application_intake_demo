import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat

import db
import settings
from handlers import admin, client, order

log = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [BotCommand(command="start", description="Главное меню"),
         BotCommand(command="cancel", description="Отменить заявку")],
        scope=BotCommandScopeAllPrivateChats(),
    )
    try:
        await bot.set_my_commands(
            [BotCommand(command="stats", description="Статистика заявок"),
             BotCommand(command="export", description="Выгрузить заявки в CSV")],
            scope=BotCommandScopeChat(chat_id=settings.ADMIN_CHAT_ID),
        )
    except TelegramAPIError as e:
        log.warning("Не удалось задать команды для чата админа (бот добавлен в чат?): %s", e)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await db.init(settings.DB_PATH)

    bot = Bot(settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    # client первым: /start сбрасывает заявку на любом шаге
    dp.include_routers(admin.router, client.router, order.router)

    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
