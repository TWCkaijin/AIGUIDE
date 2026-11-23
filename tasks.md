# tasks.md — 任務清單

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
