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
import threading
import queue
import time
import numpy as np
import pyaudio
import mlx_whisper
from pathlib import Path
from opencc import OpenCC

from vad import SileroVAD, VADConfig

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

# ===========================================
# 簡繁轉換（臺灣繁體）
# ===========================================
# s2twp: 簡體中文 -> 繁體中文（台灣），包含常用詞轉換（如「鼠標」→「滑鼠」）
cc = OpenCC('s2twp')


def should_convert_to_tw(model: str) -> bool:
    """判斷是否需要轉換成臺灣繁體"""
    # mlx-community/whisper* 模型輸出可能是簡體中文，需要轉換
    return model.startswith("mlx-community/whisper")


def convert_to_tw(text: str) -> str:
    """將文字轉換成臺灣繁體中文"""
    return cc.convert(text)


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


def transcribe_audio(audio_data: bytes, model: str, language: str | None, task: str, convert_tw: bool) -> str:
    """使用 MLX Whisper 辨識"""
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    kwargs = {
        "path_or_hf_repo": model,
        "task": task,
    }
    
    if language:
        kwargs["language"] = language
    
    result = mlx_whisper.transcribe(audio_np, **kwargs)
    text = result["text"].strip()
    
    # 轉換成臺灣繁體
    if convert_tw and text:
        text = convert_to_tw(text)
    
    return text


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
  
  # 調整 VAD 參數（說話較快時）
  uv run python realtime.py --silence-duration 0.6 --min-speech-duration 0.2

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
    # VAD 參數
    parser.add_argument(
        "--speech-threshold",
        type=float,
        default=0.5,
        help="語音偵測門檻（0.0~1.0），越高越嚴格，預設 0.5",
    )
    parser.add_argument(
        "--silence-duration",
        type=float,
        default=0.6,
        help="語音結束後的靜音時長（秒），預設 0.6",
    )
    parser.add_argument(
        "--min-speech-duration",
        type=float,
        default=0.2,
        help="最短語音長度（秒），太短會被忽略，預設 0.2",
    )
    parser.add_argument(
        "--speech-pad-duration",
        type=float,
        default=0.1,
        help="語音前後的緩衝（秒），預設 0.1",
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
        print("  • mlx-community/whisper-large-v3-mlx    翻譯✓")
        print("  • mlx-community/whisper-large-v3-turbo  翻譯✗")
        print("  • mlx-community/whisper-medium-mlx      翻譯✓")
        print("  • mlx-community/whisper-small-mlx       翻譯✓")
        print("  • mlx-community/whisper-base-mlx        翻譯✓")
        print("  • mlx-community/whisper-tiny-mlx        翻譯✓")
        return
    
    # 解析模型
    model = resolve_model(args.model)
    
    # 判斷是否需要轉換成臺灣繁體（翻譯任務輸出英文，不需要轉換）
    convert_tw = should_convert_to_tw(model) and args.task == "transcribe"

    # translate 任務若未指定語言，自動補上 zh，否則短音訊語言偵測失敗會亂辨識
    if args.task == "translate" and not args.language:
        args.language = "zh"
        print("ℹ️  translate 任務自動設定語言為 zh（可用 --language 覆蓋）")

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
    
    print("=" * 50)
    print("MLX Whisper 即時語音辨識")
    print("使用 Apple Silicon GPU 加速")
    print("=" * 50)
    print(f"模型: {model_display} ({model_source})")
    print(f"任務: {task_display}")
    print(f"語言: {lang_display}")
    if convert_tw:
        print(f"簡繁轉換: ✓ 臺灣繁體")
    print("-" * 50)
    print("VAD 設定:")
    print(f"  語音門檻: {args.speech_threshold}")
    print(f"  靜音時長: {args.silence_duration} 秒")
    print(f"  最短語音: {args.min_speech_duration} 秒")
    print(f"  前後緩衝: {args.speech_pad_duration} 秒")
    print("=" * 50)
    print("\n說話後，文字會即時顯示")
    print("按 Ctrl+C 停止\n")
    print("-" * 50)
    
    # 建立 VAD
    vad_config = VADConfig(
        speech_threshold=args.speech_threshold,
        min_silence_duration=args.silence_duration,
        min_speech_duration=args.min_speech_duration,
        speech_pad_duration=args.speech_pad_duration,
        sample_rate=RATE,
    )
    vad = SileroVAD(vad_config)
    
    # 初始化 PyAudio (由 Capture Thread 使用)
    # 這裡我們不開啟 stream，交由 Capture Thread 處理
    
    # 建立佇列
    transcription_queue = queue.Queue()
    
    # 建立停止訊號
    stop_event = threading.Event()
    
    def transcription_worker():
        """辨識執行緒"""
        print("⏳ 正在預熱模型...")
        try:
            # 預熱
            dummy = np.zeros(RATE, dtype=np.float32)
            warmup_kwargs = {"path_or_hf_repo": model, "task": args.task}
            if args.language:
                warmup_kwargs["language"] = args.language
            mlx_whisper.transcribe(dummy, **warmup_kwargs)
            print("✅ 模型預熱完成！開始監聽...\n")
        except Exception as e:
            print(f"⚠️ 模型預熱失敗: {e}\n")
            
        while not stop_event.is_set():
            try:
                audio_data = transcription_queue.get(timeout=0.5)
            except queue.Empty:
                continue
                
            # 顯示排隊狀況
            q_size = transcription_queue.qsize()
            if q_size > 0:
                print(f"⏳ (堆積 {q_size} 句) 辨識中...", end="\r")
            else:
                print("⏳ 辨識中...   ", end="\r")
                
            try:
                text = transcribe_audio(audio_data, model, args.language, args.task, convert_tw)
                if text:
                    # 清除「辨識中」並顯示結果
                    # 使用 ANSI escape code 清除整行
                    sys.stdout.write("\033[2K\r") 
                    print(f"📝 {text}")
                else:
                    # 如果沒字，也要清除狀態
                    sys.stdout.write("\033[2K\r")
                    print("🎤 等待說話...", end="\r")
                    
            except Exception as e:
                print(f"\n❌ 錯誤: {e}")
            finally:
                transcription_queue.task_done()
                
        print("辨識執行緒已停止")

    def capture_worker():
        """錄音執行緒"""
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        try:
            while not stop_event.is_set():
                # 這裡單純顯示狀態有點困難，因為這會在背景跑
                # 我們交由 Main Thread 或 Transcription Thread 更新狀態
                # 或者只在沒有堆積時更新
                
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                except Exception:
                    break
                
                audio_data = vad.process(data)
                
                if audio_data is not None and len(audio_data) > CHUNK * 10:
                    transcription_queue.put(audio_data)
                    
        except Exception as e:
            print(f"\n❌ 錄音錯誤: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("錄音執行緒已停止")

    # 啟動執行緒
    t_transcribe = threading.Thread(target=transcription_worker)
    t_capture = threading.Thread(target=capture_worker)
    
    t_transcribe.start()
    t_capture.start()
    
    try:
        while t_transcribe.is_alive() and t_capture.is_alive():
            # 主執行緒僅負責監聽 Ctrl+C 並維持程式運作
            # 這裡可以定期顯示「等待說話」，但為了不跟辨識輸出衝突，
            # 我們讓辨識執行緒負責輸出狀態
            time.sleep(0.1)
            
            # 如果佇列空閒，顯示等待中
            if transcription_queue.empty():
                 sys.stdout.write("🎤 等待說話...\r")
                 sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("\n\n正在關閉...")
        stop_event.set()
    
    # 等待執行緒結束
    t_capture.join(timeout=2.0)
    t_transcribe.join(timeout=2.0)
    print("已停止")


if __name__ == "__main__":
    main()
