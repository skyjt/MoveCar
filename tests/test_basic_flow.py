import os
import shutil
from fastapi.testclient import TestClient

os.environ.setdefault("DB_URL", "sqlite:///data/test.db")
os.environ.setdefault("APP_SECRET", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin")

from app.main import app  # noqa: E402
from app.database import init_db  # noqa: E402


def setup_module(module):
    # ensure fresh db
    if os.path.exists("data/test.db"):
        os.remove("data/test.db")
    os.makedirs("app/uploads", exist_ok=True)
    init_db()


def test_login_and_create_code():
    client = TestClient(app)
    # login page
    r = client.get("/login")
    assert r.status_code == 200
    # login
    r = client.post("/login", data={"username": "admin", "password": "admin"}, allow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/dashboard"
    # create code
    r = client.post("/codes", data={"display_name": "我的白车"}, allow_redirects=False)
    assert r.status_code == 302
    # dashboard shows code
    r = client.get("/dashboard")
    assert "我的白车" in r.text or "/c/" in r.text


def test_submit_message_and_list_on_dashboard():
    client = TestClient(app)
    # get a public code from dashboard html
    client.post("/login", data={"username": "admin", "password": "admin"})
    r = client.get("/dashboard")
    assert r.status_code == 200
    # crude extraction
    import re
    m = re.search(r"/c/([A-Za-z0-9_\-]+)", r.text)
    assert m, "no code found on dashboard"
    public_code = m.group(1)
    # landing
    r = client.get(f"/c/{public_code}")
    assert r.status_code == 200
    # submit message
    r = client.post(f"/c/{public_code}", data={"content_text": "请挪车，谢谢"}, allow_redirects=False)
    assert r.status_code == 302
    # dashboard should include message text
    client.post("/login", data={"username": "admin", "password": "admin"})
    r = client.get("/dashboard")
    assert "请挪车" in r.text

