from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_salon = State()
    choosing_service = State()
    choosing_master = State()
    choosing_time = State()
    confirming = State()
