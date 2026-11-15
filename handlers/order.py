"""Пошаговое оформление заявки."""

import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import db
import keyboards
import settings
from services import notify
from states import OrderForm

log = logging.getLogger(__name__)

B = config.BUTTONS
T = config.TEXTS
PHONE_RE = re.compile(r"^\+?[\d\s()\-]{10,20}$")

router = Router()
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


@router.message(StateFilter(OrderForm), F.text == B["cancel"])
@router.message(StateFilter(OrderForm), Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(T["cancelled"], reply_markup=keyboards.main_menu())


@router.message(F.text == B["order"])
async def start_order(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OrderForm.work_type)
    # Reply-клавиатуру с «Отменить» и inline-выбор типа работ шлём разными сообщениями
    await message.answer(B["order"], reply_markup=keyboards.cancel())
    await message.answer(T["ask_work_type"], reply_markup=keyboards.work_types())


@router.callback_query(OrderForm.work_type, F.data.startswith("work:"))
async def work_type_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    work_type = config.WORK_TYPES[int(callback.data.split(":")[1])]
    await state.update_data(work_type=work_type)
    await state.set_state(OrderForm.description)
    await callback.message.edit_text(f"{T['ask_work_type']}\n<b>{work_type}</b>")
    await callback.message.answer(T["ask_description"], reply_markup=keyboards.cancel())
    await callback.answer()


@router.message(OrderForm.description, F.text, ~F.text.startswith("/"))
async def description_entered(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if len(text) < 5:
        await message.answer(T["description_too_short"])
        return
    if len(text) > config.DESCRIPTION_MAX_LEN:
        await message.answer(T["description_too_long"])
        return
    await state.update_data(description=text)
    await state.set_state(OrderForm.photo)
    await message.answer(T["ask_photo"], reply_markup=keyboards.skip_photo())


@router.message(OrderForm.photo, F.photo)
async def photo_sent(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await ask_phone(message, state)


@router.message(OrderForm.photo, F.text == B["skip"])
async def photo_skipped(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_file_id=None)
    await ask_phone(message, state)


@router.message(OrderForm.photo)
async def photo_expected(message: Message) -> None:
    await message.answer(T["photo_expected"])


async def ask_phone(message: Message, state: FSMContext) -> None:
    await state.set_state(OrderForm.phone)
    await message.answer(T["ask_phone"], reply_markup=keyboards.phone())


@router.message(OrderForm.phone, F.contact)
async def phone_contact(message: Message, state: FSMContext) -> None:
    await save_phone(message, state, message.contact.phone_number)


@router.message(OrderForm.phone, F.photo)
async def phone_extra_photo(message: Message) -> None:
    # Остальные фото из альбома — берём только первое
    pass


@router.message(OrderForm.phone, F.text)
async def phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not PHONE_RE.match(phone) or not 10 <= len(re.sub(r"\D", "", phone)) <= 15:
        await message.answer(T["phone_invalid"])
        return
    await save_phone(message, state, phone)


async def save_phone(message: Message, state: FSMContext, phone: str) -> None:
    await state.update_data(phone=phone)
    await state.set_state(OrderForm.call_time)
    await message.answer(T["ask_call_time"], reply_markup=keyboards.call_time())


@router.message(OrderForm.call_time, F.text, ~F.text.startswith("/"))
async def call_time_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(call_time=message.text.strip()[:100])
    await state.set_state(OrderForm.confirm)
    data = await state.get_data()
    await message.answer("👇", reply_markup=keyboards.cancel())
    await message.answer(
        T["confirm"].format(summary=notify.request_summary(data)),
        reply_markup=keyboards.confirm(),
    )


@router.callback_query(OrderForm.confirm, F.data == "order:cancel")
async def confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(T["cancelled"], reply_markup=keyboards.main_menu())
    await callback.answer()


@router.callback_query(OrderForm.confirm, F.data == "order:confirm")
async def confirm_send(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    user = callback.from_user
    request_id = await db.add_request(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        work_type=data["work_type"],
        description=data["description"],
        photo_file_id=data.get("photo_file_id"),
        phone=data["phone"],
        call_time=data["call_time"],
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(T["sent"].format(id=request_id), reply_markup=keyboards.main_menu())
    await callback.answer()

    try:
        await notify.send_admin_card(bot, settings.ADMIN_CHAT_ID, await db.get_request(request_id))
    except Exception:
        # Заявка уже сохранена — её видно в /export, даже если чат админа недоступен
        log.exception("Не удалось отправить заявку %s в чат админа", request_id)
