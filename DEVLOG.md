# DEVLOG.md — 開發日誌

## 2026-11-23 — 規格書加上需求編號

- 在 AI-specification.md 的可驗證條文前加上 [REQ-章節-序號]，使用者故事加上 [US-xx]。
- 共 29 條 REQ(第 1 章 2、第 2 章 1、第 3 章 9、第 4 章 4、第 5 章 4、第 6 章 6、第 7 章 3)，2 則 US。
- 驗證：移除編號後與原規格書逐字相同，內容未增刪改寫。

## 2026-11-23 — 產出 requirements.md

- 依 AI-specification.md 整理出 25 條 FR、4 條 NFR、38 條 AC(Given/When/Then)，29 條 REQ 全部有對應。
- MVP 歸屬只依 [REQ-07-03] 判定；規格未標示歸屬的項目列入 Q-01。
- 列出 19 項待釐清事項(Q-01～Q-19)，其中 Q-02 為 REQ-04-02 與 REQ-04-01／CLAUDE.md 第 4 條的衝突。

## 2026-11-23 — 釐清待釐清事項

- 逐題訪談 requirements.md 的 Q-01～Q-19，決定寫入 decisions.md 的 D-001～D-019。
- 小組未說明理由的地方，一律記為「未說明」；沒有回答的子題記為「未決」。
- 主要未決事項：正式版簡訊認證與資料授權(D-005、D-006)、指標 B 與基準／目標值(D-014)、流程依賴表與樓層圖由誰確認(D-019)。

## 2026-11-23 — 依決策更新 requirements.md

- 依 D-001～D-019 更新各 FR 的 MVP 歸屬、描述與 AC；新增 FR-26(單一後台角色分頁，D-012)與 NFR-05(簡單樓層圖，D-019)。
- FR-11 改為「僅文件」、FR-18 改為「不實作」。
- Q-01～Q-19 標記為已決定；從 decisions.md 的未決與已知限制整理出 Q-20～Q-34。

## 2026-11-23 — 補上八項暫定決策假設

- 在 decisions.md 補寫 D-005、D-006、D-009、D-012、D-013、D-014、D-018、D-019 的暫定方案，供小組確認。
- 指標基準值待量測；涉及正式版的資料授權、介接及院內分工待合作醫院確認。

## 2026-11-23 — 補齊第二輪 Q-20～Q-34 暫定假設

- 將每題的暫定答案併入對應的決策條目，並更新 requirements.md 第 4.2 節的狀態。
- 補上原型驗證碼、檢查模式、部門更新代理審核、模擬醫囑、計時路段、變動通知、服務台備援、重試與工具、求助欄位、時間標示、版本編號及線上模型。

## 2026-11-23 — 原型模型改為 Claude Haiku

- 依小組指示，D-001 的 Q-34 由 OpenAI 暫定方案改為 Claude API 的 `claude-haiku-5-5`；requirements.md NFR-01 同步更新。

## 2026-11-23 — 整併暫定假設至 requirements.md

- 將 decisions.md 中原型相關的暫定假設寫成驗收條件，標示「(暫定，D-xxx)」，共新增 29 條暫定 AC；AC 總數 81 條。
- 新增 AC-NFR01.2、AC-NFR01.3(Claude API `claude-haiku-5-5` 與無法使用時的備援)；FR-25 納入指標 B。
- 正式版才適用的暫定假設(簡訊門號、資料授權、醫囑同步、SSO)未寫入 AC，仍留在 decisions.md。

## 2026-11-23 — 第二輪暫定假設轉為確定決策

- 依小組指示，decisions.md 中 19 處「暫定假設」改為「決定」；只剩合作醫院需確認的部分保留「待確認」。
- requirements.md 移除 29 條 AC 的「暫定」標示，4.2 節改為「已決定」；新增 AC-25.6(試辦目標，基準值量測後驗收)。
- 順手修正 decisions.md 三處過時引用：見 Q-15 → D-015、見 Q-16 → D-016、D-015 的「櫃檯」→ 服務台。

## 2026-11-23 — 產出 design.md 與建置 Firebase emulators

- design.md：規則模組 16 個(R-*)、AI 模組 3 個(A-*)；資料單向流動(輸入凍結＋雜湊比對、AI 只回傳候選 id)；R-GUARD 三類檢查；AI 失敗備援；需求→模組→測試檔對照表；設計待決事項 DD-01～DD-07。
- 提示詞檔由程式逐行複製規格原文產生；test_prompts_verbatim.py 檢查逐字相同。
- 後端：Python 3.12 venv(uv)、Flask app 包在 Cloud Functions `api`(asia-east1)；先寫 test_health.py(失敗)再實作，pytest 3 項通過。
- 前端：Vite + React + TypeScript 骨架，dev server 將 /api 代理到 Functions emulator。
- Emulators：auth 9099、functions 5001、firestore 8080、hosting 5100(5000 被 macOS AirPlay 佔用)、UI 4000；專案 demo-aiguide。煙霧測試全部 200，/api/health 經 Hosting 轉發回傳 {"status":"ok"}。
- firestore.rules 暫時全部拒絕，待撰寫規則測試後再開放讀取。

## 2026-11-23 — DD-01 決定(D-020)

- 下一站從 R-CAND 候選挑選；路線由 LLM 以樓層圖節點序列自由描述，新增規則模組 R-ROUTE 檢查是否可走。
- design.md 同步更新；DD-06(路線候選)因此不適用。

## 2026-11-23 — DD-02 決定(D-021)

- R-GUARD(格式／必含／不得出現，含「下一站屬於候選」)一律執行；R-ROUTE、R-DEP 依檢查者模式由規則或 A-CHECK 負責。design.md 同步更新。

## 2026-11-23 — DD-03 決定(D-022)

- 說明文字暫不做診斷類詞彙檢查，僅靠 Schema 與提示詞原文；AC-21.2 改以人工抽查驗證。design.md 同步更新。

## 2026-11-23 — DD-04 決定(D-023)

- 逾時秒數與 max_tokens 列為可在後台調整的模型設定(需簽核)；初始值與總等待上限未決，DD-04 保留未決部分。

## 2026-11-23 — DD-05 決定(D-024)

- 模擬資料由開發端產出 JSON 草稿並附來源，小組依 D-019 核對後放入 mock_data/。design.md 同步更新。
