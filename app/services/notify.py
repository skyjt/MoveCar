"""通知发送与通知级限流。

当前实现：
- Bark 通知（基于 https://bark.day.app/ 生态）；
- 通知流控：每个码前 3 次放行，之后默认每 30 秒最多 1 次（可通过 `NOTIFY_MIN_INTERVAL_SEC` 调整）。
"""

import httpx
from typing import Tuple, Dict, Any
import time
import os


def send_bark(base_url: str, token: str, title: str, body: str, url: str | None = None) -> Tuple[bool, str]:
    """发送 Bark 通知。

    参数：
        base_url: Bark 服务基础 URL（默认 https://api.day.app）。
        token: 设备 Token（在 Bark App 中复制）。
        title/body: 通知标题与正文。
        url: 可选跳转链接。
    返回：
        (ok, msg) 二元组，ok 为是否成功，msg 为简要说明。
    """
    base = (base_url or "").strip().rstrip("/")
    if not base or not token:
        return False, "缺少 Bark 基础 URL 或 Token"
    endpoint = f"{base}/{token}"
    payload = {"title": title or "通知", "body": body or ""}
    if url:
        payload["url"] = url
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(endpoint, json=payload)
            if resp.status_code == 200:
                return True, "发送成功"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, f"异常: {e}" 


# 通知流控：前 3 次不限制；之后每 30 秒最多 1 次（可通过环境变量调整）
_STATE: Dict[Any, Dict[str, Any]] = {}


def allow_notify(key: Any) -> bool:
    """通知速率限制判定。

    规则：
    - 前 3 次直接放行；
    - 第 4 次开始，需要距离上次成功发送 >= NOTIFY_MIN_INTERVAL_SEC（默认 30s）。
    参数：
        key: (channel, code_id) 或其他可哈希对象。
    返回：
        True/False。
    """
    now = time.time()
    min_gap = int(os.getenv("NOTIFY_MIN_INTERVAL_SEC", "30"))
    s = _STATE.get(key)
    if s is None:
        _STATE[key] = {"count": 1, "last_ts": now}
        return True
    # 前三次放行
    if s.get("count", 0) < 3:
        s["count"] = s.get("count", 0) + 1
        s["last_ts"] = now
        return True
    last = float(s.get("last_ts", 0))
    if now - last >= min_gap:
        s["last_ts"] = now
        return True
    return False
