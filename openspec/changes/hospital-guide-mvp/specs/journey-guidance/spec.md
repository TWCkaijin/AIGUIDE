# Spec Delta

## Purpose

依病人今日到院事務，由 LLM 規劃下一站與路線，並確保結果不違反醫院既定的流程依賴。

## ADDED Requirements

### Requirement: LLM 判斷下一站與路線
系統 SHALL 由 LLM 判斷使用者的下一站與路線；詳細規則透過 Context 引導，並以 tool 限制 LLM 可用的功能。

#### Scenario: 規劃今日行程
- **WHEN** 使用者送出今日到院預辦事務
- **THEN** 系統輸出目的地、路線與流程

### Requirement: 完成站點後引導至下一處
系統 SHALL 在使用者完成某一站後，引導使用者前往下一處。

#### Scenario: 抽血完成後的引導
- **WHEN** 初診病人完成抽血檢查
- **THEN** 系統引導使用者回到等候區域等待報告

### Requirement: 靜態資料一致
各部門定位與就醫流程等靜態資料 MUST 每次輸出都一致。

#### Scenario: 重複查詢同一部門
- **WHEN** 使用者在不同時間查詢同一部門位置，且期間無臨時變動
- **THEN** 系統每次回傳相同的部門位置

### Requirement: 不得牴觸流程依賴
LLM 產生的任務流程 MUST NOT 牴觸醫院指定的流程依賴。

#### Scenario: 領藥依賴批價
- **WHEN** 「領藥」依賴「批價」且批價尚未完成
- **THEN** 系統不得讓病人先進行領藥

### Requirement: 輸出檢查與重新產生
系統 MUST 由檢查者比對 LLM 輸出是否違反流程依賴；違反時 MUST 要求重新產生並記錄為系統錯誤。(檢查者採專用 Agent 或 RuleBase 規則，待確認 #8)

#### Scenario: 檢查發現違規
- **WHEN** 檢查者判定 LLM 輸出違反流程依賴
- **THEN** 系統要求 LLM 重新產生，並記錄一筆系統錯誤

### Requirement: 重試上限與轉介櫃檯
LLM 重新產生 3 次仍違規時，系統 MUST 停止重試並引導使用者至櫃檯。

#### Scenario: 連續 3 次違規
- **WHEN** LLM 重新產生 3 次後輸出仍違反流程依賴
- **THEN** 系統引導使用者至櫃檯
