"""简易后台 API 路由。

当前仅提供码级黑名单维护示例接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Code, Blacklist
from ..utils import hash_ip


router = APIRouter(prefix="/api/v1")


def current_user(request: Request, db: Session) -> User | None:
    """解析当前登录用户，未登录返回 None。"""
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, uid)


@router.post("/blocklist")
def add_blocklist(
    request: Request,
    code_id: int = Form(...),
    ip: str = Form(...),
    reason: str = Form(""),
    db: Session = Depends(get_db),
):
    """添加码级黑名单（IP）。需要已登录且对该码有权限。"""
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    bl = Blacklist(code_id=code.id, ip_hash=hash_ip(ip), reason=reason or None)
    db.add(bl)
    db.commit()
    return {"ok": True}


@router.post("/codes/{code_id}/toggle")
def api_toggle_code(
    request: Request,
    code_id: int,
    db: Session = Depends(get_db),
):
    """切换挪车码状态（AJAX）。

    返回 JSON：{"ok": true, "code_id": id, "status": "ACTIVE"|"PAUSED"}
    仅允许已登录用户且需为该码的所有者。
    """
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    code.status = "PAUSED" if code.status == "ACTIVE" else "ACTIVE"
    db.commit()
    return {"ok": True, "code_id": code.id, "status": code.status}


@router.post("/codes/{code_id}/delete")
def api_delete_code(
    request: Request,
    code_id: int,
    db: Session = Depends(get_db),
):
    """删除挪车码（AJAX）。

    返回 JSON：{"ok": true, "code_id": id}
    同步删除相关黑名单与消息（与页面路由保持一致的行为）。
    """
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    code = db.query(Code).filter(Code.id == code_id, Code.owner_id == user.id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    # 删除黑名单并删除该码（消息通过 ORM 关系配置通常会级联，若未配置则依靠外键约束/手动清理）
    db.query(Blacklist).filter(Blacklist.code_id == code.id).delete(synchronize_session=False)
    db.delete(code)
    db.commit()
    return {"ok": True, "code_id": code_id}


@router.post("/messages/{msg_id}/mark")
def api_mark_message(
    request: Request,
    msg_id: int,
    db: Session = Depends(get_db),
):
    """标记留言为已处理（AJAX）。

    返回 JSON：{"ok": true, "msg_id": id}
    仅允许该留言所属码的所有者操作。
    """
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    from ..models import Message, Code

    msg = (
        db.query(Message)
        .join(Code)
        .filter(Message.id == msg_id, Code.owner_id == user.id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.processed = True
    db.commit()
    return {"ok": True, "msg_id": msg_id}
