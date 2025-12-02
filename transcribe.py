"""
WhisperLive 即時語音轉文字客戶端（中文翻譯成英文）
"""
from whisper_live.client import TranscriptionClient


# 記錄已顯示的句子，避免重複
displayed_segments = set()


def on_transcription(text, segments):
    """自定義輸出：每句換行顯示"""
    for seg in segments:
        # 只顯示已完成的句子，避免重複
        if seg.get("completed", False):
            seg_id = (seg.get("start"), seg.get("end"), seg.get("text"))
            if seg_id not in displayed_segments:
                displayed_segments.add(seg_id)
                print(seg["text"].strip())


def main():
    print("正在連接 WhisperLive 伺服器...")
    print("說中文，會即時翻譯成英文")
    print("按 Ctrl+C 停止\n")
    print("-" * 40)
    
    client = TranscriptionClient(
        host="localhost",
        port=9090,
        lang="zh",
        translate=True,
        model="medium",
        use_vad=True,
        log_transcription=False,            # 關閉預設輸出
        transcription_callback=on_transcription,  # 使用自定義輸出
    )
    
    client()


if __name__ == "__main__":
    main()
