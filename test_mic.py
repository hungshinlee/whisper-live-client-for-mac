"""
麥克風測試工具
"""
import pyaudio
import struct
import math

def main():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    # 列出所有音訊裝置
    print("=== 可用的音訊裝置 ===\n")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:  # 只顯示有輸入的裝置
            print(f"[{i}] {info['name']}")
            print(f"    輸入通道: {info['maxInputChannels']}")
            print()
    
    # 取得預設輸入裝置
    default_input = p.get_default_input_device_info()
    print(f"=== 預設輸入裝置 ===")
    print(f"名稱: {default_input['name']}")
    print(f"Index: {default_input['index']}\n")
    
    # 開始錄音測試
    print("=== 麥克風音量測試 ===")
    print("對著麥克風說話，觀察音量條")
    print("按 Ctrl+C 停止\n")
    
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            # 計算音量 (RMS)
            samples = struct.unpack(f'{CHUNK}h', data)
            rms = math.sqrt(sum(s**2 for s in samples) / CHUNK)
            
            # 顯示音量條
            bar_length = int(rms / 500)
            bar = '█' * min(bar_length, 50)
            print(f"\r音量: {bar:<50} {rms:>6.0f}", end='', flush=True)
            
    except KeyboardInterrupt:
        print("\n\n測試結束")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()
