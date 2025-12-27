# 即時字幕浮動視窗

在簡報時顯示即時字幕，視窗會顯示在**全螢幕簡報上方**。

## 特色

- ✅ 即時語音辨識 / 翻譯成英文
- ✅ 浮動視窗，始終在最上層
- ✅ 支援全螢幕模式（Google Slides、PowerPoint、Keynote）
- ✅ 可拖動調整位置
- ✅ 使用 Apple Silicon GPU 加速
- ✅ 可自訂視窗大小、字體大小、顏色

## 使用方式

請先完成[主 README](../README.md) 的環境設置，然後執行：

```bash
# 基本使用（使用預設模型）
uv run python subtitle/subtitle.py

# 翻譯成英文
uv run python subtitle/subtitle.py --task translate

# 使用較小的模型（適合 M1/M2）
uv run python subtitle/subtitle.py --model mlx-community/whisper-medium-mlx

# 指定語言
uv run python subtitle/subtitle.py --language zh

# 列出可用模型
uv run python subtitle/subtitle.py --list
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

編輯 `subtitle/subtitle.py` 開頭的設定區塊：

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

---

## 🔤 擴展漢字支援（臺灣客語等）

臺灣客語使用的漢字有些在 CJK 擴展區，一般字體不支援，會顯示為方塊（豆腐字）。

### 安裝擴展漢字字體

```bash
./install_fonts.sh
```

可選擇安裝：
- **花園明朝 (HanaMin)** - 支援最多漢字
- **思源黑體 (Noto Sans CJK TC)** - 較美觀

### 設定字幕視窗字體

編輯 `subtitle/subtitle.py`，修改 `FONT_NAME`：

```python
FONT_NAME = "HanaMinA"           # 花園明朝
# 或
FONT_NAME = "Noto Sans CJK TC"   # 思源黑體
```

---

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
uv run python subtitle/subtitle.py --model mlx-community/whisper-medium-mlx
```

### 顯示方塊字（豆腐字）

安裝擴展漢字字體並設定 `FONT_NAME`，詳見上方說明。
