"""Cloud Functions for Firebase 進入點：以 https 函式包裝 Flask app。"""
from firebase_functions import https_fn, options

from app import create_app

options.set_global_options(region="asia-east1")

_app = create_app()


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    with _app.request_context(req.environ):
        return _app.full_dispatch_request()
