# Spec Delta

## Purpose

限制 AI 只處理醫院就醫流程相關的問題，並規範模型部署位置與可送入模型的病人資料。

## ADDED Requirements

### Requirement: 不回覆無關問題
AI MUST NOT 回覆與醫院就醫流程無關的事。

#### Scenario: 詢問無關問題
- **WHEN** 使用者詢問與醫院就醫流程無關的問題
- **THEN** AI 不回答該問題，並引導使用者至櫃檯詢問

### Requirement: 不做診斷判斷
AI MUST NOT 對任何診斷下判斷。

#### Scenario: 詢問診斷
- **WHEN** 使用者詢問與診斷相關的問題
- **THEN** AI 不做判斷，並引導使用者至櫃檯詢問

### Requirement: 院內離線自架模型
系統 MUST 使用醫院內離線自架的模型。

#### Scenario: 呼叫模型
- **WHEN** 系統需要呼叫 LLM
- **THEN** 請求只送往醫院內自架的模型，不送往院外服務

### Requirement: 送入 LLM 的資料白名單
送入 LLM 的病人資料 MUST 僅限姓名、年齡、性別、無障礙需求，以及診斷人員給予的判斷(例如醫生要求之檢查醫囑)；其餘個人資料 MUST NOT 送入 LLM。醫囑由醫院當下站點的診斷者(例如診間醫師)提供。

#### Scenario: 組裝模型輸入
- **WHEN** 系統組裝送給 LLM 的病人資料
- **THEN** 內容只包含姓名、年齡、性別、無障礙需求與檢查醫囑等診斷人員判斷，不包含其他個人資料

#### Scenario: 有無障礙需求的使用者
- **WHEN** 使用者在初始化時表示有無障礙需求
- **THEN** 該需求被送入 LLM，作為判斷路線的依據
