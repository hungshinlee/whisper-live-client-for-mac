# 即時字幕浮動視窗

在簡報時顯示即時字幕，視窗會顯示在**全螢幕簡報上方**。

## 特色

- ✅ 即時語音辨識 / 翻譯成英文
- ✅ 浮動視窗，始終在最上層
- ✅ 支援全螢幕模式（Google Slides、PowerPoint、Keynote）
- ✅ 可拖動調整位置
- ✅ 使用 Apple Silicon GPU 加速
- ✅ 可自訂視窗大小、字體大小、顏色

## 設置

```bash
# 從專案根目錄進入 subtitle 目錄
cd subtitle

# 建立虛擬環境並安裝依賴
uv venv
uv pip install mlx-whisper pyaudio numpy pyobjc-framework-Cocoa
```

## 使用方式

```bash
# 基本使用（使用預設模型）
uv run python subtitle.py

# 翻譯成英文
uv run python subtitle.py --task translate

# 使用較小的模型（適合 M1/M2）
uv run python subtitle.py --model mlx-community/whisper-medium-mlx

# 指定語言
uv run python subtitle.py --language zh

# 列出可用模型
uv run python subtitle.py --list
```

## 參數說明

| 參數 | 簡寫 | 說明 | 預設值 |
|------|------|------|--------|
| `--model` | `-m` | 模型名稱（HF repo 或本地模型）| `whisper-large-v3-mlx` |
| `--task` | `-t` | `transcribe` 或 `translate` | `transcribe` |
| `--language` | `-l` | 語言代碼（zh, en, ja...）| 自動偵測 |
| `--list` | | 列出可用模型 | |

## 操作說明

1. 執行程式後，字幕視窗會出現在螢幕底部
2. **拖動**字幕視窗可移動位置
3. 開始全螢幕簡報
4. 對著麥克風說話，字幕會即時顯示
5. 按 **Ctrl+C** 關閉程式

## 自訂設定

編輯 `subtitle.py` 開頭的設定區塊：

### 視窗設定

```python
WINDOW_WIDTH_RATIO = 0.8      # 視窗寬度佔螢幕比例
WINDOW_HEIGHT = 100           # 視窗高度（像素）
WINDOW_BOTTOM_MARGIN = 50     # 距離螢幕底部的距離
WINDOW_OPACITY = 0.85         # 透明度（0.0~1.0）
```

### 文字設定

```python
FONT_SIZE = 48                # 字體大小
FONT_NAME = None              # 字體名稱，None 為系統預設
TEXT_COLOR = "white"          # 文字顏色：white/yellow/green/cyan
```

### 錄音設定

```python
SILENCE_THRESHOLD = 500       # 靜音門檻
SILENCE_DURATION = 1.2        # 靜音多久後結束錄音（秒）
```

## 常見調整

| 需求 | 修改 |
|------|------|
| 字更大 | `FONT_SIZE = 56` |
| 字更小 | `FONT_SIZE = 36` |
| 視窗更高 | `WINDOW_HEIGHT = 150` |
| 視窗更窄 | `WINDOW_WIDTH_RATIO = 0.6` |
| 黃色字幕 | `TEXT_COLOR = "yellow"` |
| 更透明 | `WINDOW_OPACITY = 0.7` |
| 環境吵雜 | `SILENCE_THRESHOLD = 800` |
| 說話較快 | `SILENCE_DURATION = 0.8` |

## 疑難排解

### 麥克風沒有反應

**系統設定** → **隱私與安全性** → **麥克風** → 勾選終端機

### 環境太吵

提高 `SILENCE_THRESHOLD`，例如 `800` 或 `1000`。

### 字幕更新太慢

降低 `SILENCE_DURATION`，例如 `0.8` 或 `1.0`。

### 模型太慢

使用較小的模型：
```bash
uv run python subtitle.py --model mlx-community/whisper-medium-mlx
```
