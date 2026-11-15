"""Информационные разделы для клиента."""

from html import escape

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import keyboards

B = config.BUTTONS

router = Router()
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    name = escape(message.from_user.first_name or "")
    await message.answer(config.TEXTS["start"].format(name=name), reply_markup=keyboards.main_menu())


@router.message(F.text == B["services"])
async def services(message: Message) -> None:
    lines = [config.TEXTS["services_title"], ""]
    lines += [f"• {name} — <b>{price}</b>" for name, price in config.SERVICES]
    lines += ["", config.SERVICES_FOOTER]
    await message.answer("\n".join(lines))


@router.message(F.text == B["portfolio"])
async def portfolio(message: Message) -> None:
    parts = [config.TEXTS["portfolio_title"], *config.PORTFOLIO, config.PORTFOLIO_FOOTER]
    await message.answer("\n\n".join(parts))


@router.message(F.text == B["faq"])
async def faq(message: Message) -> None:
    await message.answer(config.TEXTS["faq_title"], reply_markup=keyboards.faq())


@router.callback_query(F.data.startswith("faq:"))
async def faq_answer(callback: CallbackQuery) -> None:
    question, answer = config.FAQ[int(callback.data.split(":")[1])]
    await callback.message.answer(f"<b>{question}</b>\n{answer}")
    await callback.answer()


@router.message(F.text == B["contacts"])
async def contacts(message: Message) -> None:
    await message.answer(config.CONTACTS)
