import re
from fastapi.testclient import TestClient

from app.main import app


def create_code_and_get_ids(client: TestClient):
    client.post("/login", data={"username": "admin", "password": "admin"})
    client.post("/codes", data={"display_name": "待删除码"}, follow_redirects=True)
    r = client.get("/dashboard")
    m_code = re.search(r"/c/([A-Za-z0-9_\-]+)", r.text)
    m_id = re.search(r"/codes/(\d+)/toggle", r.text)
    assert m_code and m_id
    return m_code.group(1), int(m_id.group(1))


def test_delete_code_removes_from_dashboard_and_messages():
    client = TestClient(app)
    public_code, code_id = create_code_and_get_ids(client)
    # submit a message to ensure it will be removed
    client.post(f"/c/{public_code}", data={"content_text": "将被删除的留言"})
    # delete
    r = client.post(f"/codes/{code_id}/delete", follow_redirects=True)
    assert r.status_code == 200
    # verify dashboard no longer lists the code or message
    r = client.get("/dashboard")
    assert public_code not in r.text
    assert "将被删除的留言" not in r.text

