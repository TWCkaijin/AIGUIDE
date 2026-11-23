# DEVLOG.md — 開發日誌

## 2026-11-23 — 規格書加上需求編號

- 在 AI-specification.md 的可驗證條文前加上 [REQ-章節-序號]，使用者故事加上 [US-xx]。
- 共 29 條 REQ(第 1 章 2、第 2 章 1、第 3 章 9、第 4 章 4、第 5 章 4、第 6 章 6、第 7 章 3)，2 則 US。
- 驗證：移除編號後與原規格書逐字相同，內容未增刪改寫。

## 2026-11-23 — 產出 requirements.md

- 依 AI-specification.md 整理出 25 條 FR、4 條 NFR、38 條 AC(Given/When/Then)，29 條 REQ 全部有對應。
- MVP 歸屬只依 [REQ-07-03] 判定；規格未標示歸屬的項目列入 Q-01。
- 列出 19 項待釐清事項(Q-01～Q-19)，其中 Q-02 為 REQ-04-02 與 REQ-04-01／CLAUDE.md 第 4 條的衝突。
