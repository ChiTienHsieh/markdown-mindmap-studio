# Markdown Mindmap Studio

> 以 Markdown 檔案作為單一資料來源的互動式心智圖編輯器

[English](README.md) | 繁體中文

## 特色功能

- **Markdown 為本**: 所有內容以純文字 Markdown 檔案儲存
- **互動式心智圖**: 使用 Markmap.js 呈現視覺化樹狀圖
- **雙向編輯**: 編輯 Markdown 或點擊節點皆可更新內容
- **即時同步**: 基於 WebSocket 的即時更新
- **AI 助手**: 可選的 Claude Agent 整合，輔助編輯
- **匯出功能**: 產生獨立的 HTML 心智圖及 PDF 文件

## 快速開始

```bash
# Clone 專案
git clone https://github.com/ChiTienHsieh/markdown-mindmap-studio.git
cd markdown-mindmap-studio

# 安裝相依套件
uv sync

# 啟動編輯器
uv run python editor/server.py
# 開啟 http://localhost:3000
```

## 專案結構

```
markdown-mindmap-studio/
├── mindmap/                 # 你的內容 (巢狀目錄 + content.md)
│   ├── 01_topic/
│   │   ├── content.md       # 主題內容
│   │   ├── subtopic_a/
│   │   │   └── content.md
│   │   └── subtopic_b/
│   │       └── content.md
│   └── 02_another_topic/
│       └── ...
├── editor/                  # 網頁編輯器 (FastAPI + vanilla JS)
│   ├── server.py
│   └── static/
├── scripts/                 # 匯出工具
│   └── export_mindmap.py
└── exports/                 # 產生的 HTML/PDF 檔案
```

## 自訂設定

詳見 [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md)：
- 修改專案標題和模組名稱
- 新增模組
- 自訂 AI 助手
- 語言/地區設定

## 匯出

```bash
# 產生 HTML 心智圖和 PDF
uv run python scripts/export_mindmap.py
```

## 授權條款

MIT
