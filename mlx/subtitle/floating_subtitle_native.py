"""
即時字幕浮動視窗 - macOS 原生版本
使用 PyObjC 確保在全螢幕簡報上方也能顯示
"""
import signal
import sys
import threading
import queue
import numpy as np
import pyaudio
import mlx_whisper

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

# 模型設定
MODEL_NAME = "mlx-community/whisper-large-v3-mlx"

# 錄音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.2

# 全域變數
running = True


class SubtitleWindow:
    def __init__(self):
        # 取得主螢幕尺寸
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        screen_width = screen_frame.size.width
        screen_height = screen_frame.size.height
        
        # 視窗尺寸和位置
        window_width = screen_width * 0.8
        window_height = 100
        x = (screen_width - window_width) / 2
        y = 50  # 距離螢幕底部
        
        # 建立視窗
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, window_width, window_height),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        
        # 視窗設定：始終在最上層，包括全螢幕應用上方
        self.window.setLevel_(NSScreenSaverWindowLevel)  # 最高層級
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.1, 0.1, 0.85))
        self.window.setHasShadow_(True)
        self.window.setMovableByWindowBackground_(True)  # 可拖動
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces |  # 在所有桌面顯示
            AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary  # 在全螢幕時也顯示
        )
        
        # 建立文字標籤
        content_view = self.window.contentView()
        self.label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, 10, window_width - 40, window_height - 20)
        )
        self.label.setStringValue_("🎤 等待說話...")
        self.label.setFont_(NSFont.boldSystemFontOfSize_(28))
        self.label.setTextColor_(NSColor.whiteColor())
        self.label.setBackgroundColor_(NSColor.clearColor())
        self.label.setBezeled_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(NSTextAlignmentCenter)
        
        content_view.addSubview_(self.label)
        
        # 顯示視窗
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


def get_audio_level(data):
    samples = np.frombuffer(data, dtype=np.int16)
    return np.abs(samples).mean()


def record_until_silence(stream):
    global running
    frames = []
    silent_chunks = 0
    chunks_for_silence = int(SILENCE_DURATION * RATE / CHUNK)
    is_speaking = False
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
        except:
            break
        level = get_audio_level(data)
        
        if level > SILENCE_THRESHOLD:
            is_speaking = True
            silent_chunks = 0
            frames.append(data)
        elif is_speaking:
            frames.append(data)
            silent_chunks += 1
            if silent_chunks > chunks_for_silence:
                break
    
    return b''.join(frames)


def transcribe_audio(audio_data):
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    result = mlx_whisper.transcribe(
        audio_np,
        path_or_hf_repo=MODEL_NAME,
        language="zh",
        task="translate",
    )
    
    return result["text"].strip()


def audio_thread(subtitle_window):
    """錄音和翻譯的執行緒"""
    global running
    
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
    mlx_whisper.transcribe(dummy, path_or_hf_repo=MODEL_NAME)
    
    subtitle_window.update_text("🎤 準備就緒，開始說話...")
    
    try:
        while running:
            audio_data = record_until_silence(stream)
            
            if not running:
                break
            
            if len(audio_data) > CHUNK * 10:
                subtitle_window.update_text("⏳ 翻譯中...")
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
    global running
    
    print("=" * 50)
    print("即時字幕浮動視窗 (macOS 原生版)")
    print("=" * 50)
    print("\n操作說明：")
    print("• 拖動字幕視窗可移動位置")
    print("• 按 Ctrl+C 關閉程式")
    print("• 說中文，會顯示英文翻譯")
    print("• 會顯示在全螢幕簡報上方")
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
    
    # 設定定時器來檢查是否需要關閉（讓 signal 有機會被處理）
    def check_running():
        if not running:
            AppHelper.stopEventLoop()
        else:
            # 每 0.5 秒檢查一次
            threading.Timer(0.5, lambda: AppHelper.callAfter(check_running)).start()
    
    AppHelper.callAfter(check_running)
    
    # 執行主迴圈
    AppHelper.runEventLoop()
    
    print("已關閉")


if __name__ == "__main__":
    main()
