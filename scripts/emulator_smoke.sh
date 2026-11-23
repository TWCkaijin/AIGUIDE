#!/usr/bin/env bash
# 在 Emulator 啟動後檢查各服務是否可用。用法：
#   firebase emulators:exec --project demo-aiguide "bash scripts/emulator_smoke.sh"
set -euo pipefail
check() { printf '%-12s ' "$1"; curl -fsS -o /dev/null -w '%{http_code}\n' "$2"; }
check functions "http://127.0.0.1:5001/demo-aiguide/asia-east1/api/api/health"
check hosting   "http://127.0.0.1:5100/"
check hosting-api "http://127.0.0.1:5100/api/health"
check firestore "http://127.0.0.1:8080/"
check auth      "http://127.0.0.1:9099/"
echo "health body: $(curl -fsS http://127.0.0.1:5100/api/health)"
