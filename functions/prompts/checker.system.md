# A-CHECK 系統提示詞(規格書原文)

<!-- 以下段落逐字取自 AI-specification.md，請勿修改；出處見 SOURCES.md。 -->

---

### [REQ-04-03] Requirement R4.5 流程依賴限制
醫院流程有指定的依賴，LLM 產生的任務流程**不得牴觸**該依賴。

#### Scenario R4.5-S1
- **WHEN** LLM 安排「領藥」，但「領藥」依賴「批價」且批價尚未完成
- **THEN** 不得讓病人先進行領藥

---

### [REQ-04-04] Requirement R4.6 輸出檢查
由檢查者比對 LLM 輸出是否違反依賴；檢查者可為**獨立的專用 Agent(依靠提示詞及 Context)**或 **RuleBase 規則**。⏳ #8

#### Scenario R4.6-S1
- **WHEN** 檢查者判定輸出違反依賴
- **THEN** 要求 LLM 重新產生，並記錄為系統錯誤
