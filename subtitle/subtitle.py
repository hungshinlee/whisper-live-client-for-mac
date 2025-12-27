"""
即時字幕浮動視窗 - macOS 原生版本
使用 PyObjC 確保在全螢幕簡報上方也能顯示

使用方式（從專案根目錄執行）:
  # 使用預設模型
  uv run python subtitle/subtitle.py
  
  # 指定模型
  uv run python subtitle/subtitle.py --model mlx-community/whisper-medium-mlx
  
  # 翻譯成英文
  uv run python subtitle/subtitle.py --task translate
  
  # 指定語言
  uv run python subtitle/subtitle.py --language zh
  
  # 列出可用模型
  uv run python subtitle/subtitle.py --list
"""
import argparse
import signal
import sys
import threading
import numpy as np
import pyaudio
import mlx_whisper
from pathlib import Path

# 加入父目錄到 path 以便 import vad
sys.path.insert(0, str(Path(__file__).parent.parent))
from vad import create_vad, VADConfig, HAS_SILERO

import AppKit
from AppKit import (
    NSApplication, NSWindow, NSTextField, NSColor, NSFont,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSScreenSaverWindowLevel,
    NSMakeRect, NSScreen,
    NSTextAlignmentCenter,
    NSApplicationActivationPolicyAccessory
)
from PyObjCTools import AppHelper

# ===========================================
# 📐 視窗設定（可自行調整）
# ===========================================
WINDOW_WIDTH_RATIO = 0.8      # 視窗寬度佔螢幕比例 (0.0 ~ 1.0)
WINDOW_HEIGHT = 100           # 視窗高度 (像素)
WINDOW_BOTTOM_MARGIN = 50     # 視窗距離螢幕底部的距離 (像素)
WINDOW_OPACITY = 0.85         # 視窗透明度 (0.0 ~ 1.0，1.0 為不透明)

# ===========================================
# 🔤 文字設定（可自行調整）
# ===========================================
FONT_SIZE = 48                # 字體大小 (像素)
FONT_NAME = None              # 字體名稱，None 為系統預設粗體

# ===========================================
# 🎨 顏色設定（可自行調整）
# ===========================================
BACKGROUND_COLOR = (0.1, 0.1, 0.1)  # 深灰色
TEXT_COLOR = "white"          # white / yellow / green / cyan

# ===========================================
# 🎙️ 錄音設定
# ===========================================
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512  # Silero VAD 需要特定大小

# ===========================================
# 預設設定
# ===========================================
DEFAULT_HF_MODEL = "mlx-community/whisper-large-v3-mlx"
MODELS_DIR = Path(__file__).parent.parent / "models"

# 全域變數
running = True
model = None
task = "transcribe"
language = None
use_silero_vad = True
silence_duration = 1.0


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
    
    if model_name is None:
        local_models = list_local_models()
        if local_models:
            return str(MODELS_DIR / local_models[0])
        return DEFAULT_HF_MODEL
    
    if "/" in model_name:
        return model_name
    
    model_path = MODELS_DIR / model_name
    if model_path.exists():
        return str(model_path)
    
    if not model_name.endswith("-mlx"):
        model_path = MODELS_DIR / f"{model_name}-mlx"
        if model_path.exists():
            return str(model_path)
    
    return f"mlx-community/{model_name}"


def get_text_color():
    """取得文字顏色"""
    colors = {
        "white": NSColor.whiteColor(),
        "yellow": NSColor.yellowColor(),
        "green": NSColor.greenColor(),
        "cyan": NSColor.cyanColor(),
    }
    return colors.get(TEXT_COLOR, NSColor.whiteColor())


class SubtitleWindow:
    def __init__(self):
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        screen_width = screen_frame.size.width
        screen_height = screen_frame.size.height
        
        window_width = screen_width * WINDOW_WIDTH_RATIO
        window_height = WINDOW_HEIGHT
        x = (screen_width - window_width) / 2
        y = WINDOW_BOTTOM_MARGIN
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, window_width, window_height),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        
        self.window.setLevel_(NSScreenSaverWindowLevel)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                BACKGROUND_COLOR[0], 
                BACKGROUND_COLOR[1], 
                BACKGROUND_COLOR[2], 
                WINDOW_OPACITY
            )
        )
        self.window.setHasShadow_(True)
        self.window.setMovableByWindowBackground_(True)
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces |
            AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        
        content_view = self.window.contentView()
        self.label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, 10, window_width - 40, window_height - 20)
        )
        self.label.setStringValue_("🎤 等待說話...")
        
        if FONT_NAME:
            font = NSFont.fontWithName_size_(FONT_NAME, FONT_SIZE)
            if font is None:
                font = NSFont.boldSystemFontOfSize_(FONT_SIZE)
        else:
            font = NSFont.boldSystemFontOfSize_(FONT_SIZE)
        self.label.setFont_(font)
        
        self.label.setTextColor_(get_text_color())
        self.label.setBackgroundColor_(NSColor.clearColor())
        self.label.setBezeled_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(NSTextAlignmentCenter)
        
        content_view.addSubview_(self.label)
        self.window.makeKeyAndOrderFront_(None)
    
    def update_text(self, text):
        """更新字幕文字（執行緒安全）"""
        def update():
            self.label.setStringValue_(text)
        AppHelper.callAfter(update)
    
    def close(self):
        def do_close():
            self.window.close()
            AppHelper.stopEventLoop()
        AppHelper.callAfter(do_close)


def transcribe_audio(audio_data: bytes) -> str:
    global model, task, language
    
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    kwargs = {
        "path_or_hf_repo": model,
        "task": task,
    }
    
    if language:
        kwargs["language"] = language
    
    result = mlx_whisper.transcribe(audio_np, **kwargs)
    
    return result["text"].strip()


def audio_thread(subtitle_window):
    """錄音和辨識的執行緒"""
    global running, model, task, language, use_silero_vad, silence_duration
    
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    subtitle_window.update_text("⏳ 載入模型中...")
    
    # 預熱模型
    dummy = np.zeros(RATE, dtype=np.float32)
    warmup_kwargs = {"path_or_hf_repo": model, "task": task}
    if language:
        warmup_kwargs["language"] = language
    mlx_whisper.transcribe(dummy, **warmup_kwargs)
    
    # 建立 VAD
    use_silero = use_silero_vad and HAS_SILERO
    vad = create_vad(
        use_silero=use_silero,
        min_silence_duration=silence_duration,
        silence_duration=silence_duration,
        sample_rate=RATE,
        chunk_size=CHUNK,
    )
    
    subtitle_window.update_text("🎤 準備就緒，開始說話...")
    
    try:
        while running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except:
                break
            
            if not running:
                break
            
            # 使用 VAD 處理
            audio_data = vad.process(data)
            
            if audio_data is not None and len(audio_data) > CHUNK * 10:
                task_text = "翻譯" if task == "translate" else "辨識"
                subtitle_window.update_text(f"⏳ {task_text}中...")
                text = transcribe_audio(audio_data)
                if text and running:
                    subtitle_window.update_text(text)
    
    except Exception as e:
        if running:
            subtitle_window.update_text(f"錯誤: {str(e)}")
    
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def signal_handler(signum, frame):
    """處理 Ctrl+C 信號"""
    global running
    print("\n\n正在關閉...")
    running = False
    AppHelper.stopEventLoop()


def main():
    global running, model, task, language, use_silero_vad, silence_duration
    
    parser = argparse.ArgumentParser(
        description="即時字幕浮動視窗（Apple Silicon GPU 加速）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 基本使用
  uv run python subtitle/subtitle.py
  
  # 翻譯成英文
  uv run python subtitle/subtitle.py --task translate
  
  # 使用較小的模型
  uv run python subtitle/subtitle.py --model mlx-community/whisper-medium-mlx
  
  # 指定語言
  uv run python subtitle/subtitle.py --language zh
"""
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="模型名稱：HF repo 或本地模型名稱",
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
        help="語言代碼（如 zh, en, ja）",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出可用的模型",
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
    
    # 列出模型
    if args.list:
        local_models = list_local_models()
        print("本地模型:")
        if local_models:
            for m in local_models:
                print(f"  • {m}")
        else:
            print("  （無）")
        print()
        print("HuggingFace 模型:")
        print("  • mlx-community/whisper-large-v3-mlx")
        print("  • mlx-community/whisper-medium-mlx")
        print("  • mlx-community/whisper-small-mlx")
        return
    
    # 解析模型
    model = resolve_model(args.model)
    task = args.task
    language = args.language
    use_silero_vad = not args.no_vad
    silence_duration = args.silence_duration
    
    # 顯示設定
    task_display = "轉錄" if task == "transcribe" else "翻譯成英文"
    lang_display = language if language else "自動偵測"
    
    if "/" in model and not model.startswith("/"):
        model_display = model
    else:
        model_display = Path(model).name
    
    # 決定使用哪種 VAD
    use_silero = use_silero_vad and HAS_SILERO
    vad_display = "Silero VAD" if use_silero else "音量門檻"
    
    print("=" * 50)
    print("即時字幕浮動視窗")
    print("使用 Apple Silicon GPU 加速")
    print("=" * 50)
    print(f"模型: {model_display}")
    print(f"任務: {task_display}")
    print(f"語言: {lang_display}")
    print(f"VAD: {vad_display}")
    print("=" * 50)
    print(f"\n視窗設定：")
    print(f"  寬度：螢幕的 {int(WINDOW_WIDTH_RATIO * 100)}%")
    print(f"  高度：{WINDOW_HEIGHT} 像素")
    print(f"  字體：{FONT_SIZE} 像素")
    print(f"  顏色：{TEXT_COLOR}")
    print("\n操作說明：")
    print("  • 拖動字幕視窗可移動位置")
    print("  • 按 Ctrl+C 關閉程式")
    print("  • 字幕會顯示在全螢幕簡報上方")
    print("\n正在啟動...\n")
    
    # 設定信號處理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化應用程式
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    
    # 建立字幕視窗
    subtitle_window = SubtitleWindow()
    
    # 在背景執行緒中執行錄音和翻譯
    thread = threading.Thread(target=audio_thread, args=(subtitle_window,), daemon=True)
    thread.start()
    
    # 設定定時器來檢查是否需要關閉
    def check_running():
        if not running:
            AppHelper.stopEventLoop()
        else:
            threading.Timer(0.5, lambda: AppHelper.callAfter(check_running)).start()
    
    AppHelper.callAfter(check_running)
    
    # 執行主迴圈
    AppHelper.runEventLoop()
    
    print("已關閉")


if __name__ == "__main__":
    main()
