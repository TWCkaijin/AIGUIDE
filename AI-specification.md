# 醫院通 — 以 AI 為核心的個人化智慧就醫引導系統｜規格書

> 第五組｜狀態：定稿(未決項目見文末「待確認事項」)
> 格式參照 OpenSpec：Requirement + Scenario(WHEN / THEN)。對應的 OpenSpec 變更位於 `openspec/changes/hospital-guide-mvp/`，已通過 `openspec validate --strict`。
> 本文件內容全部來自小組訪談回答；標記 ⚠️ 者為訪談者舉例、經小組同意採用；⏳ #n 對應文末「待確認事項」編號。

---

## 1. 臨床問題與照護價值

### 問題陳述
一般病患或家屬不熟悉醫院環境，造成就醫流程卡頓，或無法順利抵達要去的部門。

### Requirement R1.1 問題發生位置
就醫過程中，**站點與站點之間**的移動與銜接。

### Requirement R1.2 卡住的表現 ⚠️
包括但不限於：走錯樓層、在原地詢問他人、拿著單子不知道下一站是哪裡。

### Requirement R1.3 後果(使用者視角) ⚠️
過號、檢查時間延誤、多走冤枉路、到櫃台反覆詢問。

### [REQ-01-01] Requirement R1.4 醫院端期望
預測抵達時間、預測人流，並讓使用者追蹤掛號號碼，以減少非預期的等待時間。(原型階段為 mock，見 R7.3)

### Requirement R1.5 證據來源
親身經驗、預期行為、實際案例。⏳ #1

### Requirement R1.6 照護價值指標
- [REQ-01-02] 指標 A：使用者就醫流程的**平均完成時間**
  - 計時起點：使用者按下「開始導覽」，或每一個 stage 開始時
  - 計時終點：使用者抵達下一個站點時
- 指標 B：**必要步驟正確完成率** ⏳ #3
- 基準值與目標值 ⏳ #4

---

## 2. 使用者與使用者故事

### Requirement R2.1 主要使用者
初診病人、行動不便者、長者、陪診家屬(大部分就醫對象)。

### Requirement R2.2 排除對象
無明確排除對象。

### 其他角色
- **護理行政人員**：後台管理(US-2)
- **站點人員/站務人員**：登錄完成、核查(R3.6、R5.4)
- **各部門**：更新自身部門資訊(R5.2)

### [US-01] US-1 初診病人
身為**初診病人**，我想要**清楚知道就醫流程、路線規劃、當下指引**，以便**節省就醫時間及減少錯誤**。

#### [REQ-02-01] Scenario US-1-S1 抽血完成後的引導
- **WHEN** 初診病人完成抽血檢查
- **THEN** 系統引導使用者回到等候區域等待報告

### [US-02] US-2 護理行政人員
身為**護理行政人員**，我想要**使用後台管理資料庫及模型設定**，以便**針對系統進行管理、利用系統減輕護理人員負擔**。

---

## 3. 輸入與輸出

### 輸入

#### [REQ-03-01] Requirement R3.1 病人基本資料
使用者於前端登入並送出請求後，由後端從**個人健保資料**或**醫院資料庫**提取。欄位包含但不限於：姓名、年齡、是否初診、行動能力、語言 ⚠️。⏳ #5、#6

#### [REQ-03-02] Requirement R3.2 今日到院預辦事務
使用者透過系統以**簡短文字**說明。

#### [REQ-03-03] Requirement R3.3 登入身分
- 本人：身分證字號、健保卡
- 陪診家屬：使用欲就醫者(病人本人)之個人資料

#### [REQ-03-04] Requirement R3.5 即時資料來源
到站後預計等候時間、目前叫號，透過**串接醫院叫號系統**取得。⏳ #7

#### [REQ-03-05] Requirement R3.6 站點完成判定
由**站點人員**在病人完成該站後登錄，醫院系統自動同步。

#### [REQ-03-06] Requirement R6.6 無障礙需求(見第 6 章)
使用者初始化時詢問是否有無障礙需求。

#### [REQ-03-07] 醫囑(見 R6.5)
醫生要求之檢查醫囑。來源：醫院當下站點的診斷者，例如診間醫師。

### 輸出
[REQ-03-08] 目的地、路線、時間、流程。

#### [REQ-03-09] Requirement R3.4 時間類輸出(暫定)
- (a) 走到下一站需要多久
- (b) 到站後預計要等多久
- (c) 掛號號碼目前叫到幾號
- (d) 整趟就醫預計多久完成

---

## 4. AI 任務適切性

### [REQ-04-01] 必須每次一致(靜態資料)
各部門的定位、就醫流程等。

### 交給 AI 的任務與理由
| 任務 | 為何需要 AI(小組說法) |
|---|---|
| R4.1 判斷途徑(下一站) | 流程對照表一般使用者不一定看得懂，且可能有臨時變動(位置等) |
| R4.2 路程 | 普通用戶可直接使用演算法，但部分使用者需求不同，例如需要無障礙設施 |
| R4.3 理解使用者需求 | 一般程式無法正確理解人類語意，需透過 LLM 理解語意並進行工具調用 |

### [REQ-04-02] Requirement R4.4 決策分工
由 **LLM 自己判斷下一站與路線**；詳細規則透過 Context 引導，並使用 tool 限制功能。

### [REQ-04-03] Requirement R4.5 流程依賴限制
醫院流程有指定的依賴，LLM 產生的任務流程**不得牴觸**該依賴。

#### Scenario R4.5-S1
- **WHEN** LLM 安排「領藥」，但「領藥」依賴「批價」且批價尚未完成
- **THEN** 不得讓病人先進行領藥

### [REQ-04-04] Requirement R4.6 輸出檢查
由檢查者比對 LLM 輸出是否違反依賴；檢查者可為**獨立的專用 Agent(依靠提示詞及 Context)**或 **RuleBase 規則**。⏳ #8

#### Scenario R4.6-S1
- **WHEN** 檢查者判定輸出違反依賴
- **THEN** 要求 LLM 重新產生，並記錄為系統錯誤

---

## 5. 流程與人工介入

### [REQ-05-01] Requirement R5.1 重試上限與人工接手
#### Scenario R5.1-S1
- **WHEN** LLM 重新產生 **3 次**仍持續違反依賴
- **THEN** 系統引導使用者至**櫃檯**

### [REQ-05-02] Requirement R5.2 臨時變動的更新者
各部門更新各部門的資訊，或由護理行政人員進行資料維護。⏳ #9

### [REQ-05-03] Requirement R5.3 受影響使用者的處理
使用者開始路線時需註冊到系統，後台藉此建立與前端的使用者連結。
#### Scenario R5.3-S1
- **WHEN** 路線或站點因臨時變動受到影響
- **THEN** 系統第一時間通知受影響使用者，並建議更改路線

### [REQ-05-04] Requirement R5.4 站點核查
病人抵達下一站時，站點人員核查：病人走對站點、前一站已完成。
#### Scenario R5.4-S1
- **WHEN** 核查發現病人走錯站
- **THEN** 系統不執行任何動作，由站務人員引導回正確站點

### 人工確認點總覽
| 時機 | 由誰 |
|---|---|
| 建構前輸入流程與地形圖 | (專案卡所列)⏳ #19 |
| 站點完成登錄、下站核查 | 站點人員 |
| 臨時變動更新 | 各部門/護理行政人員 |
| 重試 3 次失敗 | 櫃檯 |
| 診斷或無關問題 | 櫃檯 |
| 求助通報 | 院內人員 |
| 模型設定變更 | 簽核者 |

---

## 6. 提示詞與倫理風險

### [REQ-06-01] Requirement R6.1 AI 禁止事項(寫入提示詞)
- 不可回覆與醫院就醫流程無關的事
- 不下任何對於診斷的判斷
#### Scenario R6.1-S1
- **WHEN** 使用者詢問診斷或與就醫流程無關的問題
- **THEN** AI 不作答，引導至櫃檯詢問

### [REQ-06-02] Requirement R6.2 疑似緊急狀況
#### Scenario R6.2-S1
- **WHEN** 系統判斷使用者可能為緊急狀況 ⏳ #10
- **THEN** 彈出「我需要求助」按鈕 ⏳ #12
#### Scenario R6.2-S2
- **WHEN** 使用者按下「我需要求助」
- **THEN** 直接通報院內人員使用者**地點**及**使用者特徵**，並引導使用者到附近顯眼地標 ⏳ #11

### [REQ-06-03] Requirement R6.3 身分保護
- 手機簡訊認證 ⏳ #13
- 僅能在院內使用 ⏳ #14
- 只顯示今日行程，不顯示病歷

### [REQ-06-04] Requirement R6.4 模型部署
使用**醫院內離線自架模型**。

### [REQ-06-05] Requirement R6.5 送入 LLM 的資料(白名單)
- 姓名、年齡、性別
- 診斷人員給予的判斷，例如醫生要求之檢查醫囑
- 無障礙需求(R6.6 初始化時收集)
- **其餘個人資料皆不應送進 LLM**

### [REQ-06-06] Requirement R6.7 模型設定變更管理
- 更改後需**簽核**方可套用
- 所有修改版本紀錄皆應保留
- 可修改項目 ⏳ #17

---

## 7. 原型介面與範圍

### [REQ-07-01] Requirement R7.1 原型形式
網頁。

### [REQ-07-02] Requirement R7.2 原型畫面
1. 登入頁
2. 使用者資訊頁面
3. AI 對話頁面
4. 今日行程頁面
5. 醫院地圖
6. 就醫導覽資料

⏳ #18

### [REQ-07-03] Requirement R7.3 原型範圍
| 項目 | 決定 |
|---|---|
| a. 串接健保/醫院資料庫(R3.1) | mock |
| b. 串接醫院叫號系統(R3.5) | mock |
| c. 預測抵達時間與人流(R1.4) | mock |
| d. 站點人員登錄完成(R3.6) | mock |
| e. LLM 判斷下一站與路線 + 檢查者 + 重試 3 次(R4.4–R5.1) | 做 |
| f. 臨時變動即時通知(R5.3) | 做 |
| g. 「我需要求助」按鈕與通報(R6.2) | 做 |
| h. 簡訊認證與院內限定(R6.3) | mock |
| i. 護理行政後台 + 簽核 + 版本紀錄(R6.7) | 做 |

---

## 8. 參考文獻

依小組提供之清單照錄(訪談者未查證、未增補)：

1. 衛生福利部國民健康署(2019)。Health Literacy(健康識能)。
2. Navigational Needs and Preferences of Hospital Patients and Visitors: What Prospects for Smart Technologies? (2021).
3. Salins PL, Anandan G, Ananda BD, Reshmi B, Jathanna RD. Internet of Things-Based Wayfinding for Hospital Visitors: A Digital Solution for Complex Health Care Infrastructures. Mayo Clin Proc Digit Health. 2025 Oct 8;3(4):100293. doi: 10.1016/j.mcpdig.2025.100293. PMID: 41245354; PMCID: PMC12613019.
4. World Health Organization. Ethics and governance of artificial intelligence for health: Guidance on large multi-modal models (2024).
5. Li X, Liu W, Kong W, Zhao W, Wang H, Tian D, Jiao J, Yu Z, Liu S. Prediction of outpatient waiting time: using machine learning in a tertiary children's hospital. Transl Pediatr. 2023 Nov 28;12(11):2030-2043. doi: 10.21037/tp-23-58. Epub 2023 Nov 23. PMID: 38130586; PMCID: PMC10730972.
6. Salins P, Anandan G, Ananda B, Internet of Things-Based Wayfinding for Hospital Visitors: A Digital Solution for Complex Health Care Infrastructures. Mayo Clinic Proceedings: Digital Health, 2025; 3
7. Shahul Es, Jithin James, Luis Espinosa Anke, and Steven Schockaert. 2024. RAGAs: Automated Evaluation of Retrieval Augmented Generation. In Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations, pages 150–158, St. Julians, Malta. Association for Computational Linguistics.

⏳ #20、#21、#22

---
## 待確認事項

編號沿用訪談時的編號(#2、#15、#16 已確認並寫入本文，故不列出)。

| # | 章節 | 項目 |
|---|---|---|
| 1 | 1 | 具體實際案例與證據來源(R1.5) |
| 3 | 1 | 指標 B「必要步驟」包含哪些、「正確完成」如何判定 |
| 4 | 1 | 兩項指標的基準值與目標值 |
| 5 | 3 | 病人基本資料完整欄位清單與各欄位用途(目前為「包含但不限於」，且部分欄位來自訪談者舉例) |
| 6 | 3/6 | 從健保/醫院資料庫取資料的授權依據與介接方式 |
| 7 | 3 | 步行時間(a)與整趟預估時間(d)的資料來源與計算方式 |
| 8 | 4 | 檢查者採專用 Agent、RuleBase 規則，或兩者並用 |
| 9 | 5 | 各部門更新資訊是否需護理行政審核後才生效 |
| 10 | 6 | 如何判斷「可能為緊急狀況」及其依據 |
| 11 | 6 | 「使用者特徵」包含哪些資料、來源；使用者位置如何取得 |
| 12 | 6 | 求助按鈕是否應常駐於所有畫面 |
| 13 | 6 | 簡訊寄送對象；陪診家屬未持病人手機時如何認證 |
| 14 | 6 | 「僅能院內使用」的實作方式 |
| 17 | 6 | 「模型設定」可修改的具體項目清單 |
| 18 | 7 | 護理行政後台(第 i 項要做)與求助通報接收端的畫面清單 |
| 19 | 5 | 「建構前輸入流程與地形圖」由誰負責、如何確認 |
| 20 | 8 | 第 3 與第 6 篇為同一篇文獻的重複條目，需合併 |
| 21 | 8 | 第 1、2、4 篇缺作者/出處/網址等完整書目資訊 |
| 22 | 8 | 各文獻分別支持本規格哪一條需求(尚未對應) |
| 23 | 1 | 指標 A 依計時定義僅量測站點間移動時間：「平均」是否為各段移動時間的平均，以及指標名稱是否需調整 |
| 24 | 3/6 | 醫囑如何進入醫院通(由醫院系統同步，或由診斷者直接在醫院通輸入) |
