# 閱讀次數 API 驗收清單

- GET／POST 優先接受 `morning-YYYY-MM-DD` 或 `asia-close-YYYY-MM-DD`，並向下相容正式報告 path。
- Sample、首頁、404、路徑穿越、任意 SQL 字串與超長識別值必須回傳 400。
- POST 拒絕跨來源、過大或無效 JSON body；SQL 一律參數化，UPSERT 原子增加。
- Pages preview、本機環境與明顯爬蟲不增加正式計數。
- 前端以 localStorage 進行同一瀏覽器、同篇報告 24 小時去重；D1 為正式總數來源。
- batch 限制最多 100 個報告 id，首頁、歷史與搜尋使用單次批次取得，卡片顯示不增加計數。
- D1 未綁定或 API 失敗時顯示「閱讀 — 次」，不影響正文、搜尋、列印或分享。
- `0002_add_page_view_created_at.sql` 為既有 `page_views` 表補上建立時間，不建立重複資料表。
