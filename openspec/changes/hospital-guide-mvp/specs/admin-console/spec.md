# Spec Delta

## Purpose

讓護理行政人員透過後台管理資料庫與模型設定，並以簽核與版本紀錄控管變更風險。

## ADDED Requirements

### Requirement: 後台管理
護理行政人員 SHALL 能使用後台管理資料庫及模型設定。(可修改項目待確認 #17；後台畫面待確認 #18)

#### Scenario: 進入後台
- **WHEN** 護理行政人員登入後台
- **THEN** 可檢視並編輯資料庫資料與模型設定

### Requirement: 設定變更需簽核
模型設定更改後 MUST 經簽核方可套用。

#### Scenario: 未簽核的變更
- **WHEN** 護理行政人員送出模型設定變更但尚未簽核
- **THEN** 系統繼續使用原本的設定

### Requirement: 保留所有版本紀錄
系統 MUST 保留所有模型設定的修改版本紀錄。

#### Scenario: 查看歷史
- **WHEN** 模型設定經過多次修改
- **THEN** 後台可查到每一個修改版本的紀錄
