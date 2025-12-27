# MLX Whisper 客戶端

使用 Apple Silicon GPU 加速的即時語音轉文字工具。

## 優勢

| 特性 | WhisperLive (faster-whisper) | MLX Whisper |
|------|------------------------------|-------------|
| Apple GPU | ❌ 不支援 | ✅ 支援 |
| 運算裝置 | CPU only | Apple Silicon GPU |
| 架構 | Client-Server | 單一程式 |

## 設置步驟

### 1. 安裝系統依賴

```bash
brew install ffmpeg portaudio
```

### 2. 建立虛擬環境

```bash
cd /Users/winston/Projects/whisper-live-client/mlx
uv venv
uv pip install mlx-whisper pyaudio numpy
```

---

## 🎤 即時語音辨識

可以直接使用 HuggingFace 上的 MLX 模型（會自動下載），或使用自行轉換的模型。

### 使用 HuggingFace 模型（自動下載，最簡單）

不需要轉換，直接使用：

```bash
# 純轉錄（使用 whisper-large-v3）
uv run python transcribe_only.py

# 翻譯成英文
uv run python transcribe.py
```

### 使用本地轉換的模型

如果你已經轉換了自訂模型，可以使用 `realtime.py`：

```bash
# 基本使用（自動偵測語言，純轉錄）
uv run python realtime.py

# 列出可用模型
uv run python realtime.py --list

# 指定模型
uv run python realtime.py --model whisper-large-v2-taiwanese-hakka-v1-mlx

# 翻譯成英文
uv run python realtime.py --task translate

# 指定語言為中文
uv run python realtime.py --language zh

# 組合使用
uv run python realtime.py -m whisper-large-v2-taiwanese-hakka-v1-mlx -l zh -t transcribe
```

### 參數說明

| 參數 | 簡寫 | 說明 | 預設值 |
|------|------|------|--------|
| `--model` | `-m` | 模型名稱或路徑 | 第一個可用模型 |
| `--task` | `-t` | `transcribe`（轉錄）或 `translate`（翻譯成英文）| `transcribe` |
| `--language` | `-l` | 語言代碼（如 zh, en, ja）| 自動偵測 |
| `--list` | | 列出可用模型 | |

---

## 模型選擇建議

⚠️ **效能提示：** 如果你的 Mac 晶片不是 M4，建議使用 `medium` 或更小的模型，以獲得更流暢的體驗。

| 晶片 | 建議模型 | 說明 |
|------|----------|------|
| M4 / M4 Pro / M4 Max | `large-v3` | 最佳品質，速度快 |
| M3 / M3 Pro / M3 Max | `large-v3` 或 `medium` | large 可能稍慢 |
| M2 / M2 Pro / M2 Max | `medium` 或 `small` | 平衡品質與速度 |
| M1 / M1 Pro / M1 Max | `small` 或 `base` | 確保流暢體驗 |

### 可用模型

⚠️ **注意：turbo 版本不支援翻譯功能！**

| 模型 | 大小 | 翻譯支援 | 建議晶片 |
|------|------|----------|----------|
| `mlx-community/whisper-large-v3-mlx` | ~3 GB | ✅ 支援 | M3/M4 |
| `mlx-community/whisper-large-v3-turbo` | ~1.6 GB | ❌ 不支援 | M2/M3/M4 |
| `mlx-community/whisper-medium-mlx` | ~1.5 GB | ✅ 支援 | M1/M2/M3/M4 |
| `mlx-community/whisper-small-mlx` | ~488 MB | ✅ 支援 | 全部 |
| `mlx-community/whisper-base-mlx` | ~145 MB | ✅ 支援 | 全部 |
| `mlx-community/whisper-tiny-mlx` | ~75 MB | ✅ 支援 | 全部 |

如需使用較小的模型，可以修改 `transcribe.py` 或 `transcribe_only.py` 中的 `MODEL_NAME`：

```python
# 例如改用 medium 模型
MODEL_NAME = "mlx-community/whisper-medium-mlx"
```

---

## 🖥️ 浮動字幕視窗（簡報用）

適用於全螢幕簡報時即時顯示字幕。

```bash
cd subtitle
uv pip install pyobjc-framework-Cocoa

# 基本使用
uv run python subtitle.py

# 翻譯成英文
uv run python subtitle.py --task translate

# 指定模型和語言
uv run python subtitle.py -m whisper-large-v2-taiwanese-hakka-v1-mlx -l zh
```

詳細說明請參考 [subtitle/README.md](subtitle/README.md)。

---

## 轉換自訂模型（可選）

如果需要使用特定語言的微調模型（如臺灣客語），可以將 HuggingFace 上的 Whisper 模型轉換為 MLX 格式。

```bash
cd convert

# 轉換模型
./convert.sh <hf-repo>

# 範例：臺灣客語模型
./convert.sh formospeech/whisper-large-v2-taiwanese-hakka-v1

# 範例：OpenAI 官方模型
./convert.sh openai/whisper-large-v3

# 強制重新轉換
./convert.sh formospeech/whisper-large-v2-taiwanese-hakka-v1 --force
```

轉換後的模型存放在 `models/` 目錄。

詳細說明請參考 [convert/README.md](convert/README.md)。

---

## 確認 GPU 使用

執行時打開「活動監視器」→「GPU」分頁，應該會看到 Python 正在使用 GPU。

## 與 WhisperLive 的差異

- **MLX Whisper**：單一程式，使用 Apple GPU，說完一句話後才辨識
- **WhisperLive**：Client-Server 架構，使用 CPU，可以即時串流顯示

如果需要「邊說邊顯示」的即時效果，請使用上層目錄的 WhisperLive 版本。

---

## 目錄結構

```
mlx/
├── transcribe.py         # 翻譯（HF 模型自動下載）
├── transcribe_only.py    # 轉錄（HF 模型自動下載）
├── realtime.py           # 🎤 即時語音辨識（本地模型）
├── convert/              # 模型轉換工具
│   ├── convert.sh
│   ├── convert.py
│   └── README.md
├── models/               # 轉換後的模型
│   └── {model-name}-mlx/
└── subtitle/             # 🖥️ 浮動字幕視窗
    ├── subtitle.py
    └── README.md
```
