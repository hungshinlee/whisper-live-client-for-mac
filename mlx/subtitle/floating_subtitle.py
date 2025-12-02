"""
即時字幕浮動視窗 - 適用於簡報時顯示翻譯字幕
使用 MLX Whisper 進行中文到英文的即時翻譯
字幕視窗會顯示在所有視窗最上層，包括全螢幕簡報
"""
import tkinter as tk
import threading
import queue
import numpy as np
import pyaudio
import mlx_whisper

# 模型設定（使用支援翻譯的完整版）
MODEL_NAME = "mlx-community/whisper-large-v3-mlx"

# 錄音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.2  # 稍微縮短，讓字幕更即時


class SubtitleWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("即時字幕")
        
        # 取得螢幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 視窗設定：底部置中，寬度為螢幕 80%
        window_width = int(screen_width * 0.8)
        window_height = 120
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 50  # 距離底部 50px
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 視窗樣式：無邊框、半透明、始終在最上層
        self.root.overrideredirect(True)  # 移除標題列
        self.root.attributes('-topmost', True)  # 始終在最上層
        self.root.attributes('-alpha', 0.85)  # 透明度
        
        # macOS 特殊設定：讓視窗顯示在全螢幕應用上方
        try:
            self.root.call('::tk::unsupported::MacWindowStyle', 'style', 
                          self.root._w, 'plain', 'none')
            # 設定視窗層級為螢幕保護程式級別（最高）
            self.root.attributes('-topmost', True)
        except:
            pass
        
        # 背景顏色（深色半透明）
        self.root.configure(bg='#1a1a1a')
        
        # 字幕文字
        self.label = tk.Label(
            self.root,
            text="🎤 等待說話...",
            font=("Helvetica Neue", 32, "bold"),
            fg='white',
            bg='#1a1a1a',
            wraplength=window_width - 40,
            justify='center'
        )
        self.label.pack(expand=True, fill='both', padx=20, pady=10)
        
        # 綁定拖動功能
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.on_drag)
        
        # 綁定右鍵關閉
        self.label.bind('<Button-2>', lambda e: self.root.quit())  # 中鍵
        self.label.bind('<Button-3>', lambda e: self.root.quit())  # 右鍵
        
        # 綁定 Escape 鍵關閉
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # 訊息佇列
        self.message_queue = queue.Queue()
        
        # 定期檢查佇列
        self.check_queue()
    
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def check_queue(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.label.config(text=message)
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)
    
    def update_text(self, text):
        self.message_queue.put(text)
    
    def run(self):
        self.root.mainloop()


def get_audio_level(data):
    samples = np.frombuffer(data, dtype=np.int16)
    return np.abs(samples).mean()


def record_until_silence(stream):
    frames = []
    silent_chunks = 0
    chunks_for_silence = int(SILENCE_DURATION * RATE / CHUNK)
    is_speaking = False
    
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
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
        task="translate",  # 翻譯成英文
    )
    
    return result["text"].strip()


def audio_thread(subtitle_window):
    """錄音和翻譯的執行緒"""
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
        while True:
            audio_data = record_until_silence(stream)
            
            if len(audio_data) > CHUNK * 10:
                subtitle_window.update_text("⏳ 翻譯中...")
                text = transcribe_audio(audio_data)
                if text:
                    subtitle_window.update_text(text)
    
    except Exception as e:
        subtitle_window.update_text(f"錯誤: {str(e)}")
    
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def main():
    print("=" * 50)
    print("即時字幕浮動視窗")
    print("=" * 50)
    print("\n操作說明：")
    print("• 拖動字幕視窗可移動位置")
    print("• 按 ESC 或右鍵點擊關閉")
    print("• 說中文，會顯示英文翻譯")
    print("\n正在啟動...\n")
    
    # 建立字幕視窗
    subtitle_window = SubtitleWindow()
    
    # 在背景執行緒中執行錄音和翻譯
    thread = threading.Thread(target=audio_thread, args=(subtitle_window,), daemon=True)
    thread.start()
    
    # 執行 GUI 主迴圈
    subtitle_window.run()
    
    print("\n已關閉")


if __name__ == "__main__":
    main()
