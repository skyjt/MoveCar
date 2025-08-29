import os
from fastapi.testclient import TestClient

os.environ.setdefault("DB_URL", "sqlite:///data/test.db")
os.environ.setdefault("APP_SECRET", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin")
os.environ.setdefault("RATE_LIMIT_WINDOW", "120")
os.environ.setdefault("RATE_LIMIT_COUNT", "1")

from app.main import app  # noqa: E402


def ensure_code(client: TestClient) -> str:
    client.post("/login", data={"username": "admin", "password": "admin"})
    r = client.post("/codes", data={"display_name": "测试码"}, allow_redirects=False)
    assert r.status_code == 302
    r = client.get("/dashboard")
    import re
    # 优先从隐藏元数据中取最新行的 public_code
    m = re.search(r'data-id="(\d+)"\s+data-public="([A-Za-z0-9_\-]+)"', r.text)
    if m:
        return m.group(2)
    m2 = re.search(r"/c/([A-Za-z0-9_\-]+)", r.text)
    assert m2
    return m2.group(1)


def test_rate_limit_blocks_second_request():
    client = TestClient(app)
    code = ensure_code(client)
    r = client.post(f"/c/{code}", data={"content_text": "first"})
    assert r.status_code in (200, 302)
    r = client.post(f"/c/{code}", data={"content_text": "second"})
    assert r.status_code == 429


def test_blacklist_blocks_request():
    client = TestClient(app)
    code = ensure_code(client)
    # get code id via dashboard html (hacky but ok for smoke)
    r = client.get("/dashboard")
    import re
    m_code_id = re.search(r"/codes/(\d+)/toggle", r.text)
    assert m_code_id
    code_id = int(m_code_id.group(1))
    # add client ip to blacklist via API
    r = client.post("/api/v1/blocklist", data={"code_id": code_id, "ip": "127.0.0.1", "reason": "test"})
    assert r.status_code == 200
    # attempt submit should be forbidden
    r = client.post(f"/c/{code}", data={"content_text": "blocked"})
    assert r.status_code == 403
