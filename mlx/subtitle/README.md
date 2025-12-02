# 即時字幕浮動視窗

在簡報時顯示即時英文翻譯字幕，字幕視窗會顯示在**全螢幕簡報上方**。

## 特色

- ✅ 即時中文轉英文翻譯
- ✅ 浮動視窗，始終在最上層
- ✅ 支援全螢幕模式（Google Slides、PowerPoint、Keynote）
- ✅ 可拖動調整位置
- ✅ 使用 Apple Silicon GPU 加速

## 設置

```bash
cd /Users/winston/Projects/whisper-live-client/mlx/subtitle
uv venv
uv pip install mlx-whisper pyaudio numpy pyobjc-framework-Cocoa
```

## 使用方式

### 推薦：macOS 原生版（支援全螢幕）

```bash
uv run python floating_subtitle_native.py
```

這個版本使用 PyObjC，確保字幕視窗能顯示在全螢幕簡報上方。

### 備用：tkinter 版本

```bash
uv run python floating_subtitle.py
```

## 操作說明

1. 執行程式後，字幕視窗會出現在螢幕底部
2. **拖動**字幕視窗可移動位置
3. 開啟 Google Slides 並進入全螢幕簡報模式
4. 對著麥克風說中文，英文翻譯會即時顯示
5. 按 **Ctrl+C** 關閉程式

## 簡報流程建議

1. 先啟動字幕程式，等待模型載入完成
2. 調整字幕視窗位置到不會遮擋重要內容的地方
3. 開始 Google Slides 全螢幕簡報
4. 正常說話，字幕會自動顯示

## 注意事項

- 首次執行會下載約 3GB 的模型
- 使用 `whisper-large-v3` 模型（支援翻譯）
- 翻譯有約 1-2 秒的延遲
- 說完一句話後會顯示翻譯

## 疑難排解

### 字幕沒有顯示在全螢幕上方

請使用 `floating_subtitle_native.py` 版本，它使用 macOS 原生 API 確保視窗層級。

### 麥克風沒有反應

確認終端機有麥克風權限：
**系統設定** → **隱私與安全性** → **麥克風** → 勾選終端機

### 翻譯品質不佳

- 說話清晰、語速適中
- 減少背景噪音
- 每句話之間稍微停頓
