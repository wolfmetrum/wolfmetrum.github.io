# 狼的格律 Wolf Metrum

「讓未馴的靈魂，臣服於恩典的格律。」

展示與收錄 [狼的格律 Wolf Metrum](https://www.youtube.com/@WolfMetrumRs) YouTube 頻道曲目的網站：<https://wolfmetrum.github.io/>

以 Jekyll（GitHub Pages，`jekyll-theme-primer`）建置，沒有額外的建置步驟，推上 `main` 就會自動發布。

## 專案結構

| 路徑 | 說明 |
|---|---|
| `index.html` | 唯一的頁面：播放器、篩選標籤、歌曲目錄（Liquid 產生列表，JS 處理播放與篩選） |
| `_data/songs.yml` | 曲目資料，網站內容的唯一來源 |
| `_config.yml` | 網站設定，含 `youtube_channel_id` |
| `assets/sheets/` | 樂譜 PDF |
| `assets/images/` | Logo |
| `scripts/sync_youtube.py` | 從 YouTube 同步新曲目的腳本 |
| `.github/workflows/sync-youtube.yml` | 每週自動執行同步 |
| `wolfeyeqrscanner_privacy.md` | 其他專案暫放的隱私權政策，與本站無關 |
| `_layouts/song.html` | 目前未使用 |

## 新增曲目

### 自動（建議）

GitHub Action 每週一（台灣時間 09:00）會抓頻道新影片，讀取描述中的資訊區塊，開一個 Pull Request 加到 `songs.yml`。也可以到 Actions 頁面手動執行 **Sync YouTube songs**。

影片描述請放入以下區塊：

```
🎵 【作品與版權資訊】
• 曲名：
• 作曲：
• 作詞：
• 收錄：
• 標籤：
• 鋼琴編曲／演奏／混音：狼的格律（Wolf Metrum）
• 調性：(移調)E-Minor
```

- 曲名、作曲、作詞、標籤依欄位名稱讀取。
- **第 4 列固定當作「備註」**，欄位名稱叫什麼都可以。
- 標籤可用 `、` `,` `，` 分隔。
- 最後兩列（編曲與調性）不會顯示；調性若以 `(移調)` 開頭，該曲會標為 `dontplay: true`（不加入「播放全部」）。
- 移調版的曲名請直接寫成 `感謝神(降3)` 這種形式。
- 欄位留空會略過。
- 沒有此區塊的影片，會改用標題《》內的文字當曲名，並在 PR 說明標出需要補欄位。

合併 PR 前請檢查內容；`sheet_music` 無法自動帶入，需要的話手動補上。

**一次性設定**（Settings 內）：

1. Secrets and variables → Actions → 新增 `YOUTUBE_API_KEY`（需限制為 YouTube Data API v3，不限制來源）。
2. Actions → General → 勾選「Allow GitHub Actions to create and approve pull requests」。

### 手動

在 `_data/songs.yml` 加一筆：

```yaml
- title: 曲名
  composer: 作曲
  lyricist: 作詞
  note: 備註（如 ©️讚美之泉、聖徒詩歌220）
  youtube_id: 影片ID
  sheet_music: /assets/sheets/檔名.pdf   # 選填
  tags: [傳統詩歌, 聖徒詩歌]
  dontplay: true                         # 選填，不加入「播放全部」（用於移調版）
```

- 標籤會自動變成篩選按鈕；`狼的格律原創`、`傳統詩歌`、`現代詩歌` 會決定曲名按鈕的配色。
- 樂譜 PDF 放在 `assets/sheets/`。

## 本機預覽

```bash
bundle exec jekyll serve
```

需要先安裝 Ruby 與 Jekyll（或使用 `github-pages` gem）。

## 開發慣例

- Commit 訊息請使用**英文**。
