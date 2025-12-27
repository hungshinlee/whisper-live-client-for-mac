# Whisper Live Client for Mac

專為 Apple Silicon Mac 設計的即時語音轉文字工具，使用 MLX 框架實現 GPU 加速。

## 功能特色

- ✅ 即時語音轉文字（Transcribe）
- ✅ 即時語音翻譯成英文（Translate）
- ✅ Apple Silicon GPU 加速
- ✅ 支援 HuggingFace 上的任何 Whisper 模型
- ✅ **浮動字幕視窗** - 適用於全螢幕簡報

## 系統需求

- macOS（Apple Silicon：M1/M2/M3/M4）
- Python 3.10+

---

## 快速開始

### 1. 安裝系統依賴

#### 安裝 Homebrew（如果尚未安裝）

Homebrew 是 macOS 的套件管理器。開啟終端機，執行：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安裝完成後，依照終端機顯示的指示，將 Homebrew 加入 PATH。通常是執行：

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

#### 安裝 uv（Python 套件管理器）

[uv](https://github.com/astral-sh/uv) 是一個快速的 Python 套件管理器：

```bash
brew install uv
```

或者使用官方安裝腳本：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 安裝音訊處理相關套件

```bash
brew install ffmpeg portaudio
```

### 2. 下載專案並設置環境

```bash
git clone https://github.com/hungshinlee/whisper-live-client-for-mac.git
cd whisper-live-client-for-mac
uv venv
uv pip install mlx-whisper pyaudio numpy
```

### 3. 開始使用

```bash
# 純轉錄（使用 whisper-large-v3，會自動下載）
uv run python transcribe_only.py

# 翻譯成英文
uv run python transcribe.py
```

---

## 🎤 即時語音辨識

### 使用 HuggingFace 模型（自動下載）

最簡單的方式，不需要轉換模型：

```bash
# 純轉錄
uv run python transcribe_only.py

# 翻譯成英文
uv run python transcribe.py
```

### 使用本地轉換的模型

如果你需要使用特定的微調模型（如臺灣客語），可以先轉換再使用：

```bash
# 轉換模型
cd convert
./convert.sh formospeech/whisper-large-v2-taiwanese-hakka-v1

# 使用轉換後的模型
cd ..
uv run python realtime.py

# 指定模型
uv run python realtime.py --model whisper-large-v2-taiwanese-hakka-v1-mlx

# 翻譯成英文
uv run python realtime.py --task translate

# 指定語言
uv run python realtime.py --language zh
```

### 參數說明

| 參數 | 簡寫 | 說明 | 預設值 |
|------|------|------|--------|
| `--model` | `-m` | 模型名稱或路徑 | 第一個可用模型 |
| `--task` | `-t` | `transcribe` 或 `translate` | `transcribe` |
| `--language` | `-l` | 語言代碼（zh, en, ja...）| 自動偵測 |
| `--list` | | 列出可用模型 | |

---

## 🖥️ 浮動字幕視窗

適用於 Google Slides、PowerPoint、Keynote 等全螢幕簡報時顯示即時字幕。

### 設置

```bash
cd subtitle
uv venv
uv pip install mlx-whisper pyaudio numpy pyobjc-framework-Cocoa
```

### 使用

```bash
# 基本使用
uv run python subtitle.py

# 翻譯成英文
uv run python subtitle.py --task translate

# 指定模型
uv run python subtitle.py --model whisper-large-v2-taiwanese-hakka-v1-mlx
```

### 特色

- 字幕視窗始終在最上層（包括全螢幕應用上方）
- 可拖動調整位置
- 可自訂視窗大小、字體、顏色

詳細說明請看 [subtitle/README.md](subtitle/README.md)

---

## 模型選擇建議

⚠️ **效能提示：** 如果你的 Mac 不是 M4 晶片，建議使用 `medium` 或更小的模型。

| 晶片 | 建議模型 | 說明 |
|------|----------|------|
| M4 / M4 Pro / M4 Max | `large-v3` | 最佳品質 |
| M3 / M3 Pro / M3 Max | `large-v3` 或 `medium` | large 可能稍慢 |
| M2 / M2 Pro / M2 Max | `medium` 或 `small` | 平衡品質與速度 |
| M1 / M1 Pro / M1 Max | `small` 或 `base` | 確保流暢體驗 |

### 可用模型

⚠️ **turbo 版本不支援翻譯功能！**

| 模型 | 大小 | 翻譯 | 建議晶片 |
|------|------|------|----------|
| `mlx-community/whisper-large-v3-mlx` | ~3 GB | ✅ | M3/M4 |
| `mlx-community/whisper-large-v3-turbo` | ~1.6 GB | ❌ | M2/M3/M4 |
| `mlx-community/whisper-medium-mlx` | ~1.5 GB | ✅ | 全部 |
| `mlx-community/whisper-small-mlx` | ~488 MB | ✅ | 全部 |
| `mlx-community/whisper-base-mlx` | ~145 MB | ✅ | 全部 |
| `mlx-community/whisper-tiny-mlx` | ~75 MB | ✅ | 全部 |

如需使用較小的模型，修改 `transcribe.py` 或 `transcribe_only.py` 中的 `MODEL_NAME`：

```python
MODEL_NAME = "mlx-community/whisper-medium-mlx"
```

---

## 轉換自訂模型

可以將 HuggingFace 上的任何 Whisper 模型轉換為 MLX 格式：

```bash
cd convert
./convert.sh <hf-repo>

# 範例
./convert.sh formospeech/whisper-large-v2-taiwanese-hakka-v1
./convert.sh openai/whisper-large-v3
```

轉換後的模型存放在 `models/` 目錄。

詳細說明請看 [convert/README.md](convert/README.md)

---

## 語言代碼

| 語言 | 代碼 |
|------|------|
| 中文 | `zh` |
| 英文 | `en` |
| 日文 | `ja` |
| 韓文 | `ko` |
| 臺灣客語 | `zh`（使用專用模型）|
| 自動偵測 | 不設定 |

---

## 疑難排解

### 麥克風沒有反應

1. **系統設定** → **隱私與安全性** → **麥克風** → 勾選終端機
2. **系統設定** → **聲音** → **輸入** → 確認選對麥克風

### 確認 GPU 使用

執行時打開「活動監視器」→「GPU」分頁，應該會看到 Python 使用 GPU。

### 辨識品質不佳

- 說話清晰、語速適中
- 減少背景噪音
- 嘗試使用更大的模型

### brew 指令找不到

如果出現 `command not found: brew`，請確認 Homebrew 已正確安裝並加入 PATH：

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### uv 指令找不到

如果出現 `command not found: uv`，請重新開啟終端機，或執行：

```bash
source ~/.zshrc
```

---

## 目錄結構

```
whisper-live-client-for-mac/
├── README.md
├── transcribe.py         # 翻譯成英文（HF 模型）
├── transcribe_only.py    # 純轉錄（HF 模型）
├── realtime.py           # 即時辨識（本地模型）
├── convert/              # 模型轉換工具
│   ├── convert.sh
│   └── convert.py
├── models/               # 轉換後的模型
└── subtitle/             # 浮動字幕視窗
    └── subtitle.py
```

---

## 授權

MIT License
