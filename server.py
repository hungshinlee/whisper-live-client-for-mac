"""
WhisperLive 本地伺服器
"""
import signal
import sys
from whisper_live.server import TranscriptionServer


server = None


def cleanup(signum, frame):
    """清理並退出"""
    print("\n\n正在關閉伺服器...")
    sys.exit(0)


def main():
    global server
    
    # 註冊信號處理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("啟動 WhisperLive 伺服器...")
    print("伺服器將在 port 9090 上運行")
    print("按 Ctrl+C 停止\n")
    
    server = TranscriptionServer()
    server.run(
        host="0.0.0.0",
        port=9090,
        backend="faster_whisper",
    )


if __name__ == "__main__":
    main()
