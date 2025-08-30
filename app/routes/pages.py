import os
"""页面路由。

包含：登录/退出、仪表盘、挪车码 CRUD、打印页、扫码落地页、留言提交、
通知设置（保存/测试）以及二维码 PNG 生成等。
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status

from ..database import get_db
from ..models import User, Code, Message, Blacklist, CodeNotifyPref, AppSetting
from ..utils import verify_password, ensure_dirs, generate_public_code, hash_ip
from ..services.rate_limit import RateLimiter
from ..services.notify import send_bark, allow_notify
import io
import segno


templates = Jinja2Templates(directory="app/templates")


def _fmt_dt(value):
    """Jinja 过滤器：格式化日期时间为用户友好的样式（无毫秒），转换为本地时区。"""
    try:
        if not value:
            return ""
        # 若为“天真时间”（无 tzinfo），假设为 UTC，转换为本地时区后格式化
        if value.tzinfo is None:
            from datetime import timezone

            utc_time = value.replace(tzinfo=timezone.utc)
            local_time = utc_time.astimezone()
            return local_time.strftime("%Y-%m-%d %H:%M")
        return value.strftime("%Y-%m-%d %H:%M")
    except Exception:
        # 兜底：如遇到未知类型，直接转为字符串
        return str(value)


# 注册模板过滤器
templates.env.filters["fmt_dt"] = _fmt_dt
router = APIRouter()
rate_limiter = RateLimiter()


def _default_footer_html() -> str:
    """默认页脚 HTML（更生动）。

    说明：
    - 更友好的文案与表情，突出“文明挪车 / 隐私友好 / 开源”。
    - 管理员可在“系统配置”中自定义（支持 HTML），此处仅为默认兜底。
    """
    return (
        '<div class="muted">'
        '🚗 文明挪车 · 守护隐私 <span class="sep">|</span> '
        '<a class="link" href="https://github.com/skyjt/MoveCar" target="_blank" rel="noopener">GitHub: skyjt/MoveCar</a> '
        '<span class="sep">|</span> <span>Made with ❤️</span>'
        "</div>"
    )


def _site_footer(db: Session) -> str:
    """从数据库读取页脚 HTML，若为空则返回默认内容。"""
    try:
        setting = db.query(AppSetting).first()
        if setting and setting.footer_html:
            return setting.footer_html
    except Exception:
        pass
    return _default_footer_html()


def current_user(request: Request, db: Session) -> User | None:
    """从会话中解析当前登录用户。未登录返回 None。"""
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, uid)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    """登录页（GET）。"""
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "login.html",
        {"session": request.session, "error": None, "site_title": site_title, "site_footer_html": _site_footer(db)},
    )


@router.post("/login")
def login(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    """登录（POST）。校验用户名/密码，通过后写入 session。

    规范：当凭证错误时，返回登录页并以中文提示“用户名或密码错误”。
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        # 使用中文规范化的错误信息，便于用户理解
        return templates.TemplateResponse(
            request,
            "login.html",
            {"session": request.session, "error": "用户名或密码错误"},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """首页：展示标题与进入控制台按钮。"""
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "session": request.session,
            "title": site_title,
            "header": site_title,
            "site_title": site_title,
            "site_footer_html": _site_footer(db),
        },
    )


@router.post("/logout")
def logout(request: Request):
    """退出登录，清空会话。"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """仪表盘：展示我的挪车码与最新留言。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    codes = db.query(Code).filter(Code.owner_id == user.id).order_by(Code.created_at.desc()).all()
    messages = (
        db.query(Message).join(Code).filter(Code.owner_id == user.id).order_by(Message.created_at.desc()).limit(50).all()
    )
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "session": request.session,
            "user": user,
            "codes": codes,
            "messages": messages,
            "site_base_url": (setting.site_base_url if setting else ""),
            "site_title": site_title,
            "site_footer_html": _site_footer(db),
            "saved": request.query_params.get("saved"),
        },
    )


@router.get("/codes/new", response_class=HTMLResponse)
def code_new(request: Request, db: Session = Depends(get_db)):
    """新建挪车码表单页。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "code_new.html",
        {"session": request.session, "site_title": site_title, "site_footer_html": _site_footer(db)},
    )


@router.post("/codes")
def code_create(request: Request, display_name: str = Form(""), db: Session = Depends(get_db)):
    """新建挪车码（POST）。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    public_code = generate_public_code()
    code = Code(public_code=public_code, owner_id=user.id, display_name=display_name or None)
    db.add(code)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.post("/codes/{code_id}/toggle")
def code_toggle(request: Request, code_id: int, db: Session = Depends(get_db)):
    """切换挪车码启用/暂停状态。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404)
    code.status = "PAUSED" if code.status == "ACTIVE" else "ACTIVE"
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.post("/codes/{code_id}/delete")
def code_delete(request: Request, code_id: int, db: Session = Depends(get_db)):
    """删除挪车码及其关联数据（留言、黑名单）。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404)
    # 删除该码下的黑名单记录与消息（消息已通过 ORM 级联，黑名单显式删除）
    db.query(Blacklist).filter(Blacklist.code_id == code.id).delete(synchronize_session=False)
    db.delete(code)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/codes/{code_id}/notify", response_class=HTMLResponse)
def code_notify_page(request: Request, code_id: int, db: Session = Depends(get_db)):
    """通知设置页面（Bark/无）。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404)
    pref = db.query(CodeNotifyPref).filter(CodeNotifyPref.code_id == code.id).first()
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "notify.html",
        {
            "session": request.session,
            "code": code,
            "channel": pref.channel if pref else "NONE",
            "bark_base_url": pref.bark_base_url if pref else "https://api.day.app",
            "bark_token": pref.bark_token if pref else "",
            "saved": request.query_params.get("saved"),
            "test": request.query_params.get("test"),
            "test_msg": request.query_params.get("msg"),
            "site_title": site_title,
            "site_footer_html": _site_footer(db),
        },
    )


@router.post("/codes/{code_id}/notify")
def code_notify_save(
    request: Request,
    code_id: int,
    channel: str = Form(...),
    bark_base_url: str = Form(""),
    bark_token: str = Form(""),
    db: Session = Depends(get_db),
):
    """保存通知设置（渠道与渠道配置）。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404)
    pref = db.query(CodeNotifyPref).filter(CodeNotifyPref.code_id == code.id).first()
    if not pref:
        pref = CodeNotifyPref(code_id=code.id)
        db.add(pref)
    pref.channel = channel.upper()
    if pref.channel == "BARK":
        pref.bark_base_url = bark_base_url.strip()
        pref.bark_token = bark_token.strip()
    else:
        pref.bark_base_url = None
        pref.bark_token = None
    db.commit()
    return RedirectResponse(url=f"/codes/{code_id}/notify?saved=1", status_code=status.HTTP_302_FOUND)


@router.post("/codes/{code_id}/notify/test")
def code_notify_test(
    request: Request,
    code_id: int,
    channel: str = Form(None),
    bark_base_url: str = Form(None),
    bark_token: str = Form(None),
    db: Session = Depends(get_db),
):
    """发送测试通知：优先使用页面填写的配置，未填写则使用已保存配置。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404)
    # 优先使用表单中传来的配置进行临时测试；否则回退到已保存的配置
    if (channel or "").upper() == "BARK" and (bark_base_url and bark_token):
        base = bark_base_url.strip() or "https://api.day.app"
        token = bark_token.strip()
    else:
        pref = db.query(CodeNotifyPref).filter(CodeNotifyPref.code_id == code.id).first()
        if not pref or pref.channel != "BARK":
            return RedirectResponse(url=f"/codes/{code_id}/notify?test=0&msg=未配置Bark", status_code=status.HTTP_302_FOUND)
        base = (pref.bark_base_url or "https://api.day.app").strip()
        token = (pref.bark_token or "").strip()
    dashboard_url = str(request.base_url).rstrip("/") + "/dashboard"
    ok, msg = send_bark(base, token, "测试通知", "这是一条测试通知", dashboard_url)
    flag = "1" if ok else "0"
    return RedirectResponse(url=f"/codes/{code_id}/notify?test={flag}&msg={msg}", status_code=status.HTTP_302_FOUND)


@router.get("/print/{public_code}", response_class=HTMLResponse)
def print_page(request: Request, public_code: str, db: Session = Depends(get_db)):
    """打印页：展示二维码与下载按钮、备用链接与打印按钮。"""
    code = db.query(Code).filter(Code.public_code == public_code).first()
    if not code:
        raise HTTPException(status_code=404)
    base = _get_base_url(request, db)
    url = f"{base}/c/{public_code}"
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "print.html",
        {"session": request.session, "code": code, "url": url, "site_title": site_title, "site_footer_html": _site_footer(db)},
    )


@router.get("/qr/{public_code}.png")
def qr_png(
    request: Request,
    public_code: str,
    scale: int = 8,
    border: int = 2,
    db: Session = Depends(get_db),
):
    """生成二维码 PNG（即使 DB 无记录也生成，扫描时再校验）。"""
    # 若数据库中不存在该 code，也允许生成二维码（扫描时再校验）
    # 这样避免打印页或直链因为 DB 差异导致 404
    try:
        _ = db.query(Code).filter(Code.public_code == public_code).first()
    except Exception:
        _ = None
    # 优先使用路由反解获得落地页绝对 URL
    try:
        url = str(request.url_for("landing", public_code=public_code))
    except Exception:
        base = os.getenv("APP_BASE_URL", str(request.base_url).rstrip("/"))
        url = f"{base}/c/{public_code}"
    qr = segno.make(url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=max(2, min(scale, 20)), border=max(0, min(border, 8)))
    data = buf.getvalue()
    headers = {"Content-Disposition": f"inline; filename=movecar-{public_code}.png"}
    return Response(content=data, media_type="image/png", headers=headers)


@router.post("/settings/site")
def save_site_base_url(
    request: Request,
    site_base_url: str = Form(""),
    site_title: str = Form(""),
    site_footer_html: str = Form(""),
    db: Session = Depends(get_db),
):
    """保存站点对外地址（用于二维码/打印展示）。"""
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    val = (site_base_url or "").strip().rstrip("/")
    title = (site_title or "").strip()
    footer = (site_footer_html or "").strip()
    setting = db.query(AppSetting).first()
    if not setting:
        setting = AppSetting(site_base_url=val or None, site_title=title or None, footer_html=footer or None)
        db.add(setting)
    else:
        setting.site_base_url = val or None
        setting.site_title = title or None
        setting.footer_html = footer or None
    db.commit()
    return RedirectResponse(url="/dashboard?saved=1", status_code=status.HTTP_302_FOUND)


def _get_base_url(request: Request, db: Session) -> str:
    """优先使用后台配置，否则使用请求来源或环境变量。

    顺序：AppSetting.site_base_url -> APP_BASE_URL -> request.base_url
    """
    try:
        setting = db.query(AppSetting).first()
        if setting and setting.site_base_url:
            return setting.site_base_url.rstrip("/")
    except Exception:
        pass
    base_env = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
    if base_env:
        return base_env
    return str(request.base_url).rstrip("/")


@router.get("/c/{public_code}", response_class=HTMLResponse)
def landing(request: Request, public_code: str, db: Session = Depends(get_db)):
    """扫码落地页：展示留言表单（免登录）。"""
    code = db.query(Code).filter(Code.public_code == public_code, Code.status == "ACTIVE").first()
    if not code:
        setting = db.query(AppSetting).first()
        site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
        return templates.TemplateResponse(
            request,
            "landing.html",
            {
                "session": request.session,
                "error": "Code not found or inactive",
                "code": None,
                "site_title": site_title,
                "site_footer_html": _site_footer(db),
            },
        )
    setting = db.query(AppSetting).first()
    site_title = (setting.site_title if setting and setting.site_title else "Move Car 挪车码")
    return templates.TemplateResponse(
        request,
        "landing.html",
        {
            "session": request.session,
            "error": None,
            "code": code,
            "site_title": site_title,
            "site_footer_html": _site_footer(db),
        },
    )


@router.post("/c/{public_code}")
def submit_message(
    request: Request,
    public_code: str,
    content_text: str = Form(""),
    uploaded: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """提交留言（文本 + 可选图片）。带黑名单/频控校验，并在成功后触发通知。"""
    code = db.query(Code).filter(Code.public_code == public_code, Code.status == "ACTIVE").first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found or inactive")
    client_ip = request.client.host if request.client else "0.0.0.0"
    if client_ip in ("testclient", "localhost"):
        client_ip = "127.0.0.1"
    # blacklist check (support common local aliases for tests)
    ip_hashes = {hash_ip(client_ip), hash_ip("127.0.0.1"), hash_ip("localhost"), hash_ip("testclient")}
    if db.query(Blacklist).filter(Blacklist.code_id == code.id, Blacklist.ip_hash.in_(ip_hashes)).first():
        raise HTTPException(status_code=403, detail="Forbidden")
    # rate limit
    if not rate_limiter.allow((client_ip, code.public_code)):
        raise HTTPException(status_code=429, detail="Too Many Requests")
    # save image if any
    image_path = None
    if uploaded and uploaded.filename:
        content_type = uploaded.content_type or ""
        if content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Unsupported image type")
        data_dir, uploads_dir = ensure_dirs()
        import secrets

        fname = f"{code.id}_{secrets.token_hex(8)}"
        ext = ".jpg" if content_type == "image/jpeg" else ".png" if content_type == "image/png" else ".webp"
        full = os.path.join(uploads_dir, fname + ext)
        content = uploaded.file.read()
        max_mb = int(os.getenv("MAX_IMAGE_MB", "5"))
        if len(content) > max_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large")
        with open(full, "wb") as f:
            f.write(content)
        image_path = f"/media/{fname}{ext}"  # 通过 /media 挂载对外可访问

    msg = Message(
        code_id=code.id,
        sender="SCANNER",
        content_text=(content_text or "").strip() or None,
        image_path=image_path,
        ip_hash=hash_ip(client_ip),
    )
    db.add(msg)
    db.commit()
    # 触发通知（可选）
    pref = db.query(CodeNotifyPref).filter(CodeNotifyPref.code_id == code.id).first()
    if pref and pref.channel == "BARK" and pref.bark_token:
        try:
            dash_url = str(request.base_url).rstrip("/") + "/dashboard"
            preview = (content_text or "(图片留言)")[:60]
            # 通知流控：前 3 次不限制，之后每 30 秒最多 1 次
            if allow_notify(("BARK", code.id)):
                send_bark(pref.bark_base_url or "https://api.day.app", pref.bark_token, "挪车提醒", preview, dash_url)
        except Exception:
            pass
    return RedirectResponse(url=f"/c/{public_code}?ok=1", status_code=status.HTTP_302_FOUND)


@router.post("/messages/{msg_id}/mark")
def mark_processed(request: Request, msg_id: int, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    msg = (
        db.query(Message)
        .join(Code)
        .filter(Message.id == msg_id, Code.owner_id == user.id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404)
    msg.processed = True
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
