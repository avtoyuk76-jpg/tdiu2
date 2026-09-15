"""
guruhlar.json / ustozlar.json / xonalar.json fayllari "flat" (tekis)
dict shaklida keladi, lekin ichida ketma-ket joylashgan sarlavha
kalitlari bor (masalan fakultet nomi, keyin "1KURS", keyin guruhlar).

Bu modul shu tekis faylni {sarlavha1: {sarlavha2: {nom: url}}} kabi
ierarxik daraxtga aylantiradi. Qaysi kalitlar "sarlavha" ekanini
aniqlash uchun regex naqshlari HIERARCHY_CONFIG_FILE (hierarchy_config.json)
faylida saqlanadi - bu adminka orqali ham sozlanishi mumkin, chunki
ustozlar.json / xonalar.json ning aniq formatini oldindan bilmaymiz.

boshxonalar.json esa butunlay boshqacha, tayyor tuzilgan format:
    {"10": {"room_id":10, "room_name":"1/126", "busy_slots":[...], "free_slots":[...]}, ...}
Bu yerda hech qanday tree qurishga hojat yo'q - to'g'ridan-to'g'ri
bino (room_name dagi "/" dan oldingi qism) va kun/davr bo'yicha
filtrlanadi.
"""

import json
import re
import threading
from pathlib import Path

from . import config

_lock = threading.Lock()

DEFAULT_HIERARCHY_CONFIG = {
    "guruhlar": {
        "levels": [
            {"pattern": r"^[A-Z]+$", "label": "fakultet"},
            {"pattern": r"^\dKURS$", "label": "kurs"},
        ]
    },
    "ustozlar": {
        "levels": [
            {"pattern": r"^[A-Z]+$", "label": "fakultet"},
        ]
    },
    "xonalar": {
        "levels": [
            {"pattern": r"^[A-Z0-9]+$", "label": "bino"},
        ]
    },
}

SKIP_KEYS = {"-", "", "—"}

DEFAULT_DISPLAY_NAMES = {
    "MENEJMENTFAKULTETI": "Menejment fakulteti",
    "IQTISODIYOT": "Iqtisodiyot fakulteti",
    "RAQAMLIIQT": "Raqamli iqtisodiyot fakulteti",
    "TURIZM": "Turizm fakulteti",
    "MOLIYA": "Moliya fakulteti",
    "BUXGALTERIYAFAKULTETI": "Buxgalteriya hisobi fakulteti",
    "SOLIQFAKULTETI": "Soliq fakulteti",
    "BANKISHI": "Bank ishi fakulteti",
    "POLOTSKIY": "Polotskiy filiali",
    "MASOFAVIYFAKULTETI": "Masofaviy ta'lim fakulteti",
}

_KURS_RE = re.compile(r"^(\d)KURS$")


def load_display_names() -> dict:
    if not config.DISPLAY_NAMES_FILE.exists():
        save_display_names(DEFAULT_DISPLAY_NAMES)
        return dict(DEFAULT_DISPLAY_NAMES)
    return _load_json(config.DISPLAY_NAMES_FILE)


def save_display_names(mapping: dict):
    with open(config.DISPLAY_NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def display_name_for(key: str, custom_map: dict | None = None) -> str:
    """Xom kalitni (masalan 'MENEJMENTFAKULTETI' yoki '1KURS') foydalanuvchiga
    chiroyli ko'rinishda ko'rsatish uchun aylantiradi.
    1) '1KURS' -> '1-kurs' kabi avtomatik format.
    2) Aks holda display_names.json dagi moslashtirilgan nomdan foydalaniladi.
    3) Agar mapping'da yo'q bo'lsa, xom kalitning o'zi qaytariladi."""
    m = _KURS_RE.match(key)
    if m:
        return f"{m.group(1)}-kurs"

    mapping = custom_map if custom_map is not None else load_display_names()
    return mapping.get(key, key)


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_hierarchy_config() -> dict:
    if not config.HIERARCHY_CONFIG_FILE.exists():
        save_hierarchy_config(DEFAULT_HIERARCHY_CONFIG)
        return DEFAULT_HIERARCHY_CONFIG
    return _load_json(config.HIERARCHY_CONFIG_FILE)


def save_hierarchy_config(cfg: dict):
    with open(config.HIERARCHY_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def build_tree(flat: dict, level_patterns: list) -> dict:
    """Tekis {kalit: url} dictni ierarxik daraxtga aylantiradi.

    level_patterns: [{"pattern": regex_str, ...}, ...] - tartib bo'yicha
    (masalan avval fakultet, keyin kurs).

    Natija tuzilishi (2 daraja bo'lsa):
        {
          "FAKULTET1": {
            "1KURS": {"GURUH-1/26": "https://...", ...},
            "2KURS": {...},
          },
          ...
        }
    Agar biror guruh hech qanday sarlavhadan oldin kelsa (fayl boshida),
    ular "__umumiy__" degan maxsus bo'limga tushadi.
    """
    compiled = [re.compile(lv["pattern"]) for lv in level_patterns]
    n_levels = len(compiled)

    root: dict = {}
    path_nodes = [None] * n_levels  # har bir daraja uchun joriy nom
    current_dict = root

    def get_or_create_path():
        node = root
        for i in range(n_levels):
            name = path_nodes[i] or "__umumiy__"
            node = node.setdefault(name, {})
        return node

    for key, value in flat.items():
        if key in SKIP_KEYS:
            continue

        matched_level = -1
        for i, pat in enumerate(compiled):
            if pat.match(key):
                matched_level = i
                break

        if matched_level != -1:
            path_nodes[matched_level] = key
            # pastroq darajalarni tozalaymiz (yangi bo'lim boshlandi)
            for j in range(matched_level + 1, n_levels):
                path_nodes[j] = None
            continue

        # oddiy element (leaf) - joriy yo'l ostiga qo'shamiz
        current_dict = get_or_create_path()
        current_dict[key] = value

    return root


class DataStore:
    """Barcha ma'lumotlarni xotirada ushlab turadi, reload() bilan
    qayta yuklash mumkin (adminka fayl yangilaganda chaqiriladi)."""

    def __init__(self):
        self.guruhlar_tree = {}
        self.ustozlar_tree = {}
        self.xonalar_tree = {}
        self.boshxonalar = {}
        self.reload()

    def reload(self):
        with _lock:
            hcfg = load_hierarchy_config()

            guruhlar_flat = _load_json(config.GURUHLAR_FILE)
            ustozlar_flat = _load_json(config.USTOZLAR_FILE)
            xonalar_flat = _load_json(config.XONALAR_FILE)
            self.boshxonalar = _load_json(config.BOSHXONALAR_FILE)

            self.guruhlar_tree = build_tree(
                guruhlar_flat, hcfg.get("guruhlar", DEFAULT_HIERARCHY_CONFIG["guruhlar"])["levels"]
            )
            self.ustozlar_tree = build_tree(
                ustozlar_flat, hcfg.get("ustozlar", DEFAULT_HIERARCHY_CONFIG["ustozlar"])["levels"]
            )
            self.xonalar_tree = build_tree(
                xonalar_flat, hcfg.get("xonalar", DEFAULT_HIERARCHY_CONFIG["xonalar"])["levels"]
            )

    # ---------- bo'sh xonalar uchun yordamchi funksiyalar ----------

    def buildings(self) -> list:
        """boshxonalar.json dagi room_name'lardan bino nomlarini chiqarib
        oladi (masalan '1/126' -> '1')."""
        names = set()
        for room in self.boshxonalar.values():
            rn = room.get("room_name", "")
            prefix = rn.split("/")[0].strip() if "/" in rn else rn.strip()
            if prefix:
                names.add(prefix)
        return sorted(names, key=lambda s: (len(s), s))

    def free_rooms(self, building: str, day: str, period: int) -> list:
        """Berilgan bino + kun + davr uchun bo'sh xonalar ro'yxatini
        qaytaradi: [{"room_name": ..., "url": ...}, ...]"""
        result = []
        for room in self.boshxonalar.values():
            rn = room.get("room_name", "")
            prefix = rn.split("/")[0].strip() if "/" in rn else rn.strip()
            if prefix != building:
                continue
            free_slots = room.get("free_slots", [])
            is_free = any(
                s.get("day") == day and s.get("period") == period for s in free_slots
            )
            if is_free:
                result.append({"room_name": rn, "url": room.get("url", "")})
        result.sort(key=lambda r: r["room_name"])
        return result


store = DataStore()
