from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 8

DAYS = [
    ("Mn", "Dushanba"),
    ("Tu", "Seshanba"),
    ("Wed", "Chorshanba"),
    ("Thu", "Payshanba"),
    ("Fri", "Juma"),
    ("Sat", "Shanba"),
]

PERIOD_TIMES = {
    1: "8:00-9:20",
    2: "9:30-10:50",
    3: "11:00-12:20",
    4: "13:00-14:20",
    5: "14:30-15:50",
    6: "16:00-17:20",
    7: "17:30-18:50",
    8: "19:00-20:20",
}


def main_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🎓 Talabalar", callback_data="menu:guruh")
    b.button(text="👨‍🏫 O'qituvchilar", callback_data="menu:ustoz")
    b.button(text="🚪 Xonalar", callback_data="menu:xona")
    b.button(text="🟢 Bo'sh xonalarni topish", callback_data="menu:free")
    b.adjust(2, 2)
    return b.as_markup()


def nav_kb(names: list, page: int, can_go_back: bool, prefix: str = "nav") -> InlineKeyboardMarkup:
    """names: joriy darajadagi barcha nomlar ro'yxati (tartib bo'yicha).
    page: qaysi sahifa ko'rsatilmoqda.
    Callback data: "{prefix}:idx:<absolute_index>" | "{prefix}:page:prev" |
                    "{prefix}:page:next" | "{prefix}:back" | "{prefix}:home"
    """
    b = InlineKeyboardBuilder()
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    for i, name in enumerate(names[start:end], start=start):
        b.button(text=name, callback_data=f"{prefix}:idx:{i}")
    b.adjust(1)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{prefix}:page:prev"))
    if end < len(names):
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{prefix}:page:next"))
    if nav_row:
        b.row(*nav_row)

    bottom_row = []
    if can_go_back:
        bottom_row.append(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"{prefix}:back"))
    bottom_row.append(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data=f"{prefix}:home"))
    b.row(*bottom_row)

    return b.as_markup()


def after_result_kb(prefix: str = "nav") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Orqaga", callback_data=f"{prefix}:back")
    b.button(text="🏠 Bosh menyu", callback_data=f"{prefix}:home")
    b.adjust(2)
    return b.as_markup()


def days_kb(prefix: str = "free") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code, label in DAYS:
        b.button(text=label, callback_data=f"{prefix}:day:{code}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data=f"{prefix}:home"))
    return b.as_markup()


def periods_kb(prefix: str = "free") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for n, t in PERIOD_TIMES.items():
        b.button(text=f"{n}-para ({t})", callback_data=f"{prefix}:period:{n}")
    b.adjust(2)
    b.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data=f"{prefix}:home"))
    return b.as_markup()
