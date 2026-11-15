"""Карточка заявки для админа и уведомления клиенту."""

import logging
from html import escape

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

import config
import keyboards

log = logging.getLogger(__name__)

# Лимит подписи к фото в Telegram — 1024 символа, поэтому описание в карточке с фото режем
CAPTION_DESCRIPTION_LIMIT = 500


def request_summary(data: dict, description_limit: int | None = None) -> str:
    """Поля заявки, общие для подтверждения клиенту и карточки админу."""
    description = data["description"]
    if description_limit and len(description) > description_limit:
        description = description[:description_limit] + "…"
    lines = [
        f"<b>Тип работ:</b> {escape(data['work_type'])}",
        f"<b>Описание:</b> {escape(description)}",
        f"<b>Фото:</b> {'есть' if data.get('photo_file_id') else 'нет'}",
        f"<b>Телефон:</b> {escape(data['phone'])}",
        f"<b>Время для звонка:</b> {escape(data['call_time'])}",
    ]
    return "\n".join(lines)


def admin_card(request: dict) -> str:
    limit = CAPTION_DESCRIPTION_LIMIT if request["photo_file_id"] else None
    client = f'<a href="tg://user?id={request["user_id"]}">{escape(request["full_name"] or "Клиент")}</a>'
    if request["username"]:
        client += f" (@{escape(request['username'])})"
    lines = [
        f"<b>Заявка №{request['id']}</b> — {config.STATUSES[request['status']]}",
        "",
        request_summary(request, limit),
        f"<b>Клиент:</b> {client}",
        f"<b>Создана:</b> {request['created_at']}",
    ]
    if request["processed_by"]:
        lines.append(f"<b>Обработал:</b> {escape(request['processed_by'])}")
    return "\n".join(lines)


async def send_admin_card(bot: Bot, chat_id: int, request: dict) -> None:
    markup = keyboards.admin_actions(request["id"], request["status"])
    text = admin_card(request)
    if request["photo_file_id"]:
        await bot.send_photo(chat_id, request["photo_file_id"], caption=text, reply_markup=markup)
    else:
        await bot.send_message(chat_id, text, reply_markup=markup)


async def notify_client(bot: Bot, request: dict) -> None:
    text = config.STATUS_NOTIFY.get(request["status"])
    if not text:
        return
    try:
        await bot.send_message(request["user_id"], text.format(id=request["id"]))
    except TelegramAPIError as e:
        # Клиент мог заблокировать бота — это не повод ронять обработку
        log.warning("Не удалось уведомить клиента по заявке %s: %s", request["id"], e)
