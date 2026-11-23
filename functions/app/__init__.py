"""Flask app：只負責路由與輸入驗證，業務邏輯放在 rules/ 與 ai/。"""
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
