# 閱讀次數 API 測試清單

- GET 僅接受 `/reports/morning/YYYY-MM-DD.html` 與 `/reports/asia-close/YYYY-MM-DD.html`。
- Sample、首頁、404、路徑穿越與超長 path 必須回傳 400。
- POST 拒絕跨來源、過大或無效 JSON body；SQL 一律參數化。
- Pages 預覽、本機環境與明顯爬蟲不增加計數。
- 前端以 localStorage 進行同頁 30 分鐘去重；D1 為正式總數來源。
- batch 限制最多 100 個 path，D1 未綁定時回傳 503，頁面顯示空狀態。
- API 失敗不影響報告正文、搜尋、列印或分享。
