"""
Talabalar, O'qituvchilar va Xonalar bo'limlari bir xil mantiqqa ega:
daraxt bo'ylab (fakultet -> kurs -> guruh, yoki bino -> xona) yurish va
oxirida URL manzilidan skrinshot olib yuborish. Shu sabab bitta umumiy
handler orqali barchasi boshqariladi ("feature" FSM data'da saqlanadi).
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from .. import data_loader
from ..keyboards import after_result_kb, nav_kb
from ..screenshot import take_timetable_screenshot
from ..states import BrowseStates

router = Router(name="browser")
logger = logging.getLogger(__name__)

FEATURE_TREES = {
    "guruh": lambda: data_loader.store.guruhlar_tree,
    "ustoz": lambda: data_loader.store.ustozlar_tree,
    "xona": lambda: data_loader.store.xonalar_tree,
}

FEATURE_TITLES = {
    "guruh": "🎓 Talabalar",
    "ustoz": "👨‍🏫 O'qituvchilar",
    "xona": "🚪 Xonalar",
}


def get_node(tree: dict, path: list):
    node = tree
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return {}
        node = node[key]
    return node


def path_title(feature: str, path: list) -> str:
    title = FEATURE_TITLES.get(feature, "")
    if path:
        pretty_path = [data_loader.display_name_for(p) for p in path]
        title += " › " + " › ".join(pretty_path)
    return title


async def render_level(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    feature = data["feature"]
    path = data.get("path", [])
    page = data.get("page", 0)

    tree = FEATURE_TREES[feature]()
    node = get_node(tree, path)
    keys = sorted(node.keys())
    display_names_map = data_loader.load_display_names()
    display_list = [data_loader.display_name_for(k, display_names_map) for k in keys]

    text = path_title(feature, path) + "\n\nQuyidagilardan birini tanlang:"
    kb = nav_kb(display_list, page, can_go_back=bool(path), prefix="nav")

    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.in_(["menu:guruh", "menu:ustoz", "menu:xona"]))
async def open_feature(call: CallbackQuery, state: FSMContext):
    feature = call.data.split(":")[1]
    await state.set_state(BrowseStates.browsing)
    await state.update_data(feature=feature, path=[], page=0)
    await render_level(call, state)
    await call.answer()


@router.callback_query(BrowseStates.browsing, F.data.startswith("nav:idx:"))
async def choose_item(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    feature = data["feature"]
    path = data.get("path", [])

    tree = FEATURE_TREES[feature]()
    node = get_node(tree, path)
    names = sorted(node.keys())

    idx = int(call.data.split(":")[2])
    if idx < 0 or idx >= len(names):
        await call.answer("Noto'g'ri tanlov, qayta urinib ko'ring.", show_alert=True)
        return

    chosen_name = names[idx]
    chosen_value = node[chosen_name]

    if isinstance(chosen_value, dict):
        # yana ichkariga kiramiz (masalan fakultet -> kurs)
        new_path = path + [chosen_name]
        await state.update_data(path=new_path, page=0)
        await render_level(call, state)
        await call.answer()
        return

    # chosen_value - bu URL (leaf element). Skrinshot olib yuboramiz.
    await call.answer("⏳ Jadval yuklanmoqda, biroz kuting...")
    loading_msg = await call.message.edit_text(f"⏳ {chosen_name} jadvali yuklanmoqda...")

    try:
        png_path = await take_timetable_screenshot(chosen_value)
        photo = FSInputFile(png_path)
        await call.message.answer_photo(
            photo,
            caption=f"📅 {chosen_name}",
            reply_markup=after_result_kb(prefix="nav"),
        )
        png_path.unlink(missing_ok=True)
        try:
            await loading_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.exception("Skrinshot olishda xatolik: %s", chosen_value)
        await call.message.answer(
            f"❌ Jadvalni yuklab bo'lmadi. Xatolik: {e}\n\n"
            f"Havola: {chosen_value}",
            reply_markup=after_result_kb(prefix="nav"),
        )


@router.callback_query(BrowseStates.browsing, F.data == "nav:page:prev")
async def page_prev(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(page=max(0, data.get("page", 0) - 1))
    await render_level(call, state)
    await call.answer()


@router.callback_query(BrowseStates.browsing, F.data == "nav:page:next")
async def page_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(page=data.get("page", 0) + 1)
    await render_level(call, state)
    await call.answer()


@router.callback_query(BrowseStates.browsing, F.data == "nav:back")
async def go_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    path = data.get("path", [])
    if path:
        path = path[:-1]
    await state.update_data(path=path, page=0)
    await render_level(call, state)
    await call.answer()
