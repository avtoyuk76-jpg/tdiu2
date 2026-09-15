"""
/netcheck - serverdan tsue.edupage.org saytiga ulanish bor-yo'qligini
bosqichma-bosqich tekshiradi (DNS -> TCP -> brauzer orqali HTTP).
Skrinshot doim "timeout" xatosi berayotgan bo'lsa, shu buyruq orqali
muammo aniq qaysi bosqichda ekanini bilib olish mumkin.
"""

import asyncio
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .. import screenshot as ss

router = Router(name="debug")

HOST = "tsue.edupage.org"


@router.message(Command("netcheck"))
async def netcheck(message: Message):
    lines = [f"🔍 Tarmoq tekshiruvi: {HOST}\n"]
    status_msg = await message.answer("⏳ Tekshirilmoqda...")

    # 1) DNS
    t0 = time.monotonic()
    try:
        loop = asyncio.get_event_loop()
        infos = await asyncio.wait_for(loop.getaddrinfo(HOST, 443), timeout=10)
        ip = infos[0][4][0]
        lines.append(f"✅ DNS aniqlandi: {ip} ({time.monotonic() - t0:.2f}s)")
    except Exception as e:
        lines.append(f"❌ DNS xatosi: {e}")
        await status_msg.edit_text("\n".join(lines))
        return

    # 2) Xom TCP ulanish (443-port, HTTPS)
    t0 = time.monotonic()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(HOST, 443), timeout=10
        )
        writer.close()
        await writer.wait_closed()
        lines.append(f"✅ TCP ulanish (443-port): OK ({time.monotonic() - t0:.2f}s)")
    except Exception as e:
        lines.append(f"❌ TCP ulanish xatosi: {e}")
        lines.append(
            "\n➡️ Bu Railway serverining o'zi shu saytga chiqa olmayotganini "
            "bildiradi (masalan sayt Railway IP manzillarini bloklagan bo'lishi "
            "mumkin)."
        )
        await status_msg.edit_text("\n".join(lines))
        return

    # 3) Brauzer orqali (Playwright) ulanish
    t0 = time.monotonic()
    try:
        if ss._browser is None:
            await ss.start_browser()
        page = await ss._browser.new_page()
        try:
            await page.goto(
                f"https://{HOST}/timetable/", wait_until="commit", timeout=15000
            )
            lines.append(
                f"✅ Brauzer orqali ulanish: OK ({time.monotonic() - t0:.2f}s)"
            )
        finally:
            await page.close()
    except Exception as e:
        lines.append(f"❌ Brauzer orqali ulanish xatosi: {e}")
        lines.append(
            "\n➡️ TCP ulanish bor, lekin brauzer ulana olmayapti - bu "
            "Chromium sozlamalarida muammo bo'lishi mumkin."
        )
        await status_msg.edit_text("\n".join(lines))
        return

    lines.append("\n🎉 Hammasi joyida - ulanish muammosi yo'q.")
    await status_msg.edit_text("\n".join(lines))
