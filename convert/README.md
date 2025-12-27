# Whisper 模型轉換工具

將 HuggingFace Whisper 模型轉換為 MLX 格式，以便在 Apple Silicon 上使用 GPU 加速。

## 快速開始

```bash
cd convert

# 轉換臺灣客語模型
./convert.sh formospeech/whisper-large-v2-taiwanese-hakka-v1

# 轉換 OpenAI 模型
./convert.sh openai/whisper-large-v3
```

轉換完成後，模型會保存在 `models/` 目錄（與 `convert/` 同層）。

## 使用方式

### Shell 腳本（推薦）

```bash
# 基本用法
./convert.sh <hf-repo>

# 強制重新轉換
./convert.sh <hf-repo> --force

# 使用 float32 精度（檔案較大但精度較高）
./convert.sh <hf-repo> --float32
```

### Python 直接呼叫

```bash
# 如果 convert 目錄沒有獨立環境，先設置
uv venv
uv pip install mlx numpy huggingface_hub safetensors

# 執行轉換
uv run python convert.py formospeech/whisper-large-v2-taiwanese-hakka-v1

# 查看所有選項
uv run python convert.py --help
```

## 選項說明

| 選項 | 說明 |
|------|------|
| `--output-dir` | 輸出目錄（預設：`../models`）|
| `--dtype` | 數據類型：`float16`（預設）或 `float32` |
| `--force` | 強制重新轉換，即使模型已存在 |

## 使用轉換後的模型

```bash
# 回到專案根目錄
cd ..

# 列出可用模型
uv run python realtime.py --list

# 使用轉換後的模型
uv run python realtime.py --model whisper-large-v2-taiwanese-hakka-v1-mlx

# 翻譯成英文
uv run python realtime.py -m whisper-large-v2-taiwanese-hakka-v1-mlx --task translate
```

## 支援的模型

理論上支援所有 HuggingFace 上的 Whisper 模型：

- OpenAI 官方模型：`openai/whisper-large-v3`
- 臺灣客語：`formospeech/whisper-large-v2-taiwanese-hakka-v1`
- 其他社群微調模型

## 注意事項

- 首次轉換會從 HuggingFace 下載模型
- large 模型約 3GB，需要足夠的磁碟空間
- 轉換後使用 float16 格式以節省空間
- 如果模型已轉換過，會自動跳過
