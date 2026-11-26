# design.md — 醫院通系統設計

> 依據：`requirements.md`(FR／NFR／AC)與 `decisions.md`(D-001～D-035)。規格書 `AI-specification.md` 不修改。
> 本文件的技術選型由開發端規劃(依小組指定：雲端優先 Firebase、前端 Vite + React、後端 Python Flask)。
> 規格與決策都沒有寫的數值、名單與規則，本文件不自行填入，一律列在第 10 節「設計待決事項」(DD-xx)。

---

## 1. 設計原則

| # | 原則 | 依據 |
|---|---|---|
| P1 | **每次結果都必須一樣的部分，只能由規則程式產生**，不交給生成式 AI | CLAUDE.md 第 4 條、[REQ-04-01]、D-002、D-018 |
| P2 | **資料只能從規則程式流向 AI**。AI 只讀規則程式準備好的輸入，AI 的輸出不得寫回、也不得改動規則程式的結果與原始輸入 | 小組設計要求 |
| P3 | **AI 的輸出必須先通過檢查才能顯示**：格式、必須包含的內容、不得出現的內容 | 小組設計要求、[REQ-04-04]、D-008 |
| P4 | **給 AI 的提示詞使用規格書原文**，存成獨立檔案，程式不得自行改寫 | 小組設計要求 |
| P5 | **AI 失敗時，使用者仍能完成工作**：一律有規則程式的備援路徑 | D-001 Q-34、D-017 |
| P6 | **只使用模擬資料** | CLAUDE.md 第 5 條、NFR-04 |
| P7 | **只把白名單欄位送進 AI** | [REQ-06-05]、D-006、FR-22 |

---

## 2. 模組劃分：規則程式 vs. 生成式 AI

### 2.1 必須每次一樣 → 規則模組(`functions/rules/`)

| 模組 | 職責 | 主要對應 |
|---|---|---|
| **R-STATIC** 靜態資料 | 依「版本組合」查詢站點、部門定位、樓層圖節點與路段、流程依賴表、服務台、地標、等候區 | FR-06、NFR-05、D-018 |
| **R-VERSION** 版本與審核 | 部門資訊變更送審、審核、退回；模型設定送簽、簽核、版本紀錄；發布「生效版本組合」 | FR-06、FR-19、FR-24、D-009、D-016、D-018 |
| **R-DEMO** 範例草案 | 只在「檢查者模式」欄位提供三份範例(標示「範例」)，載入後只產生草稿，不改動生效設定 | FR-24、D-038 |
| **R-PROGRESS** 就醫進度 | 記錄站點完成(模擬登錄)、模擬醫囑推送、今日待辦步驟 | FR-05、FR-14、FR-17、D-013 |
| **R-CAND** 候選產生 | 依流程依賴表、目前進度、有效醫囑，算出**允許的下一站候選** | FR-01、FR-02、D-002、D-020 |
| **R-ROUTE** 路線檢查 | 檢查 LLM 描述的路線(樓層圖節點序列)：相鄰節點之間有路段、路段開放、符合無障礙需求、起訖點正確 | FR-01、FR-13、D-020 |
| **R-WL** 白名單組裝 | 只取姓名、年齡、性別、醫囑、無障礙需求，組成送給 AI 的病人資料 | FR-07、FR-13、FR-14、FR-22、D-006 |
| **R-GUARD** 輸出檢查 | 檢查 AI 輸出的格式、必須包含的內容、不得出現的內容(見第 4 節) | FR-01、FR-21、FR-23、P3 |
| **R-DEP** 依賴檢查(RuleBase 檢查者) | 比對 AI 選定的流程是否違反流程依賴表 | FR-02、FR-03、D-008 |
| **R-ORCH** 規劃流程控制 | 串接 R-CAND → A-PLAN → R-GUARD → 檢查者(依模式：R-ROUTE＋R-DEP／A-CHECK)；處理重試上限、檢查者模式、失敗轉備援；記錄系統錯誤 | FR-03、FR-04、D-008、D-011 |
| **R-DESK** 服務台備援 | 依最新生效樓層圖選服務台與路線、產生固定文案 | FR-04、FR-21、NFR-01、D-017 |
| **R-QUEUE** 模擬叫號 | 提供 (b) 預計等候時間、(c) 目前叫號、預測人流(皆為模擬資料) | FR-15、FR-16 |
| **R-IMPACT** 變動影響判斷 | 新版本生效時，比對各導引工作階段的當前與未走路段、未抵達站點 | FR-20、D-015、D-018 |
| **R-NOTIFY** 站內通知 | 寫入通知、同一工作階段同一版本只推一次 | FR-14、FR-20、D-013、D-015 |
| **R-HELP** 求助通報 | 組成通報(模擬姓名、必要時無障礙需求、站點或路段)，送給護理站與服務台 | FR-23、D-010、D-011 |
| **R-AUTH** 登入 | 模擬身分證／健保卡登入、固定測試碼驗證、建立工作階段 | FR-09、FR-10、FR-12、D-005 |
| **R-RBAC** 後台權限 | 角色與部門範圍、禁止自審自簽、服務台只能代填今日事務 | FR-19、FR-24、FR-26、FR-27、D-012、D-016、D-033 |
| **R-METRIC** 成效指標 | 指標 A 依路段計時與平均、指標 B 計算 | FR-25、D-014 |

### 2.2 交給生成式 AI → AI 模組(`functions/ai/`)

| 模組 | 職責 | 可以決定什麼 | 不可以做什麼 | 對應 |
|---|---|---|---|---|
| **A-PLAN** 導引規劃 | 依今日事務文字與白名單資料，從 R-CAND 的候選中**挑選**下一站，並**自由描述**前往路線(D-020) | 選哪一個下一站候選；路線經過哪些樓層圖節點(依序)；說明文字；(a) 步行時間估計；(d) 整趟時間估計；是否「超出就醫流程範圍」；是否提示求助 | 不能選候選以外的下一站；路線只能使用樓層圖既有的節點 id；不能改動候選、依賴表、進度、醫囑或使用者輸入；不能輸出緊急等級、病名、診斷、處置建議 | FR-01、FR-15、FR-21、FR-23、D-002、D-007、D-010、D-020 |
| **A-CHECK** 專用 Agent 檢查者 | 依提示詞檢查 A-PLAN 的輸出是否違反依賴 | 通過／不通過與理由 | 不能修改 A-PLAN 的輸出 | FR-03、D-008 |
| **A-CLIENT** 模型呼叫 | 以 Claude API 呼叫 `claude-haiku-5-5`，使用結構化輸出；處理逾時、服務錯誤、拒絕回應 | — | 不在前端呼叫；金鑰只在後端 | NFR-01、D-001 Q-34 |

> **對 D-002 的落實方式(D-020)**：下一站由 LLM 從規則程式給定的候選中挑選，確保不牴觸依賴([REQ-04-03])；路線由 LLM 自由描述，再由 R-ROUTE 檢查是否可走。AI 的輸出不會改動規則程式的結果(P2)。

---

## 3. 資料流(單向：規則 → AI → 檢查 → 顯示)

```text
使用者輸入(今日事務文字)──┐
模擬病人資料 ── R-WL 白名單 ─┤
進度/醫囑 ── R-PROGRESS ─────┤
版本組合 ── R-STATIC ── R-CAND(下一站候選)、樓層圖 ─┤
                                                      ▼
                         ┌──────── 唯讀輸入包 PlanInput(凍結) ────────┐
                         │  · 提示詞檔(規格原文)                         │
                         │  · 白名單病人資料、今日事務文字                 │
                         │  · 下一站候選(含 id)、樓層圖節點與路段         │
                         └──────────────────┬──────────────────────────┘
                                            ▼
                                  A-PLAN(Claude Haiku)
                                            ▼
                                  AiPlanOutput(下一站 id、路線節點序列、文字)
                                            ▼
                        R-GUARD 格式／必含／不得出現(一律執行) ─不通過┐
                                            ▼                    │
              檢查者(依模式：R-ROUTE＋R-DEP／A-CHECK／兩者，D-021) ─不通過┤
                                            ▼                    ▼
                                    發布導引結果          R-ORCH 重試(上限 D-011)
                                            ▼                    ▼ 超過上限／AI 失敗
                                 前端顯示(附來源版本組合)   R-DESK 服務台備援
```

**單向保證的實作方式**

1. **輸入凍結**：R-ORCH 先組好 `PlanInput`(不可變的資料物件)並計算雜湊值；AI 呼叫前後比對雜湊，不一致即視為系統錯誤。
2. **輸出只含參照**：A-PLAN 的結構化輸出只允許 `next_station_id`(候選 id)、`route_node_ids`(樓層圖節點 id 序列)與文字欄位；最後顯示的站點名稱、樓層、路段，一律由 R-STATIC 依 id 查出，不使用 AI 產生的名稱。
3. **分開儲存**：AI 輸出存在 `ai_plans` 集合，引用版本組合與 `PlanInput` 雜湊；規則資料所在的集合，AI 模組沒有寫入權限(程式層：AI 模組不匯入 Firestore 寫入函式；資料層：Firestore 規則禁止前端寫入)。
4. **AI 不呼叫寫入型工具**：提供給模型的 tool 只有唯讀查詢(D-011 Q-29)；工具結果也來自 R-STATIC／R-QUEUE。

---

## 4. AI 輸出檢查(R-GUARD)

A-PLAN 使用 Claude API 的結構化輸出(`output_config.format` 的 JSON Schema)。即使如此，後端仍完整驗證一次，三類檢查全部通過才交給檢查者。依 D-021，R-GUARD 不受檢查者模式影響、一律執行；路線可不可走(R-ROUTE)與流程依賴(R-DEP)則依檢查者模式由規則程式或 A-CHECK 負責。

| 類別 | 檢查項目 | 不通過時 |
|---|---|---|
| **格式** | 符合 `AiPlanOutput` JSON Schema(必要欄位、型別、無多餘欄位)；`stop_reason` 不是 `refusal`、不是 `max_tokens` | 視為 AI 失敗，計入重試 |
| **必須包含** | `next_station_id` 屬於 R-CAND 的下一站候選；`route_node_ids` 由目前位置開始、在該下一站結束，且每個 id 都存在於樓層圖(可不可走由檢查者負責，見 D-021)；`explanation` 非空字串；`walk_minutes_estimate`、`total_minutes_estimate` 為數值或 null；`out_of_scope`、`suggest_help` 為布林值 | 計入重試 |
| **不得出現** | 輸出中不得出現候選以外的下一站 id、樓層圖以外的節點 id；說明文字中出現的站點名稱(依 R-STATIC 名稱表比對)只能是被選中的站點或其路線經過的站點；不得出現白名單以外的病人欄位；不得出現緊急等級、病名、診斷、處置建議的欄位(Schema 不提供這些欄位) | 計入重試 |

- `out_of_scope = true` 時(使用者問診斷或非就醫流程問題)：不顯示 AI 的說明文字，改由 R-DESK 顯示 [AC-21.3] 的固定文案與服務台路線。
- `suggest_help = true` 時：只觸發求助按鈕提示([AC-23.4])，不顯示任何判斷文字。
- 依 D-022，說明文字**暫不做**診斷類詞彙檢查，只以 Schema 限制(不提供相關欄位)與提示詞原文([REQ-06-01])防範。AI 仍可能在說明文字中寫出類似診斷的句子，原型以人工抽查驗證。

---

## 5. 提示詞檔案(規格書原文)

| 檔案 | 用途 | 收錄的規格原文 |
|---|---|---|
| `functions/prompts/planner.system.md` | A-PLAN 的系統提示詞 | [US-01]、[REQ-02-01]、[REQ-03-08]、[REQ-03-09] 的 (a)(d)、[REQ-04-02]、[REQ-04-03]、[REQ-06-01]、[REQ-06-02] Scenario S1 |
| `functions/prompts/checker.system.md` | A-CHECK 的系統提示詞 | [REQ-04-03]、[REQ-04-04] |
| `functions/prompts/SOURCES.md` | 每段原文的出處行號與編號 | — |

規則：

- 檔案中的原文段落必須與 `AI-specification.md` **逐字相同**(含原文中的 ⏳ 標記)，由測試 `functions/tests/test_prompts_verbatim.py` 檢查。
- 檔案只額外加上標題列與分隔線，不加入規格以外的指示。
- 執行時才加入的資料(候選清單、白名單病人資料、今日事務文字)放在使用者訊息中，不寫進提示詞檔。
- 修改提示詞屬於「模型設定」，依 D-011、D-016 送簽後才生效；版本紀錄保存在 Firestore，檔案中的內容為初始版本。

---

## 6. AI 失敗時的備援

| 失敗情況 | 偵測方式 | 使用者看到的內容 | 使用者如何完成工作 |
|---|---|---|---|
| 模型服務無法使用、逾時、網路錯誤 | A-CLIENT 例外 | 「目前無法自動規劃，請向服務台詢問」([AC-NFR01.3]) | R-DESK 用規則程式產生前往服務台的路線(D-017)，由現場人員協助 |
| 模型拒絕回應(`refusal`) | `stop_reason` | 同上 | 同上 |
| 輸出格式錯誤或內容不合格 | R-GUARD | 重試期間顯示「規劃中」；超過重試上限後顯示 [AC-04.2] 文案 | 同上 |
| 檢查者判定違反依賴 | R-DEP／A-CHECK | 同上 | 同上 |
| 檢查結果無法取得 | R-ORCH | 不發布該次輸出([AC-03.6])，再依重試上限處理 | 同上 |
| 起點無法確認 | R-DESK | 請使用者選擇所在站點；仍無法確認時顯示「請詢問附近院內人員」([AC-04.4]) | 現場人員協助 |

**AI 失敗時仍可正常使用的功能**(都由規則模組提供，不依賴 AI)：

- 今日行程頁：已完成與待完成的站點、(b) 預計等候、(c) 目前叫號(模擬)
- 醫院地圖、就醫導覽資料(靜態頁)
- 側邊欄常駐的「我需要求助」按鈕與通報([AC-23.1]、[AC-23.3])
- 臨時變動通知、站內通知
- 後台全部功能

---

## 7. 技術架構

### 7.1 選型

| 層 | 技術 | 說明 |
|---|---|---|
| 前端 | Vite + React + TypeScript | 病人端 6 個畫面(NFR-03)與後台(FR-26)放在同一個 SPA，以路由 `/` 與 `/admin` 區分 |
| 前端測試 | Vitest + React Testing Library | — |
| 後端 | Python 3.12、Flask | 以 Cloud Functions for Firebase(Python)的 `https_fn.on_request` 包裝 Flask app，對外路徑 `/api/**` |
| 後端測試 | pytest | 規則模組單元測試；AI 模組以假的模型客戶端測試；整合測試連 Emulator |
| AI | Anthropic Python SDK、`claude-haiku-5-5` | 結構化輸出、唯讀 tool；只在後端呼叫 |
| 資料庫 | Cloud Firestore | 規則資料、版本、進度、通知、通報、指標紀錄 |
| 登入 | Firebase Authentication | 病人：後端驗證模擬身分與固定測試碼後發 custom token；後台：模擬個人帳號＋custom claims(角色、部門) |
| 即時通知 | Firestore 即時監聽(`onSnapshot`) | 站內通知、求助通報、行程更新(D-015「立即推送」) |
| 部署 | Firebase Hosting ＋ Cloud Functions，區域 `asia-east1` | Hosting 將 `/api/**` 轉給 Functions |
| 本機開發 | Firebase Local Emulator Suite | Auth、Functions、Firestore、Hosting、Emulator UI；專案 id `demo-aiguide`(demo- 開頭，不連到真實專案) |
| 金鑰 | Functions secret `ANTHROPIC_API_KEY`、固定測試碼(D-025) | 本機放在 `functions/.secret.local`(不進版控)，repo 只提供範本 |

### 7.2 目錄結構

```text
AIHealthCare/
├── firebase.json / .firebaserc / firestore.rules / firestore.indexes.json
├── frontend/                 Vite + React(病人端＋後台)
├── functions/
│   ├── main.py               Functions 進入點(包裝 Flask)
│   ├── app/                  Flask 路由(只做輸入驗證與呼叫模組)
│   ├── rules/                規則模組 R-*
│   ├── ai/                   AI 模組 A-*
│   ├── prompts/              提示詞檔(規格原文)
│   ├── requirements.txt
│   └── tests/                pytest
├── mock_data/                模擬資料(D-019 確認後才放入)
└── scripts/                  模擬資料匯入 Emulator 等工具
```

### 7.3 Firestore 資料模型(主要集合)

| 集合 | 內容 | 寫入者 |
|---|---|---|
| `data_versions/{v}` | 站點、部門、樓層圖節點與路段、服務台、地標、等候區(某一版本) | R-VERSION |
| `model_settings_versions/{v}` | 提示詞、流程依賴表、檢查者模式、模型、重試上限、工具組件、逾時秒數、`max_tokens`(D-023) | R-VERSION |
| `active/current` | 目前生效的版本組合 | R-VERSION |
| `change_requests/{id}` | 部門資訊變更、模型設定變更的送審／送簽紀錄 | R-VERSION |
| `patients/{id}` | 模擬病人(只有白名單 5 欄) | 匯入腳本 |
| `visits/{id}` | 當次就醫、今日待辦、進度、有效醫囑 | R-PROGRESS |
| `guide_sessions/{id}` | 導引工作階段、目前路段、引用的版本組合 | R-ORCH |
| `ai_plans/{id}` | AI 輸出、檢查結果、引用的 `PlanInput` 雜湊 | R-ORCH |
| `notifications/{uid}/items/{id}` | 站內通知 | R-NOTIFY |
| `help_alerts/{id}` | 求助通報 | R-HELP |
| `segment_timings/{id}`、`step_results/{id}` | 指標 A、B 的原始紀錄 | R-METRIC |
| `system_errors/{id}` | 依賴違規、AI 失敗等系統錯誤 | R-ORCH |

所有寫入都經過後端(Admin SDK)。`firestore.rules` 只開放已登入使用者**讀取**自己的就醫、通知，以及後台角色可讀的集合；前端一律不能寫入。

### 7.4 Emulator

| 服務 | 位址 |
|---|---|
| Emulator UI | http://127.0.0.1:4000 |
| Hosting | http://127.0.0.1:5100 |
| Functions | http://127.0.0.1:5001 |
| Firestore | http://127.0.0.1:8080 |
| Auth | http://127.0.0.1:9099 |

啟動方式：

```bash
firebase emulators:start --project demo-aiguide
```

---

## 8. 主要流程

1. **登入**(FR-09、FR-10)：前端送模擬身分與驗證碼 → R-AUTH 比對固定測試碼 → 發 custom token → 前端以 Auth 登入。
2. **規劃**(FR-01～FR-04)：前端送今日事務文字 → R-ORCH 依第 3 節流程產生結果 → 寫入 `ai_plans` 與 `guide_sessions` → 前端顯示由 R-STATIC 查出的站點與路線、AI 說明文字、(a)(d) 估計(標示「AI 估計（原型示意）」)、(b)(c) 模擬資料。
3. **站點完成**(FR-05、FR-17)：測試工具模擬站點登錄 → R-PROGRESS 更新進度 → 開始新的計時路段(R-METRIC) → 重新規劃。
4. **醫囑推送**(FR-14)：測試工具推送模擬醫囑 → R-PROGRESS 更新 → R-NOTIFY 送「今日行程已更新，請確認下一站」→ 重新規劃。
5. **部門變更**(FR-19、FR-20)：部門送審 → 他人審核 → R-VERSION 發布新版本組合 → R-IMPACT 找出受影響工作階段 → R-NOTIFY 推送 → 受影響者重新規劃。
6. **求助**(FR-23)：使用者按按鈕 → R-HELP 寫入 `help_alerts` → 後台求助通報分頁即時收到。
7. **模型設定**(FR-24)：護理行政人員修改 → 送簽 → 另一位簽核 → R-VERSION 發布新的模型設定版本。
   - 示範草案(D-038)：僅「檢查者模式」欄位旁有「使用範例」按鈕，載入開發端草擬的範例(只用規則程式／只用專用 Agent／兩者都用)，畫面標示「範例」；載入後走同一條送簽、簽核流程；接上真實金鑰後按鈕保留；範例不得改動提示詞原文。

---

## 9. 不在本設計範圍

- FR-11 僅限院內使用：只寫在文件中(D-004)。
- FR-18 站點核查走錯站：系統不實作(D-001 第 9 項)。
- 所有真實系統串接(健保、HIS、叫號、簡訊、SSO、院內自架模型)：正式版另行設計。

---

## 10. 設計待決事項

| 編號 | 問題 | 為何需要決定 | 相關 |
|---|---|---|---|
| ~~DD-01~~ | ~~下一站與路線的決策分工~~ | 已決定：D-020(下一站從候選挑選，路線由 LLM 自由描述後由規則檢查) | D-002 |
| ~~DD-02~~ | ~~檢查者模式與規則輸出檢查的分工~~ | 已決定：D-021(R-GUARD 一律執行；R-ROUTE、R-DEP 依檢查者模式) | D-008 |
| ~~DD-03~~ | ~~診斷類用語詞表~~ | 已決定：D-022(暫不做詞彙檢查) | FR-21、D-010 |
| ~~DD-04~~ | ~~逾時秒數、`max_tokens` 初始值與總等待上限~~ | 已決定：D-023(列為可調整的模型設定)、D-029(30 秒／16000／總上限 60 秒) | NFR-01 |
| ~~DD-05~~ | ~~模擬資料的製作方式~~ | 已決定：D-024(開發端產出 JSON 草稿，小組依 D-019 核對後放入 `mock_data/`) | D-019、FR-05、FR-23 |
| ~~DD-06~~ | ~~路線候選的產生方式與數量~~ | 依 D-020 不再產生路線候選，此項不適用 | FR-01 |
| ~~DD-07~~ | ~~模擬病人與固定測試碼~~ | 已決定：D-025(併入 D-024 草稿；測試碼放 `functions/.secret.local`) | FR-09、FR-10 |

---

## 11. 需求 → 模組 → 測試檔 對照表

測試檔路徑：後端在 `functions/tests/`，前端在 `frontend/src/**/__tests__/`，Firestore 規則測試在 `tests/firestore-rules/`。測試檔依 CLAUDE.md 第 3 條，在對應程式之前撰寫。

| 需求 | 模組 | 測試檔 |
|---|---|---|
| FR-01 規劃下一站與路線 | R-CAND、R-ROUTE、A-PLAN、R-ORCH、R-GUARD | `functions/tests/rules/test_candidates.py`、`functions/tests/rules/test_route_check.py`、`functions/tests/ai/test_planner.py`、`functions/tests/rules/test_plan_pipeline.py`、`functions/tests/rules/test_output_guard.py` |
| FR-02 流程依賴限制 | R-CAND、R-DEP | `functions/tests/rules/test_candidates.py`、`functions/tests/rules/test_dependency_checker.py` |
| FR-03 輸出檢查與重新產生 | R-ORCH、R-DEP、A-CHECK | `functions/tests/rules/test_plan_pipeline.py`、`functions/tests/rules/test_dependency_checker.py`、`functions/tests/ai/test_agent_checker.py` |
| FR-04 重試上限與轉介服務台 | R-ORCH、R-DESK | `functions/tests/rules/test_plan_pipeline.py`、`functions/tests/rules/test_service_desk.py` |
| FR-05 完成站點後的引導 | R-PROGRESS、R-ORCH | `functions/tests/rules/test_progress.py`、`functions/tests/integration/test_api_progress.py` |
| FR-06 靜態資料版本內一致 | R-STATIC、R-VERSION | `functions/tests/rules/test_static_data.py`、`functions/tests/rules/test_versioning.py` |
| FR-07 取得病人基本資料 | R-WL | `functions/tests/rules/test_whitelist.py` |
| FR-08 今日到院預辦事務輸入 | 前端 AI 對話頁、R-ORCH | `frontend/src/pages/__tests__/ChatPage.test.tsx`、`functions/tests/integration/test_api_plan.py` |
| FR-09 登入身分 | R-AUTH、前端登入頁 | `functions/tests/rules/test_auth_mock.py`、`frontend/src/pages/__tests__/LoginPage.test.tsx` |
| FR-10 手機簡訊認證 | R-AUTH | `functions/tests/rules/test_auth_mock.py` |
| FR-11 僅限院內使用 | (僅文件) | — |
| FR-12 只顯示今日行程 | 前端使用者資訊頁、Firestore 規則 | `frontend/src/pages/__tests__/ProfilePage.test.tsx`、`tests/firestore-rules/rules.test.ts` |
| FR-13 收集無障礙需求 | 前端使用者資訊頁、R-WL、R-ROUTE | `frontend/src/pages/__tests__/ProfilePage.test.tsx`、`functions/tests/rules/test_whitelist.py`、`functions/tests/rules/test_route_check.py` |
| FR-14 醫囑輸入 | R-PROGRESS、R-NOTIFY、R-WL | `functions/tests/rules/test_progress.py`、`functions/tests/rules/test_notify.py`、`functions/tests/rules/test_whitelist.py` |
| FR-15 時間類輸出 | R-QUEUE、A-PLAN、前端今日行程頁 | `functions/tests/rules/test_queue_mock.py`、`functions/tests/ai/test_planner.py`、`frontend/src/pages/__tests__/ItineraryPage.test.tsx` |
| FR-16 預測抵達時間與人流 | R-QUEUE | `functions/tests/rules/test_queue_mock.py` |
| FR-17 站點完成登錄 | R-PROGRESS | `functions/tests/rules/test_progress.py` |
| FR-18 站點核查走錯站 | (不實作) | — |
| FR-19 臨時變動資訊更新與審核 | R-VERSION、R-RBAC | `functions/tests/rules/test_versioning.py`、`functions/tests/rules/test_rbac.py` |
| FR-20 路線註冊與變動通知 | R-IMPACT、R-NOTIFY、R-ORCH | `functions/tests/rules/test_impact.py`、`functions/tests/rules/test_notify.py`、`functions/tests/integration/test_api_change_flow.py` |
| FR-21 AI 禁止事項 | 提示詞檔、R-GUARD、R-DESK | `functions/tests/test_prompts_verbatim.py`、`functions/tests/rules/test_output_guard.py`、`functions/tests/rules/test_service_desk.py` |
| FR-22 送入 LLM 的資料白名單 | R-WL、A-CLIENT | `functions/tests/rules/test_whitelist.py`、`functions/tests/ai/test_claude_client.py` |
| FR-23 求助按鈕與通報 | 前端側邊欄、R-HELP、R-GUARD | `frontend/src/components/__tests__/HelpButton.test.tsx`、`functions/tests/rules/test_help_alert.py`、`functions/tests/rules/test_output_guard.py` |
| FR-24 模型設定修改與雙人覆核 | R-VERSION、R-RBAC | `functions/tests/rules/test_versioning.py`、`functions/tests/rules/test_rbac.py` |
| FR-25 成效指標計算 | R-METRIC | `functions/tests/rules/test_metrics.py` |
| FR-26 單一後台與角色分頁 | 前端後台、R-RBAC、Firestore 規則 | `frontend/src/admin/__tests__/AdminTabs.test.tsx`、`functions/tests/rules/test_rbac.py`、`tests/firestore-rules/rules.test.ts` |
| FR-27 服務台代填今日事務 | 前端後台代填分頁、R-RBAC、R-ORCH | `frontend/src/admin/__tests__/ProxyInputTab.test.tsx`、`functions/tests/rules/test_rbac.py`、`functions/tests/integration/test_api_plan.py` |
| FR-28 補充需求後重新規劃 | 前端 AI 對話頁、R-ORCH | `frontend/src/pages/__tests__/ChatPage.test.tsx`、`functions/tests/integration/test_api_plan.py` |
| NFR-01 模型(Claude Haiku)與備援 | A-CLIENT、R-DESK | `functions/tests/ai/test_claude_client.py`、`functions/tests/rules/test_service_desk.py` |
| NFR-02 網頁形式 | 前端、Hosting | `functions/tests/integration/test_hosting_smoke.py` |
| NFR-03 病人端 6 個畫面 | 前端路由 | `frontend/src/__tests__/routes.test.tsx` |
| NFR-04 只使用模擬資料 | A-CLIENT、匯入腳本 | `functions/tests/ai/test_claude_client.py`、`functions/tests/test_mock_data_only.py` |
| NFR-05 簡單樓層圖 | R-STATIC、前端醫院地圖頁 | `functions/tests/rules/test_static_data.py`、`frontend/src/pages/__tests__/MapPage.test.tsx` |
| P2 資料單向流動 | R-ORCH | `functions/tests/rules/test_plan_pipeline.py`(輸入雜湊不變、AI 輸出不寫入規則集合) |
| P4 提示詞為規格原文 | 提示詞檔 | `functions/tests/test_prompts_verbatim.py` |
| 後端健康檢查(Emulator 驗證用) | Flask app | `functions/tests/test_health.py` |
