# TSUE Dars Jadvali Telegram Bot

TSUE (tsue.edupage.org) dars jadvalini Telegram orqali ko'rsatuvchi bot.
Talabalar, o'qituvchilar va xonalar bo'yicha jadval skrinshotini
yuboradi, shuningdek berilgan bino/kun/para bo'yicha **bo'sh xonalarni**
topib beradi.

## Tarkibi

```
tsue_bot/
├── bot/                    # Telegram bot (aiogram 3)
│   ├── config.py           # sozlamalar (.env dan o'qiladi)
│   ├── data_loader.py      # JSON fayllarni ierarxik daraxtga aylantiradi
│   ├── screenshot.py       # Playwright orqali jadval skrinshotini oladi
│   ├── keyboards.py        # inline tugmalar
│   ├── states.py           # FSM holatlari
│   ├── main.py             # botning kirish nuqtasi
│   └── handlers/
│       ├── start.py        # /start, bosh menyu
│       ├── browser.py      # Talabalar/O'qituvchilar/Xonalar navigatsiyasi
│       └── free_rooms.py   # Bo'sh xonalarni topish oqimi
├── admin/                  # Web-admin panel (FastAPI)
│   ├── app.py
│   └── templates/
├── data/                   # JSON ma'lumot fayllari (shu yerda saqlanadi)
│   ├── guruhlar.json
│   ├── ustozlar.json
│   ├── xonalar.json
│   ├── boshxonalar.json
│   └── hierarchy_config.json   # avtomatik yaratiladi
├── run.py                  # bot + admin panelni birga ishga tushiradi
├── Dockerfile
├── requirements.txt
└── railway.json
```

## Ma'lumot fayllari haqida

### guruhlar.json / ustozlar.json / xonalar.json

Bu fayllar **"tekis" (flat) dict** ko'rinishida bo'lishi kerak, lekin
ichida ketma-ket joylashgan sarlavha kalitlari bor:

```json
{
  "MENEJMENTFAKULTETI": "https://tsue.edupage.org/timetable/view.php?num=94&class=*1800",
  "1KURS": "https://tsue.edupage.org/timetable/view.php?num=94&class=*1389",
  "MO-900/26": "https://tsue.edupage.org/timetable/view.php?num=94&class=*3",
  "MO-901/26": "https://tsue.edupage.org/timetable/view.php?num=94&class=*4",
  "2KURS": "...",
  "...": "..."
}
```

Bot bu faylni avtomatik ravishda **{fakultet: {kurs: {guruh: url}}}**
ko'rinishidagi daraxtga aylantiradi. Qaysi kalitlar "sarlavha"
(fakultet/kurs/bino) ekanini aniqlash uchun **regex naqshlari**
ishlatiladi - ular `data/hierarchy_config.json` faylida (yoki admin
panelning "Ierarxiya sozlamalari" bo'limida) saqlanadi:

```json
{
  "guruhlar": {
    "levels": [
      {"pattern": "^[A-Z]+$", "label": "fakultet"},
      {"pattern": "^\\dKURS$", "label": "kurs"}
    ]
  },
  "ustozlar": {
    "levels": [
      {"pattern": "^[A-Z]+$", "label": "fakultet"}
    ]
  },
  "xonalar": {
    "levels": [
      {"pattern": "^[A-Z0-9]+$", "label": "bino"}
    ]
  }
}
```

**MUHIM:** `ustozlar.json` va `xonalar.json` ning aniq formatini hali
ko'rmaganim uchun, ularning "sarlavha" pattern'lari `guruhlar.json`
asosida **taxminiy** qilib qo'yilgan. Fayllarni yuklab bo'lgach:

1. Admin panelda **Ierarxiya sozlamalari** bo'limiga kiring.
2. Botda **O'qituvchilar** yoki **Xonalar** tugmasini bosib ko'ring.
3. Agar sarlavha (masalan bino nomi) guruh/o'qituvchi sifatida chiqib
   qolsa yoki aksincha - pattern'ni shunga qarab to'g'irlang va
   saqlang (kod o'zgartirishga hojat yo'q, avtomatik qayta yuklanadi).

### boshxonalar.json ("bo'sh xonalar")

Bu fayl **oldindan tayyorlangan** (scraper orqali yig'ilgan) va quyidagi
formatda bo'lishi kerak:

```json
{
  "10": {
    "room_id": 10,
    "room_name": "1/126",
    "url": "https://tsue.edupage.org/timetable/view.php?num=94&classroom=*10",
    "busy_slots": [{"day": "Mn", "period": 3, "time": "11:00-12:20", "info": "..."}],
    "free_slots": [{"day": "Mn", "period": 1, "time": "8:00-9:20"}]
  },
  "11": { "...": "..." }
}
```

Bino nomi `room_name` dagi `/` belgisidan oldingi qismdan olinadi
(masalan `"1/126"` -> bino **"1"**). Botda foydalanuvchi bino, kun va
parani tanlaganda, bot shu binoga tegishli barcha xonalar orasidan
`free_slots` ichida mos (kun, para) yozuvi bor xonalarni ro'yxat
qilib chiqaradi.

Bu faylni yangilash uchun avval yozgan `room_schedule_scraper_svg.py`
skriptini qayta ishga tushirib, natijani (`rooms_schedule.json`) admin
panel orqali `boshxonalar.json` sifatida yuklashingiz mumkin.

## Lokal ishga tushirish (test uchun)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# .env faylini oching va BOT_TOKEN, ADMIN_PASSWORD qiymatlarini kiriting

# data/ papkasiga guruhlar.json, ustozlar.json, xonalar.json,
# boshxonalar.json fayllaringizni joylashtiring

python run.py
```

Bot ishga tushadi (polling), admin panel esa http://localhost:8000
manzilida ochiladi (login: .env dagi ADMIN_USERNAME/ADMIN_PASSWORD).

## Railway'ga deploy qilish

1. Loyihani GitHub'ga yuklang (yangi repository yarating, shu papkani
   push qiling).
2. [railway.app](https://railway.app) da **New Project -> Deploy from
   GitHub repo** ni tanlang, shu repo'ni tanlang.
3. Railway `Dockerfile`ni avtomatik topib, shu asosida build qiladi.
4. **Variables** bo'limiga quyidagilarni qo'shing:
   - `BOT_TOKEN` - @BotFather dan olingan token
   - `ADMIN_USERNAME` - admin panel login
   - `ADMIN_PASSWORD` - admin panel paroli (kuchli parol tanlang!)
5. **Settings -> Networking** bo'limida **Generate Domain** tugmasini
   bosing - shu orqali admin panelga ochiladigan havola olasiz
   (masalan `https://sizning-loyiha.up.railway.app`).
6. Deploy tugagach, botga Telegram'da `/start` yuboring - ishlashi
   kerak.
7. `data/` papkasidagi JSON fayllarni admin panel orqali (havola oxiriga
   `/file/guruhlar` va h.k. qo'shib, yoki bosh sahifadan) yuklang.

**Eslatma - fayllar saqlanishi haqida:** Railway'ning standart
(ephemeral) fayl tizimida konteyner qayta ishga tushganda (masalan
yangi deploy qilinganda) `data/` papkasidagi o'zgarishlar **yo'qolishi
mumkin**, chunki ular image ichida emas, balki runtime paytida yozilgan
bo'ladi. Bunday holatni oldini olish uchun ikki yo'l bor:
  - **Railway Volume** qo'shing (Settings -> Volumes) va uni `/app/data`
    ga ulang - shunda fayllar doimiy saqlanadi.
  - Yoki har safar deploy qilishdan oldin yangi JSON fayllarni to'g'ridan-to'g'ri
    repo ichidagi `data/` papkasiga qo'yib, GitHub'ga push qiling.

Birinchi variant (Volume) tavsiya etiladi, chunki shunda fayllarni
admin panel orqali qayta deploy qilmasdan yangilash mumkin bo'ladi.

## Botning ishlash mantig'i (qisqacha)

- **Talabalar / O'qituvchilar / Xonalar**: foydalanuvchi daraxt
  bo'ylab (fakultet -> kurs -> guruh, yoki bino -> xona) yuradi,
  oxirida tanlangan element uchun edupage sahifasiga Playwright orqali
  kirilib, jadval qismining (SVG) skrinshoti olinadi va foydalanuvchiga
  rasm sifatida yuboriladi.
- **Bo'sh xonalarni topish**: bino -> kun -> para tanlanadi, so'ng
  `boshxonalar.json` dagi tayyor `free_slots` ma'lumotidan foydalanib,
  mos keluvchi xonalar ro'yxati matn ko'rinishida chiqariladi (bunda
  skrinshotga hojat yo'q, chunki ma'lumot allaqachon tayyor).

## Muammolarni bartaraf etish

- **Bot javob bermayapti**: Railway loglarini tekshiring
  (`BOT_TOKEN` to'g'ri kiritilganiga ishonch hosil qiling).
- **Skrinshot o'rniga xatolik chiqyapti**: edupage sayti vaqtincha
  ishlamay qolgan yoki URL noto'g'ri bo'lishi mumkin - loglarda aniq
  xabar ko'rinadi.
- **Fakultet/bino noto'g'ri aniqlanmoqda**: admin paneldagi
  "Ierarxiya sozlamalari" bo'limidan regex pattern'larni to'g'irlang.
- **Admin panelga kira olmayapman**: `.env` (yoki Railway Variables)
  dagi `ADMIN_USERNAME`/`ADMIN_PASSWORD` to'g'ri ekanini tekshiring.
