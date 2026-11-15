from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    work_type = State()
    description = State()
    photo = State()
    phone = State()
    call_time = State()
    confirm = State()
