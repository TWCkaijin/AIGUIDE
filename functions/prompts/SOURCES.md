# SOURCES.md — 提示詞原文出處

| 檔案 | 編號 | AI-specification.md 行號 |
|---|---|---|
| `planner.system.md` | [US-01] | 51–52 |
| `planner.system.md` | [REQ-02-01] | 54–56 |
| `planner.system.md` | [REQ-03-08] | 90 |
| `planner.system.md` | [REQ-03-09] (a)(d) | 92–93、96 |
| `planner.system.md` | [REQ-04-02] | 112–113 |
| `planner.system.md` | [REQ-04-03] | 115–120 |
| `planner.system.md` | [REQ-06-01] | 168–173 |
| `planner.system.md` | [REQ-06-02] Scenario R6.2-S1 | 175–178 |
| `checker.system.md` | [REQ-04-03] | 115–120 |
| `checker.system.md` | [REQ-04-04] | 122–127 |

- 每一行都與規格書逐字相同(含 ⏳ 標記)，由 `functions/tests/test_prompts_verbatim.py` 檢查。
- [REQ-03-09] 只取標題與 (a)、(d) 兩行：(b)、(c) 由規則模組 R-QUEUE 提供，不交給 AI(D-007)。
- 執行時的資料(候選清單、白名單病人資料、今日事務文字)放在使用者訊息中，不寫入本目錄。
