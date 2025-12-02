"""
WhisperLive 即時語音轉文字客戶端（純轉錄，不翻譯）
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
    print("說話後，文字會即時顯示（保持原語言）")
    print("按 Ctrl+C 停止\n")
    print("-" * 40)
    
    client = TranscriptionClient(
        host="localhost",
        port=9090,
        lang="zh",
        translate=False,
        model="large-v3",
        use_vad=True,
        log_transcription=False,
        transcription_callback=on_transcription,
    )
    
    client()


if __name__ == "__main__":
    main()
