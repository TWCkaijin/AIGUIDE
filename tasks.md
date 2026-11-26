# tasks.md — 任務清單

> 依據：`design.md`(模組)與 `test-cases.md`(案例)。每個模組都是「先寫測試 → 跑一次看到失敗 → 實作 → 再跑測試」。
> 規則只能引用 `decisions.md`；文件沒寫清楚的地方，停下來詢問小組。
> 每完成一個階段：在本檔打勾、寫 DEVLOG、git commit(CLAUDE.md 第 6 條)。

## 已完成(文件與骨架階段)

- [x] 將規格書逐節轉成 AI-specification.md，加上 [REQ-章節-序號] 與 [US-xx] 編號
- [x] 依 AI-specification.md 產出 requirements.md(FR、AC、MVP 範圍、待釐清事項)
- [x] 逐題釐清 requirements.md 待釐清事項 Q-01～Q-19，寫入 decisions.md(D-001～D-019)
- [x] 依 decisions.md(D-001～D-019)更新 requirements.md
- [x] 為 decisions.md 的 D-005、D-006、D-009、D-012、D-013、D-014、D-018、D-019 補上暫定假設
- [x] 補齊 requirements.md 的 Q-20～Q-34 暫定假設並對應 decisions.md
- [x] 原型線上模型改為 Claude API Haiku(claude-haiku-5-5)
- [x] 將 decisions.md 的暫定假設與 Q-34 決定整併進 requirements.md 的 AC
- [x] 將第二輪(Q-20～Q-34)暫定假設轉為確定決策，並整併進 requirements.md
- [x] 產出 design.md(規則／AI 模組劃分、單向資料流、輸出檢查、備援、技術架構、需求→模組→測試對照表)
- [x] 建立提示詞檔(規格原文)：functions/prompts/planner.system.md、checker.system.md、SOURCES.md
- [x] 建立 Firebase emulators 設定、Flask 後端骨架與 Vite React 前端骨架，並以 emulators:exec 煙霧測試驗證
- [x] 逐題釐清 design.md 設計待決事項 DD-01～DD-07(D-020～D-025)
- [x] 產出模擬資料草稿(mock_data_draft/，D-024、D-025)與一致性檢查腳本
- [x] 依 requirements.md 與 decisions.md 產出 test-cases.md(140 案例、8 項待確認 TQ)
- [x] 逐題釐清 test-cases.md 待確認事項 TQ-01～TQ-08(D-026～D-036)，同步 requirements／design／test-cases
- [x] 依 design.md 與 test-cases.md 產出本分階段任務清單

---

## 階段 1：不依賴醫院資料的規則核心

| 模組 | 測試檔 | 對應案例 |
|---|---|---|
| R-WL 白名單 | `functions/tests/rules/test_whitelist.py` | TC-WL-01～04、TC-DATA-01、TC-BAD-02 |
| R-GUARD 輸出檢查 | `functions/tests/rules/test_output_guard.py` | TC-GUARD-01～04、TC-ROUTE-02／03／08、TC-SCOPE-03、TC-BAD-04、TC-AIF-02／03、TC-PROP-F1～F6、M1～M3、N1～N4 |
| R-METRIC 成效指標 | `functions/tests/rules/test_metrics.py` | TC-MET-01～11 |

- [x] 1.1 寫 R-WL 測試
- [x] 1.2 寫 R-GUARD 測試
- [x] 1.3 寫 R-METRIC 測試
- [x] 1.4 執行測試，確認失敗
- [x] 1.5 實作 R-WL
- [x] 1.6 實作 R-GUARD
- [x] 1.7 實作 R-METRIC
- [x] 1.8 執行測試，確認通過

## 階段 2：規劃流程控制與模型呼叫介面

| 模組 | 測試檔 | 對應案例 |
|---|---|---|
| R-ORCH 規劃流程控制 | `functions/tests/rules/test_plan_pipeline.py` | TC-GUARD-05、TC-RETRY-01～06、TC-CHK-01～05、TC-AIF-01～09、TC-BAD-05、TC-PROP-N6 |
| A-CLIENT 模型呼叫介面(含假客戶端) | `functions/tests/ai/test_claude_client.py` | TC-AIF-01～04、AC-NFR01.2、TC-WL-01 |

- [ ] 2.1 寫 R-ORCH 測試(以假的 AI 客戶端與假的服務台備援注入)
- [ ] 2.2 寫 A-CLIENT 介面測試(不呼叫真實 API)
- [ ] 2.3 執行測試，確認失敗
- [ ] 2.4 實作 R-ORCH
- [ ] 2.5 實作 A-CLIENT 介面與假客戶端
- [ ] 2.6 執行測試，確認通過

## 階段 3：示範草案模式(AI 未接上真實金鑰前)

> 需求來源：小組指示「AI 還沒接上真的金鑰之前，提供『載入示範草案』的功能，讓我可以先驗收審查與確認的流程」。開始前需先確認細節(見下方「開始前待確認」)，並先寫進 decisions.md 與 design.md。

- [ ] 3.0 釐清示範草案的細節，寫入 decisions.md、design.md
- [ ] 3.1 寫示範草案模式的測試
- [ ] 3.2 執行測試，確認失敗
- [ ] 3.3 實作示範草案模式
- [ ] 3.4 執行測試，確認通過

## 階段 4：依賴醫院資料的規則

> 前提：測試資料來源需先確認(見「開始前待確認」)。

| 模組 | 測試檔 | 對應案例 |
|---|---|---|
| R-STATIC 靜態資料 | `functions/tests/rules/test_static_data.py` | TC-VER-01、TC-CAND-07 |
| R-CAND 下一站候選 | `functions/tests/rules/test_candidates.py` | TC-EX-01、TC-CAND-01～07 |
| R-ROUTE 路線檢查 | `functions/tests/rules/test_route_check.py` | TC-ROUTE-01～08、TC-DATA-01 |
| R-DEP 依賴檢查 | `functions/tests/rules/test_dependency_checker.py` | TC-EX-01、TC-CAND-05／06 |
| R-DESK 服務台備援 | `functions/tests/rules/test_service_desk.py` | TC-DESK-01～09、TC-SCOPE-01 |

- [ ] 4.1 寫 R-STATIC、R-CAND、R-ROUTE、R-DEP、R-DESK 測試
- [ ] 4.2 執行測試，確認失敗
- [ ] 4.3 實作 R-STATIC、R-CAND、R-ROUTE、R-DEP、R-DESK
- [ ] 4.4 執行測試，確認通過

## 階段 5：進度、版本、通知與影響

| 模組 | 測試檔 | 對應案例 |
|---|---|---|
| R-PROGRESS | `functions/tests/rules/test_progress.py` | TC-ORD-01～04、TC-DATA-08 |
| R-VERSION | `functions/tests/rules/test_versioning.py` | TC-VER-02～04、TC-REV-01～07、TC-SET-01～05 |
| R-NOTIFY | `functions/tests/rules/test_notify.py` | TC-ORD-01／02、TC-IMP-05 |
| R-IMPACT | `functions/tests/rules/test_impact.py` | TC-IMP-01～05 |
| R-QUEUE | `functions/tests/rules/test_queue_mock.py` | TC-TIME-03、TC-DATA-03、TC-DATA-10 |

- [ ] 5.1 寫測試
- [ ] 5.2 執行測試，確認失敗
- [ ] 5.3 實作
- [ ] 5.4 執行測試，確認通過

## 階段 6：登入、權限與求助

| 模組 | 測試檔 | 對應案例 |
|---|---|---|
| R-AUTH | `functions/tests/rules/test_auth_mock.py` | TC-AUTH-01～07 |
| R-RBAC | `functions/tests/rules/test_rbac.py` | TC-REV-02、TC-SET-02、TC-PROXY-03、TC-ORD-03 |
| R-HELP | `functions/tests/rules/test_help_alert.py` | TC-HELP-02～05 |
| Firestore 規則 | `tests/firestore-rules/rules.test.ts` | TC-TIME-05、FR-26 |

- [ ] 6.1 寫測試
- [ ] 6.2 執行測試，確認失敗
- [ ] 6.3 實作
- [ ] 6.4 執行測試，確認通過

## 階段 7：AI 模組接上 Claude API

> 前提：小組提供 `ANTHROPIC_API_KEY`(放在 `functions/.secret.local`)。

| 模組 | 測試檔 | 對應案例 |
|---|---|---|
| A-PLAN | `functions/tests/ai/test_planner.py` | TC-TIME-01～04、TC-HELP-05、TC-SCOPE-01～03 |
| A-CHECK | `functions/tests/ai/test_agent_checker.py` | TC-CHK-02～04 |

- [ ] 7.1 寫測試(以錄製或假的回應為主，真實呼叫只做煙霧測試)
- [ ] 7.2 執行測試，確認失敗
- [ ] 7.3 實作
- [ ] 7.4 執行測試，確認通過

## 階段 8：後端 API 與 Emulator 整合

| 範圍 | 測試檔 | 對應案例 |
|---|---|---|
| 規劃、進度、變更流程 API | `functions/tests/integration/test_api_plan.py`、`test_api_progress.py`、`test_api_change_flow.py` | TC-DATA-02／06／07／09、TC-PROXY-01／02、TC-REJ-04／06～08 |
| Hosting 煙霧測試 | `functions/tests/integration/test_hosting_smoke.py` | NFR-02 |

- [ ] 8.1 寫整合測試
- [ ] 8.2 執行測試，確認失敗
- [ ] 8.3 實作 Flask 路由與 Firestore 存取
- [ ] 8.4 執行測試，確認通過

## 階段 9：前端(病人端 6 個畫面與後台)

| 範圍 | 測試檔 | 對應案例 |
|---|---|---|
| 病人端 | `frontend/src/pages/__tests__/*.test.tsx`、`frontend/src/__tests__/routes.test.tsx` | NFR-03、TC-TIME-01～03、TC-HELP-01、TC-PROP-M4／M5 |
| 後台 | `frontend/src/admin/__tests__/*.test.tsx` | FR-26、FR-27、TC-PROXY-03 |

- [ ] 9.1 寫前端測試(Vitest + React Testing Library)
- [ ] 9.2 執行測試，確認失敗
- [ ] 9.3 實作
- [ ] 9.4 執行測試，確認通過

## 階段 10：端到端驗收

- [ ] 10.1 以模擬病人跑完 TC-EX-01 全流程(Emulator)
- [ ] 10.2 依 test-cases.md 第 7 節性質，人工抽查 AI 說明文字(D-022)

---

## 開始前待確認

| 編號 | 階段 | 問題 |
|---|---|---|
| TK-01 | 3 | 「載入示範草案」的細節：示範草案的內容從哪裡來、由誰在哪個畫面載入、要驗收的「審查與確認流程」是指哪一段 |
| TK-02 | 4 以後 | 自動化測試的醫院資料來源：`mock_data_draft/` 尚未經小組核對(D-019)，而且不進版控；測試要用什麼資料 |
