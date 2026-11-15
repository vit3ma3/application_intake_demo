from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

import config

B = config.BUTTONS


def _reply(rows: list[list[KeyboardButton]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def main_menu() -> ReplyKeyboardMarkup:
    return _reply([
        [KeyboardButton(text=B["services"]), KeyboardButton(text=B["portfolio"])],
        [KeyboardButton(text=B["faq"]), KeyboardButton(text=B["contacts"])],
        [KeyboardButton(text=B["order"])],
    ])


def cancel() -> ReplyKeyboardMarkup:
    return _reply([[KeyboardButton(text=B["cancel"])]])


def skip_photo() -> ReplyKeyboardMarkup:
    return _reply([[KeyboardButton(text=B["skip"])], [KeyboardButton(text=B["cancel"])]])


def phone() -> ReplyKeyboardMarkup:
    return _reply([
        [KeyboardButton(text=B["send_phone"], request_contact=True)],
        [KeyboardButton(text=B["cancel"])],
    ])


def call_time() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=t)] for t in config.CALL_TIMES]
    rows.append([KeyboardButton(text=B["cancel"])])
    return _reply(rows)


def work_types() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"work:{i}")]
        for i, name in enumerate(config.WORK_TYPES)
    ])


def confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=B["confirm"], callback_data="order:confirm"),
        InlineKeyboardButton(text=B["confirm_cancel"], callback_data="order:cancel"),
    ]])


def faq() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=question, callback_data=f"faq:{i}")]
        for i, (question, _) in enumerate(config.FAQ)
    ])


def admin_actions(request_id: int, status: str) -> InlineKeyboardMarkup | None:
    """Кнопки под карточкой заявки; для финальных статусов — без кнопок."""
    available = {
        "new": ("in_progress", "closed", "rejected"),
        "in_progress": ("closed", "rejected"),
    }.get(status, ())
    if not available:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=config.ADMIN_ACTIONS[s], callback_data=f"status:{request_id}:{s}")
        for s in available
    ]])
