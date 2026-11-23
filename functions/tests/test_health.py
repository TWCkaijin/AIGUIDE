"""後端健康檢查：用來確認 Flask app 與 Emulator 能正常啟動。"""
from app import create_app


def test_health_returns_ok():
    client = create_app().test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
