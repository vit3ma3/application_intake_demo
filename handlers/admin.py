"""Обработка заявок в чате админа: смена статусов, /stats, /export."""

import csv
import io

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import config
import db
import keyboards
import settings
from services import notify

router = Router()
router.message.filter(F.chat.id == settings.ADMIN_CHAT_ID)
router.callback_query.filter(F.message.chat.id == settings.ADMIN_CHAT_ID)


@router.callback_query(F.data.startswith("status:"))
async def change_status(callback: CallbackQuery, bot: Bot) -> None:
    _, request_id, status = callback.data.split(":")
    request_id = int(request_id)
    admin = callback.from_user
    admin_name = f"@{admin.username}" if admin.username else admin.full_name

    if not await db.update_status(request_id, status, admin_name):
        await callback.answer("Статус этой заявки уже изменён", show_alert=True)
        request = await db.get_request(request_id)
    else:
        request = await db.get_request(request_id)
        await callback.answer(config.STATUSES[status])
        await notify.notify_client(bot, request)

    text = notify.admin_card(request)
    markup = keyboards.admin_actions(request_id, request["status"])
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=markup)
    else:
        await callback.message.edit_text(text, reply_markup=markup)


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    s = await db.get_stats()
    lines = [
        "<b>Статистика заявок</b>",
        f"За сегодня: <b>{s['today']}</b>",
        f"За 7 дней: <b>{s['week']}</b>",
        f"Всего: <b>{s['total']}</b>",
        "",
        "<b>По статусам:</b>",
    ]
    lines += [f"{label}: {s['by_status'].get(key, 0)}" for key, label in config.STATUSES.items()]
    await message.answer("\n".join(lines))


@router.message(Command("export"))
async def export(message: Message) -> None:
    requests = await db.get_all_requests()
    if not requests:
        await message.answer("Заявок пока нет.")
        return

    columns = [
        ("id", "№"), ("created_at", "Создана"), ("status", "Статус"),
        ("work_type", "Тип работ"), ("description", "Описание"), ("phone", "Телефон"),
        ("call_time", "Время для звонка"), ("full_name", "Имя"), ("username", "Username"),
        ("user_id", "Telegram ID"), ("processed_by", "Обработал"), ("updated_at", "Обновлена"),
    ]
    buffer = io.StringIO()
    # «;» — разделитель, который русскоязычный Excel понимает без мастера импорта
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(title for _, title in columns)
    for r in requests:
        r["status"] = config.STATUSES.get(r["status"], r["status"])
        writer.writerow(r[key] if r[key] is not None else "" for key, _ in columns)

    # BOM, чтобы Excel распознал UTF-8
    data = buffer.getvalue().encode("utf-8-sig")
    filename = f"requests_{message.date.strftime('%Y-%m-%d')}.csv"
    await message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=f"Всего заявок: {len(requests)}",
    )
