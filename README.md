# Asia Market Intelligence

繁體中文的全球市場晨報與亞洲股市收盤研究發布網站。專案採 HTML5、CSS3、Vanilla JavaScript、Python、GitHub Actions、Cloudflare Pages／Pages Functions 與 D1，不使用大型前端框架、傳統伺服器、Google Analytics、廣告追蹤或第三方 Cookie。

> 目前狀態：網站與發布流程已在本機完成；尚未建立 GitHub 遠端 Repository、Cloudflare Pages 專案與 D1，亦尚未完成自動內容上傳。`data/market-sample.json` 只作版面示意，不是即時行情。

## 架構與檔案

- 根目錄 HTML：首頁、晨報、收盤報、歷史、熱門、關於、隱私、離線與 404。
- `assets/`：共用響應式、深淺主題、列印、搜尋、分享、PWA 與閱讀次數前端。
- `reports/`：正式報告與明確標示的 Sample 版面頁；Sample 不進 `reports.json`、不計閱讀數。
- `incoming/`：待匯入報告；成功移至 `processed`、失敗移至 `failed`。
- `data/reports.json`：唯一公開報告索引；`site-config.json` 保存非秘密設定。
- `templates/`：晨報與亞洲收盤報 HTML 模板。
- `functions/api/`、`migrations/`：Pages Functions 與 D1 公開閱讀次數。
- `scripts/`、`tests/`：匯入、重建、驗證與測試。
- `.github/workflows/`：每日發布、驗證與手動重建工作流程。

## 本機預覽與驗證

不需要安裝 Git；只要 Python 3：

```bash
python scripts/validate-site.py
python -m unittest discover -s tests -v
python -m http.server 8000
```

瀏覽 `http://localhost:8000/`。若不想在本機安裝任何工具，可在 GitHub Codespaces 或 GitHub 網頁編輯器維護，並以 Actions 執行驗證。請勿只用 `file://` 驗證 fetch、Service Worker 或 API。

## 新增報告

正式 HTML 必須是 UTF-8、具完整 HTML 結構、足夠內容與免責聲明，且不可含 `TODO`、`PLACEHOLDER` 或 `SAMPLE ONLY`。

```bash
python scripts/add-report.py --type morning --date 2026-07-20 --title "全球新聞晨報" --summary "今日全球市場摘要" --source report.html
python scripts/add-report.py --type asia-close --date 2026-07-20 --title "亞洲股市收盤報" --summary "今日亞洲市場摘要" --source report.html
```

腳本會驗證、複製、備份既有檔、排序 `reports.json`，並更新 Sitemap 與 RSS。重複報告預設拒絕；確認覆蓋時才加 `--replace`。Word 僅可作下載／內部格式並填入 `wordFile`，不可直接當網頁；未提供時不顯示連結。

自動匯入：將 `YYYY-MM-DD.html` 放入 `incoming/morning/` 或 `incoming/asia-close/`。無檔案會正常顯示 `No report available for publication`；過期檔預設拒絕，人工核准才用 `--allow-past`。一份失敗不破壞其餘檔案。

## GitHub 與排程

建立公開 Repository `asia-market-intelligence`、預設分支 `main`，首次提交訊息為 `Initial launch of Asia Market Intelligence`。Repository 不可放 Token、Cookie、API Key、個人電子郵件、本機絕對路徑或其他秘密。

- 晨報：台北每日 08:45，UTC cron `45 0 * * *`。
- 亞洲收盤報：台北每日 16:00，UTC cron `0 8 * * *`。
- 兩者支援 Actions 頁面的 `Run workflow` 手動執行；選擇 `main` 後執行相應 workflow。
- 查看紀錄：Repository → Actions → 選 workflow 與 run。
- 暫停：Actions → 該 workflow → `Disable workflow`；恢復用 `Enable workflow`。不要停用舊內容任務，直到新流程兩個時段各成功至少兩次且內容核對、失敗紀錄與部署均正常。

Actions 只匯入可靠 HTML、驗證、重建、測試、commit 與 push，不負責憑空生成即時市場內容。內容生成層可日後接合法新聞／行情／OpenAI API；秘密只放 GitHub／Cloudflare Secrets，不放前端或儲存庫。

## 更新、失敗與回復

一般更新走分支與 Pull Request，通過 `Validate site` 後合併。失敗時先查看 Actions log；錯誤檔在 `incoming/failed/`，修正後重新放回來源資料夾。回復版本建議用 GitHub 的 Revert commit／Revert PR 建立可稽核反向提交；不要刪除歷史。匯入前備份存於本機 `.backups/`（被 Git 忽略）。變更網站名稱時同步調整 HTML metadata、`site-config.json`、manifest、RSS 與 README。

## Cloudflare Pages 部署

以 GitHub 官方整合連接 Repository：專案名 `asia-market-intelligence`、Production branch `main`、Framework preset `None`、Build command 留空、Root directory 為 repository root。純靜態專案通常不需 build output directory；應依當時 Pages 介面選擇「無建置／根目錄」，不要盲填 `/`。自動部署與 HTTPS 保持啟用，先使用免費 `pages.dev` URL；取得正式 URL 後才更新 `data/site-config.json` 的 `baseUrl` 並重建 RSS／Sitemap／canonical。

部署紀錄在 Cloudflare Dashboard → Workers & Pages → 專案 → Deployments。驗證首頁、CSS、JS、索引、正式報告、404、手機、HTTPS、Functions、D1、RSS、manifest 與離線頁。免費方案有執行、D1、建置與分析配額限制，應以 Cloudflare 當期官方說明為準。

## D1 與閱讀次數

建立 D1 `asia-market-intelligence-db`，Pages binding 必須命名 `DB`，再執行 `migrations/0001_create_page_views.sql`。`wrangler.toml` 刻意不填虛構 `database_id`。API 僅接受日期型正式報告路徑，使用參數化 SQL、同源與 body 限制；Sample、首頁、404、預覽、本機與明顯爬蟲不增加正式數。瀏覽器 localStorage 只做 30 分鐘去重，D1 才是總數來源。公開數字是近似值，不宣稱精準真人訪客。

備份 D1 前請先以 Cloudflare 官方匯出工具保存資料。重設計數屬破壞性操作，應先備份，再針對明確 path 執行參數化 `DELETE`／`UPDATE`，不可批次清空未確認資料。

## Web Analytics 與隱私

在正式 Pages 專案啟用 Cloudflare Web Analytics；查看 Page Views、Unique Visitors、熱門頁、來源、地區、裝置與 Core Web Vitals。本站不使用 Google Analytics 或第三方 Cookie，隱私說明見 `privacy.html`。目前 `analyticsEnabled` 為 `false`，尚未注入或虛構分析結果。

## RSS、PWA、分享與 PDF

- `feed.xml` 隨匯入重建；沒有 `baseUrl` 時保留相對連結，不填虛構 URL。
- PWA 使用版本化 Cache，只快取 GET 靜態資源／已讀頁；不快取 API POST，更新時清除舊 Cache。
- 分享使用 Web Share API 或複製網址，另提供 X、LinkedIn、Facebook 連結，不載入第三方追蹤 script。
- PDF 以瀏覽器列印／另存 PDF 與 A4 Print CSS 提供；未實作伺服器 PDF 生成。
- 熱門排行只讀 D1 batch API；D1 不可用時顯示空狀態，不使用假排行。

## 自訂網域、安全與已知限制

自訂網域尚未設定；部署穩定後在 Pages 的 Custom domains 依官方流程新增並驗證 DNS，再更新 `baseUrl`。`_headers` 提供 nosniff、Referrer、Permissions、X-Frame 與 CSP；正式部署後應以瀏覽器 Console 和安全掃描確認。電子郵件訂閱、AI 搜尋、自動內容生成、自動內容上傳、GitHub 遠端、Cloudflare Pages、D1、Web Analytics 與正式 URL目前均尚未完成。

常見問題：路徑錯誤通常來自報告不在兩層資料夾；RSS 無絕對 URL 是因 `baseUrl` 尚未設定；閱讀數空白表示 D1 未綁定；離線內容只保證曾成功快取的頁面。任何 OAuth、條款接受、Repository 選擇、D1 建立／綁定與部署確認都必須由帳戶本人完成，且不應在聊天或 issue 貼出秘密。
