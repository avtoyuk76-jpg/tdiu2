"""
Oddiy web-admin panel: 4 ta JSON faylni (guruhlar, ustozlar, xonalar,
boshxonalar) va ierarxiya sozlamalarini (hierarchy_config.json)
brauzer orqali ko'rish/tahrirlash/yuklash imkonini beradi.

Ishga tushirish (lokal test uchun):
    uvicorn admin.app:app --reload --port 8000

Railway'da bot va admin panel alohida ikkita "process" sifatida
ishga tushiriladi (Procfile ga qarang).
"""

import json
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import config, data_loader  # noqa: E402

app = FastAPI(title="TSUE Bot Admin")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
security = HTTPBasic()

FILES = {
    "guruhlar": config.GURUHLAR_FILE,
    "ustozlar": config.USTOZLAR_FILE,
    "xonalar": config.XONALAR_FILE,
    "boshxonalar": config.BOSHXONALAR_FILE,
}

FILE_TITLES = {
    "guruhlar": "🎓 Guruhlar (talabalar)",
    "ustozlar": "👨‍🏫 O'qituvchilar",
    "xonalar": "🚪 Xonalar",
    "boshxonalar": "🟢 Bo'sh xonalar ma'lumoti",
}


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, config.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, config.ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Login yoki parol noto'g'ri",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def file_stats(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "count": 0, "size_kb": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        count = len(data) if isinstance(data, (dict, list)) else 0
    except Exception:
        count = "xato"
    size_kb = round(path.stat().st_size / 1024, 1)
    return {"exists": True, "count": count, "size_kb": size_kb}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(check_auth)):
    stats = {key: file_stats(path) for key, path in FILES.items()}
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "files": FILES,
            "titles": FILE_TITLES,
            "stats": stats,
        },
    )


@app.get("/file/{name}", response_class=HTMLResponse)
async def view_file(request: Request, name: str, user: str = Depends(check_auth)):
    if name not in FILES:
        raise HTTPException(404, "Bunday fayl yo'q")
    path = FILES[name]
    content = path.read_text(encoding="utf-8") if path.exists() else "{}"
    return templates.TemplateResponse(
        request,
        "edit_file.html",
        {
            "name": name,
            "title": FILE_TITLES.get(name, name),
            "content": content,
            "error": None,
        },
    )


@app.post("/file/{name}", response_class=HTMLResponse)
async def save_file(
    request: Request,
    name: str,
    content: str = Form(...),
    user: str = Depends(check_auth),
):
    if name not in FILES:
        raise HTTPException(404, "Bunday fayl yo'q")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        return templates.TemplateResponse(
            request,
            "edit_file.html",
            {
                "name": name,
                "title": FILE_TITLES.get(name, name),
                "content": content,
                "error": f"JSON xatosi: {e}",
            },
        )

    path = FILES[name]
    path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    data_loader.store.reload()

    return RedirectResponse(url=f"/file/{name}?saved=1", status_code=303)


@app.post("/file/{name}/upload")
async def upload_file(
    name: str,
    file: UploadFile = File(...),
    user: str = Depends(check_auth),
):
    if name not in FILES:
        raise HTTPException(404, "Bunday fayl yo'q")

    raw = await file.read()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(400, f"Yuklangan fayl to'g'ri JSON emas: {e}")

    path = FILES[name]
    path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    data_loader.store.reload()

    return RedirectResponse(url=f"/file/{name}?saved=1", status_code=303)


@app.get("/hierarchy", response_class=HTMLResponse)
async def view_hierarchy(request: Request, user: str = Depends(check_auth)):
    cfg = data_loader.load_hierarchy_config()
    return templates.TemplateResponse(
        request,
        "edit_hierarchy.html",
        {
            "content": json.dumps(cfg, ensure_ascii=False, indent=2),
            "error": None,
        },
    )


@app.post("/hierarchy", response_class=HTMLResponse)
async def save_hierarchy(request: Request, content: str = Form(...), user: str = Depends(check_auth)):
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        return templates.TemplateResponse(
            request,
            "edit_hierarchy.html",
            {"content": content, "error": f"JSON xatosi: {e}"},
        )

    data_loader.save_hierarchy_config(parsed)
    data_loader.store.reload()
    return RedirectResponse(url="/hierarchy?saved=1", status_code=303)


@app.get("/names", response_class=HTMLResponse)
async def view_names(request: Request, user: str = Depends(check_auth)):
    names = data_loader.load_display_names()
    return templates.TemplateResponse(
        request,
        "edit_names.html",
        {
            "content": json.dumps(names, ensure_ascii=False, indent=2),
            "error": None,
        },
    )


@app.post("/names", response_class=HTMLResponse)
async def save_names(request: Request, content: str = Form(...), user: str = Depends(check_auth)):
    try:
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Yuqori darajadagi qiymat dict (obyekt) bo'lishi kerak")
    except (json.JSONDecodeError, ValueError) as e:
        return templates.TemplateResponse(
            request,
            "edit_names.html",
            {"content": content, "error": f"Xatolik: {e}"},
        )

    data_loader.save_display_names(parsed)
    data_loader.store.reload()
    return RedirectResponse(url="/names?saved=1", status_code=303)


@app.post("/reload")
async def reload_data(user: str = Depends(check_auth)):
    data_loader.store.reload()
    return RedirectResponse(url="/?reloaded=1", status_code=303)
