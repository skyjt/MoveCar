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
