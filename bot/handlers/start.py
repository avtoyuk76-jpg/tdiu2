from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import main_menu_kb

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "TSUE dars jadvali botiga xush kelibsiz.\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(lambda c: c.data == "nav:home" or c.data == "free:home")
async def go_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Bosh menyu. Quyidagilardan birini tanlang:",
        reply_markup=main_menu_kb(),
    )
    await call.answer()
