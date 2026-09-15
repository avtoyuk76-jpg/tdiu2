from aiogram.fsm.state import State, StatesGroup


class BrowseStates(StatesGroup):
    """Talabalar / O'qituvchilar / Xonalar bo'limlari uchun umumiy
    ko'rish holati. `feature` FSM data ichida saqlanadi: 'guruh' | 'ustoz' | 'xona'."""
    browsing = State()


class FreeRoomStates(StatesGroup):
    choosing_building = State()
    choosing_day = State()
    choosing_period = State()
