"""
MLX Whisper 即時語音辨識（使用 Apple Silicon GPU）

使用方式:
  # 最簡單：使用預設 HF 模型
  uv run python realtime.py
  
  # 翻譯成英文
  uv run python realtime.py --task translate
  
  # 指定語言
  uv run python realtime.py --language zh
  
  # 使用特定 HF 模型
  uv run python realtime.py --model mlx-community/whisper-medium-mlx
  
  # 使用本地轉換的模型
  uv run python realtime.py --model whisper-large-v2-taiwanese-hakka-v1-mlx
  
  # 列出本地模型
  uv run python realtime.py --list
"""
import argparse
import sys
import numpy as np
import pyaudio
import mlx_whisper
from pathlib import Path

from vad import create_vad, VADConfig, HAS_SILERO

# ===========================================
# 預設設定
# ===========================================
DEFAULT_HF_MODEL = "mlx-community/whisper-large-v3-mlx"
MODELS_DIR = Path(__file__).parent / "models"

# ===========================================
# 錄音設定
# ===========================================
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512  # Silero VAD 需要特定大小，512 是 16kHz 下的標準值


def list_local_models() -> list[str]:
    """列出所有可用的本地模型"""
    if not MODELS_DIR.exists():
        return []
    
    models = []
    for path in MODELS_DIR.iterdir():
        if path.is_dir():
            config_file = path / "config.json"
            weights_file = path / "weights.npz"
            if config_file.exists() and weights_file.exists():
                models.append(path.name)
    
    return sorted(models)


def resolve_model(model_name: str | None) -> str:
    """解析模型名稱，返回可用的模型路徑或 HF repo"""
    
    # 如果沒有指定模型
    if model_name is None:
        # 優先使用本地模型
        local_models = list_local_models()
        if local_models:
            model_path = MODELS_DIR / local_models[0]
            return str(model_path)
        # 否則使用預設 HF 模型
        return DEFAULT_HF_MODEL
    
    # 如果是 HF repo 格式（包含 /）
    if "/" in model_name:
        return model_name
    
    # 嘗試在本地 models 目錄找
    model_path = MODELS_DIR / model_name
    if model_path.exists():
        return str(model_path)
    
    # 嘗試加上 -mlx 後綴
    if not model_name.endswith("-mlx"):
        model_path = MODELS_DIR / f"{model_name}-mlx"
        if model_path.exists():
            return str(model_path)
    
    # 假設是 HF repo 的簡寫（如 whisper-large-v3-mlx）
    return f"mlx-community/{model_name}"


def transcribe_audio(audio_data: bytes, model: str, language: str | None, task: str) -> str:
    """使用 MLX Whisper 辨識"""
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    kwargs = {
        "path_or_hf_repo": model,
        "task": task,
    }
    
    if language:
        kwargs["language"] = language
    
    result = mlx_whisper.transcribe(audio_np, **kwargs)
    
    return result["text"].strip()


def main():
    parser = argparse.ArgumentParser(
        description="MLX Whisper 即時語音辨識（Apple Silicon GPU 加速）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 最簡單：使用預設模型，自動偵測語言
  uv run python realtime.py
  
  # 翻譯成英文
  uv run python realtime.py --task translate
  
  # 指定語言為中文
  uv run python realtime.py --language zh
  
  # 使用較小的模型（適合 M1/M2）
  uv run python realtime.py --model mlx-community/whisper-medium-mlx
  
  # 使用本地轉換的模型
  uv run python realtime.py --model whisper-large-v2-taiwanese-hakka-v1-mlx

常用模型:
  mlx-community/whisper-large-v3-mlx    ~3GB   翻譯✓  M3/M4 推薦
  mlx-community/whisper-large-v3-turbo  ~1.6GB 翻譯✗  M2/M3/M4
  mlx-community/whisper-medium-mlx      ~1.5GB 翻譯✓  全部晶片
  mlx-community/whisper-small-mlx       ~488MB 翻譯✓  全部晶片
"""
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="模型名稱：HF repo（如 mlx-community/whisper-medium-mlx）或本地模型名稱",
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        choices=["transcribe", "translate"],
        default="transcribe",
        help="任務：transcribe（轉錄）或 translate（翻譯成英文）",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="語言代碼（如 zh, en, ja），不指定則自動偵測",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出可用的本地模型",
    )
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="不使用 Silero VAD（改用簡單音量門檻）",
    )
    parser.add_argument(
        "--silence-duration",
        type=float,
        default=1.0,
        help="語音結束後的靜音時長（秒），預設 1.0",
    )
    
    args = parser.parse_args()
    
    # 列出本地模型
    if args.list:
        models = list_local_models()
        print("本地模型:")
        if models:
            for m in models:
                print(f"  • {m}")
        else:
            print("  （無）")
        print()
        print("HuggingFace 模型（會自動下載）:")
        print("  • mlx-community/whisper-large-v3-mlx")
        print("  • mlx-community/whisper-large-v3-turbo")
        print("  • mlx-community/whisper-medium-mlx")
        print("  • mlx-community/whisper-small-mlx")
        print("  • mlx-community/whisper-base-mlx")
        print("  • mlx-community/whisper-tiny-mlx")
        return
    
    # 解析模型
    model = resolve_model(args.model)
    
    # 顯示設定
    task_display = "轉錄" if args.task == "transcribe" else "翻譯成英文"
    lang_display = args.language if args.language else "自動偵測"
    
    # 判斷模型來源
    if "/" in model and not model.startswith("/"):
        model_display = model  # HF repo
        model_source = "HuggingFace"
    else:
        model_display = Path(model).name  # 本地模型
        model_source = "本地"
    
    # 決定使用哪種 VAD
    use_silero = not args.no_vad and HAS_SILERO
    vad_display = "Silero VAD" if use_silero else "音量門檻"
    
    print("=" * 50)
    print("MLX Whisper 即時語音辨識")
    print("使用 Apple Silicon GPU 加速")
    print("=" * 50)
    print(f"模型: {model_display} ({model_source})")
    print(f"任務: {task_display}")
    print(f"語言: {lang_display}")
    print(f"VAD: {vad_display}")
    print("=" * 50)
    print("\n說話後，文字會即時顯示")
    print("按 Ctrl+C 停止\n")
    print("-" * 50)
    
    # 建立 VAD
    vad = create_vad(
        use_silero=use_silero,
        min_silence_duration=args.silence_duration,
        silence_duration=args.silence_duration,  # for SimpleVAD
        sample_rate=RATE,
        chunk_size=CHUNK,
    )
    
    # 初始化 PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    print("正在載入模型...")
    
    # 預熱模型
    dummy = np.zeros(RATE, dtype=np.float32)
    warmup_kwargs = {"path_or_hf_repo": model, "task": args.task}
    if args.language:
        warmup_kwargs["language"] = args.language
    mlx_whisper.transcribe(dummy, **warmup_kwargs)
    print("模型載入完成！開始監聽...\n")
    
    try:
        while True:
            print("🎤 等待說話...", end="\r")
            
            # 讀取音訊
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # 使用 VAD 處理
            audio_data = vad.process(data)
            
            if audio_data is not None and len(audio_data) > CHUNK * 10:
                print("⏳ 辨識中...   ", end="\r")
                text = transcribe_audio(audio_data, model, args.language, args.task)
                if text:
                    print(f"📝 {text}")
    
    except KeyboardInterrupt:
        print("\n\n正在關閉...")
    
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("已停止")


if __name__ == "__main__":
    main()
