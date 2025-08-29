"""简单的内存限流器。

算法：滑动窗口计数（每个键保留窗口内时间戳），适合单实例/轻量使用。
用于限制留言提交频率（按 IP + public_code 维度）。
"""

import os
import time
from typing import Dict, Any


class RateLimiter:
    """基于窗口计数的限流器。"""

    def __init__(self):
        self.window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self.count = int(os.getenv("RATE_LIMIT_COUNT", "1"))
        self._hits: Dict[Any, list[float]] = {}

    def allow(self, key: Any) -> bool:
        """是否允许当前请求。

        参数：
            key: 任意可哈希键（如 (ip, public_code)）。
        返回：
            True 表示放行；False 表示超出阈值。
        """
        now = time.time()
        window_start = now - self.window
        buf = self._hits.setdefault(key, [])
        # drop old
        i = 0
        for t in buf:
            if t >= window_start:
                break
            i += 1
        if i:
            del buf[:i]
        if len(buf) >= self.count:
            return False
        buf.append(now)
        return True
