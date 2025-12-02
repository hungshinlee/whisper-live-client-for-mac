# MLX Whisper 客戶端

使用 Apple Silicon GPU 加速的即時語音轉文字工具。

## 優勢

| 特性 | WhisperLive (faster-whisper) | MLX Whisper |
|------|------------------------------|-------------|
| Apple GPU | ❌ 不支援 | ✅ 支援 |
| 運算裝置 | CPU only | Apple Silicon GPU |
| 架構 | Client-Server | 單一程式 |

## 設置步驟

### 1. 安裝 ffmpeg 和 PortAudio

```bash
brew install ffmpeg portaudio
```

### 2. 建立虛擬環境並安裝依賴

```bash
cd /Users/winston/Projects/whisper-live-client/mlx
uv venv
uv pip install mlx-whisper pyaudio numpy
```

## 使用方式

不需要啟動伺服器，直接執行即可：

**中文翻譯成英文：**
```bash
uv run python transcribe.py
```

**純中文轉錄（不翻譯）：**
```bash
uv run python transcribe_only.py
```

## 可用模型

### 翻譯功能（translate）

⚠️ **重要：turbo 版本不支援翻譯！** 翻譯必須使用完整版模型。

| 模型 | 大小 | 翻譯支援 | 說明 |
|------|------|----------|------|
| `mlx-community/whisper-large-v3-mlx` | ~3 GB | ✅ 支援 | 翻譯功能推薦 |
| `mlx-community/whisper-large-v3-turbo` | ~1.6 GB | ❌ 不支援 | 只能轉錄 |
| `mlx-community/distil-whisper-large-v3` | ~1.5 GB | ❌ 不支援 | 只能轉錄 |

### 純轉錄功能（transcribe）

所有模型都支援轉錄：

| 模型 | 大小 | 速度 | 說明 |
|------|------|------|------|
| `mlx-community/whisper-tiny` | ~75 MB | 最快 | 基本測試 |
| `mlx-community/whisper-small` | ~488 MB | 快 | 一般使用 |
| `mlx-community/whisper-large-v3-turbo` | ~1.6 GB | 中等 | 轉錄推薦，速度快 |
| `mlx-community/whisper-large-v3-mlx` | ~3 GB | 較慢 | 最高準確度 |

首次使用會自動從 Hugging Face 下載模型。

## 確認 GPU 使用

執行時打開「活動監視器」（Activity Monitor），選擇「GPU」分頁，應該會看到 Python 程序正在使用 GPU。

## 與 WhisperLive 的差異

- **MLX Whisper**：單一程式，使用 Apple GPU，說完一句話後才辨識
- **WhisperLive**：Client-Server 架構，使用 CPU，可以即時串流顯示（邊說邊辨識）

如果你需要「邊說邊顯示」的即時效果，請使用上層目錄的 WhisperLive 版本。
如果你需要更快的辨識速度，請使用此 MLX 版本。
