"""
MLX Whisper 即時語音轉文字（使用 Apple Silicon GPU）
純轉錄版本（不翻譯）
"""
import numpy as np
import pyaudio
import mlx_whisper

# 模型設定 - 使用 MLX 優化版本
MODEL_NAME = "mlx-community/whisper-large-v3-turbo"

# 錄音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500      # 靜音門檻
SILENCE_DURATION = 1.5       # 靜音多久後開始辨識（秒）


def get_audio_level(data):
    """計算音量"""
    samples = np.frombuffer(data, dtype=np.int16)
    return np.abs(samples).mean()


def record_until_silence(stream):
    """錄音直到靜音"""
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
    """使用 MLX Whisper 辨識"""
    # 轉換為 numpy array
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    result = mlx_whisper.transcribe(
        audio_np,
        path_or_hf_repo=MODEL_NAME,
        language="zh",          # 輸入語言：中文
        task="transcribe",      # 純轉錄（X->X，保持原語言）
    )
    
    return result["text"].strip()


def main():
    print("=" * 50)
    print("MLX Whisper 即時語音轉文字")
    print("使用 Apple Silicon GPU 加速")
    print(f"模型: {MODEL_NAME}")
    print("=" * 50)
    print("\n說話後會顯示文字（保持原語言）")
    print("按 Ctrl+C 停止\n")
    print("-" * 50)
    
    # 初始化 PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    print("正在載入模型（首次需要下載，約 1.6GB）...")
    
    # 預熱模型
    dummy = np.zeros(RATE, dtype=np.float32)
    mlx_whisper.transcribe(dummy, path_or_hf_repo=MODEL_NAME)
    print("模型載入完成！開始監聽...\n")
    
    try:
        while True:
            print("🎤 等待說話...", end="\r")
            audio_data = record_until_silence(stream)
            
            if len(audio_data) > CHUNK * 10:  # 確保有足夠的音訊
                print("⏳ 辨識中...   ", end="\r")
                text = transcribe_audio(audio_data)
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
