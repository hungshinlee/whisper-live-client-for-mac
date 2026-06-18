# Whisper Live Client for Mac

專為 Apple Silicon Mac 設計的即時語音轉文字工具。使用 MLX 框架讓 Whisper 模型在本地 GPU 上執行，搭配 Silero VAD 偵測語音段落，完全離線、延遲極低。支援轉錄與翻譯成英文，辨識結果自動轉換為臺灣繁體中文，並提供可浮在全螢幕上方的即時字幕視窗，適合簡報使用。

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black?logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![MLX](https://img.shields.io/badge/MLX-Framework-FF6B00?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyeiIvPjwvc3ZnPg==)
![License](https://img.shields.io/badge/license-MIT-22c55e)

---

## 目錄

- [功能特色](#功能特色)
- [系統需求](#系統需求)
- [快速開始](#快速開始)
- [參數說明](#參數說明)
- [自動簡繁轉換](#自動簡繁轉換)
- [浮動字幕視窗](#浮動字幕視窗)
- [擴展漢字支援](#擴展漢字支援)
- [模型選擇建議](#模型選擇建議)
- [轉換自訂模型](#轉換自訂模型)
- [疑難排解](#疑難排解)
- [目錄結構](#目錄結構)
- [授權](#授權)

---

## 功能特色

- 即時語音轉文字（Transcribe）
- 即時語音翻譯成英文（Translate）
- Apple Silicon GPU 加速（MLX 框架）
- **自動轉換成臺灣繁體中文**（使用 mlx-community 模型時）
- 支援 HuggingFace 上的任何 Whisper 模型
- **浮動字幕視窗** — 適用於全螢幕簡報（Google Slides、Keynote 等）
- **多螢幕支援** — 可指定字幕顯示在哪個螢幕

---

## 系統需求

- macOS（Apple Silicon：M1 / M2 / M3 / M4）
- Python 3.10+

---

## 快速開始

### 1. 安裝系統依賴

需要 [Homebrew](https://brew.sh)、[uv](https://github.com/astral-sh/uv)，以及音訊相關套件：

```bash
brew install uv ffmpeg portaudio
```

<details>
<summary>還沒安裝 Homebrew？展開查看</summary>

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安裝完後，依終端機指示將 Homebrew 加入 PATH：

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

</details>

### 2. 下載專案並安裝相依套件

```bash
git clone https://github.com/hungshinlee/whisper-live-client-for-mac.git
cd whisper-live-client-for-mac
uv venv
uv pip install mlx-whisper pyaudio numpy pyobjc-framework-Cocoa pysilero-vad opencc-python-reimplemented
```

### 3. 開始使用

```bash
# 最簡單：直接執行（預設模型，首次自動下載約 3 GB）
uv run python realtime.py

# 翻譯成英文
uv run python realtime.py --task translate

# 指定辨識語言為中文
uv run python realtime.py --language zh

# 使用較小的模型（適合 M1/M2，約 1.5 GB）
uv run python realtime.py --model mlx-community/whisper-medium-mlx

# 列出可用模型
uv run python realtime.py --list
```

---

## 參數說明

### 基本參數

| 參數 | 簡寫 | 說明 | 預設值 |
|------|------|------|--------|
| `--model` | `-m` | 模型名稱（HF repo 或本地路徑）| `whisper-large-v3-mlx` |
| `--task` | `-t` | `transcribe` 或 `translate` | `transcribe` |
| `--language` | `-l` | 語言代碼（`zh`、`en`、`ja`…）| 自動偵測 |
| `--list` | | 列出可用模型 | |

### VAD 參數（語音偵測）

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--speech-threshold` | 語音偵測門檻（0.0–1.0），越高越嚴格 | `0.5` |
| `--silence-duration` | 語音結束後的靜音時長（秒） | `0.6` |
| `--min-speech-duration` | 最短語音長度（秒），太短會被忽略 | `0.2` |
| `--speech-pad-duration` | 語音前後的緩衝（秒） | `0.1` |

### VAD 調整建議

| 情境 | 建議調整 |
|------|----------|
| 說話較快 | `--silence-duration 0.4` |
| 環境吵雜 | `--speech-threshold 0.6` |
| 短句被忽略 | `--min-speech-duration 0.1` |
| 開頭被截斷 | `--speech-pad-duration 0.2` |

```bash
# 組合多個參數
uv run python realtime.py --silence-duration 0.4 --speech-threshold 0.6
```

---

## 自動簡繁轉換

使用 `mlx-community/whisper*` 模型時，辨識結果會自動轉換成**臺灣繁體中文**：

- 簡體字 → 繁體字（「开放」→「開放」）
- 大陸用語 → 臺灣用語（「鼠标」→「滑鼠」、「内存」→「記憶體」）

使用 [OpenCC](https://github.com/BYVoid/OpenCC) 的 `s2twp` 配置。使用本地轉換的模型（如臺灣客語模型）時，不會進行簡繁轉換，以保留原始輸出。

---

## 浮動字幕視窗

適用於全螢幕簡報時顯示即時字幕，視窗始終顯示在最上層（包括全螢幕應用上方）。

```bash
# 基本使用
uv run python subtitle/subtitle.py

# 翻譯成英文
uv run python subtitle/subtitle.py --task translate

# 使用較小的模型
uv run python subtitle/subtitle.py --model mlx-community/whisper-medium-mlx

# 顯示在延伸螢幕（外接螢幕，螢幕編號從 0 開始）
uv run python subtitle/subtitle.py --screen 1

# 調整 VAD 參數
uv run python subtitle/subtitle.py --silence-duration 0.4
```

**特色：**
- 可拖動調整位置
- 支援多行顯示，最新字幕在最下方
- 支援多螢幕

### 自訂樣式

編輯 `subtitle/subtitle.py` 開頭的設定區塊：

```python
# 視窗設定
WINDOW_WIDTH_RATIO = 0.8      # 視窗寬度佔螢幕比例
WINDOW_BOTTOM_MARGIN = 50     # 距離螢幕底部的距離（px）
WINDOW_OPACITY = 0.85         # 透明度（0.0–1.0）

# 文字設定
FONT_SIZE = 36                # 字體大小
FONT_NAME = None              # 字體名稱，None 為系統預設
MAX_LINES = 3                 # 顯示行數
LINE_HEIGHT = 1.3             # 行高倍率
TEXT_COLOR = "white"          # 文字顏色：white / yellow / green / cyan
```

| 需求 | 設定 |
|------|------|
| 字更大 | `FONT_SIZE = 48` |
| 字更小 | `FONT_SIZE = 28` |
| 顯示更多行 | `MAX_LINES = 5` |
| 只顯示一行 | `MAX_LINES = 1` |
| 視窗更窄 | `WINDOW_WIDTH_RATIO = 0.6` |
| 黃色字幕 | `TEXT_COLOR = "yellow"` |
| 更透明 | `WINDOW_OPACITY = 0.7` |

---

## 擴展漢字支援

臺灣客語使用的漢字有些在 CJK 擴展區，一般字體不支援，會顯示為方塊（豆腐字）。

```bash
./install_fonts.sh
```

此腳本提供兩種字體：

| 字體 | 特色 |
|------|------|
| 花園明朝 (HanaMin) | 支援最多漢字，適合臺灣客語 |
| 思源黑體 (Noto Sans CJK TC) | Google/Adobe 聯合製作，較美觀 |

安裝後，設定終端機或字幕視窗使用該字體：

**iTerm2：** Preferences → Profiles → Text → Font 選擇 `HanaMinA`

**Terminal.app：** 偏好設定 → 描述檔 → 字體 → 更改 → 選擇 `HanaMinA`

**字幕視窗：** 編輯 `subtitle/subtitle.py`，修改 `FONT_NAME = "HanaMinA"`

---

## 模型選擇建議

> **效能提示：** M4 以外的晶片建議使用 `medium` 或更小的模型。

| 晶片 | 建議模型 |
|------|----------|
| M4 / M4 Pro / M4 Max | `large-v3` |
| M3 / M3 Pro / M3 Max | `large-v3` 或 `medium` |
| M2 / M2 Pro / M2 Max | `medium` 或 `small` |
| M1 / M1 Pro / M1 Max | `small` 或 `base` |

### 可用模型

> **注意：** `turbo` 版本不支援翻譯功能。

| 模型 | 大小 | 支援翻譯 | 建議晶片 |
|------|------|:--------:|----------|
| `mlx-community/whisper-large-v3-mlx` | ~3 GB | ✅ | M3/M4 |
| `mlx-community/whisper-large-v3-turbo` | ~1.6 GB | ❌ | M2/M3/M4 |
| `mlx-community/whisper-medium-mlx` | ~1.5 GB | ✅ | 全部 |
| `mlx-community/whisper-small-mlx` | ~488 MB | ✅ | 全部 |
| `mlx-community/whisper-base-mlx` | ~145 MB | ✅ | 全部 |
| `mlx-community/whisper-tiny-mlx` | ~75 MB | ✅ | 全部 |

---

## 轉換自訂模型

如需使用 HuggingFace 上的其他 Whisper 模型（如特定語言的微調模型），可以轉換為 MLX 格式。

```bash
cd convert

# 基本用法
./convert.sh <hf-repo>

# 強制重新轉換（模型已存在時）
./convert.sh <hf-repo> --force

# 使用 float32 精度（檔案較大但精度較高）
./convert.sh <hf-repo> --float32
```

### 選項說明

| 選項 | 說明 |
|------|------|
| `--output-dir` | 輸出目錄（預設：`../models`）|
| `--dtype` | 數據類型：`float16`（預設）或 `float32` |
| `--force` | 強制重新轉換，即使模型已存在 |

### 使用轉換後的模型

```bash
cd ..

# 列出可用模型（包含本地模型）
uv run python realtime.py --list

# 使用轉換後的模型
uv run python realtime.py --model whisper-large-v2-taiwanese-hakka-v1-mlx
```

> 首次轉換會從 HuggingFace 下載原始模型，large 模型約 3 GB，請確認磁碟空間充足。若模型已轉換過，會自動跳過。

---

## 疑難排解

**麥克風沒有反應**
- 系統設定 → 隱私與安全性 → 麥克風 → 勾選終端機
- 系統設定 → 聲音 → 輸入 → 確認選對麥克風

**確認 GPU 使用**
- 開啟「活動監視器」→「GPU」分頁，應可看到 Python 使用 GPU

**辨識品質不佳**
- 說話清晰、語速適中，減少背景噪音
- 嘗試使用更大的模型

**VAD 偵測不準確**

```bash
uv run python realtime.py --speech-threshold 0.6   # 環境吵雜
uv run python realtime.py --silence-duration 0.4   # 說話較快
```

**顯示方塊字（豆腐字）**

```bash
./install_fonts.sh
```

安裝後設定終端機或字幕視窗使用 `HanaMinA` 字體。

**`brew` 指令找不到**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**`uv` 指令找不到**

```bash
source ~/.zshrc
```

---

## 目錄結構

```
whisper-live-client-for-mac/
├── realtime.py           # 即時語音辨識（主程式）
├── vad.py                # Silero VAD 模組
├── install_fonts.sh      # 安裝擴展漢字字體
├── pyproject.toml        # 專案設定與依賴
├── uv.lock               # 鎖定版本
├── convert/              # 模型轉換工具
│   ├── convert.sh
│   └── convert.py
├── models/               # 轉換後的本地模型
└── subtitle/             # 浮動字幕視窗
    └── subtitle.py
```

---

## 授權

[MIT License](LICENSE)
