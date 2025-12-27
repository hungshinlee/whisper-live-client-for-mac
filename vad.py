"""
Silero VAD 語音活動偵測模組

使用 Silero VAD 模型來偵測語音，比簡單的音量門檻更準確。
能區分人聲和背景噪音（鍵盤聲、空調聲等）。
"""
from collections import deque
from dataclasses import dataclass

from pysilero_vad import SileroVoiceActivityDetector


@dataclass
class VADConfig:
    """VAD 設定"""
    # 語音機率門檻（0.0~1.0），越高越嚴格
    speech_threshold: float = 0.5
    
    # 語音結束後，需要多長的靜音才算真正結束（秒）
    min_silence_duration: float = 1.0
    
    # 最短語音長度（秒），太短的語音會被忽略
    min_speech_duration: float = 0.3
    
    # 語音前的緩衝（秒），保留語音開始前的一小段音訊
    speech_pad_duration: float = 0.1
    
    # 取樣率
    sample_rate: int = 16000


class SileroVAD:
    """
    Silero VAD 封裝類別
    
    使用方式：
        vad = SileroVAD()
        
        # 持續餵入音訊 chunk
        while True:
            chunk = stream.read(...)
            result = vad.process(chunk)
            
            if result is not None:
                # result 是完整的語音片段
                transcribe(result)
    """
    
    def __init__(self, config: VADConfig | None = None):
        self.config = config or VADConfig()
        self.vad = SileroVoiceActivityDetector()
        
        # 計算 chunk 大小（Silero VAD 需要特定大小）
        self.chunk_samples = self.vad.chunk_samples()
        self.chunk_bytes = self.vad.chunk_bytes()
        
        # 計算各種時間相關的 chunk 數量
        chunks_per_second = self.config.sample_rate / self.chunk_samples
        self.silence_chunks_threshold = int(
            self.config.min_silence_duration * chunks_per_second
        )
        self.min_speech_chunks = int(
            self.config.min_speech_duration * chunks_per_second
        )
        self.pad_chunks = int(
            self.config.speech_pad_duration * chunks_per_second
        )
        
        # 狀態
        self.reset()
    
    def reset(self):
        """重置狀態"""
        self.is_speaking = False
        self.silence_chunks = 0
        self.speech_chunks = 0
        self.audio_buffer = []
        # 保留最近的音訊作為前導緩衝
        self.pre_buffer = deque(maxlen=max(1, self.pad_chunks))
    
    def process(self, audio_bytes: bytes) -> bytes | None:
        """
        處理音訊 chunk
        
        Args:
            audio_bytes: 16kHz 16-bit mono PCM 音訊資料
            
        Returns:
            如果偵測到完整的語音片段，返回該片段的 bytes
            否則返回 None
        """
        # 確保 chunk 大小正確
        if len(audio_bytes) != self.chunk_bytes:
            # 如果大小不對，嘗試分割處理
            return self._process_variable_chunk(audio_bytes)
        
        # 取得語音機率
        prob = self.vad(audio_bytes)
        is_speech = prob >= self.config.speech_threshold
        
        if is_speech:
            if not self.is_speaking:
                # 語音開始
                self.is_speaking = True
                self.silence_chunks = 0
                self.speech_chunks = 0
                # 加入前導緩衝
                self.audio_buffer = list(self.pre_buffer)
            
            self.audio_buffer.append(audio_bytes)
            self.speech_chunks += 1
            self.silence_chunks = 0
        else:
            # 更新前導緩衝
            self.pre_buffer.append(audio_bytes)
            
            if self.is_speaking:
                # 正在說話但遇到靜音
                self.audio_buffer.append(audio_bytes)
                self.silence_chunks += 1
                
                if self.silence_chunks >= self.silence_chunks_threshold:
                    # 靜音夠長，語音結束
                    self.is_speaking = False
                    
                    # 檢查語音是否夠長
                    if self.speech_chunks >= self.min_speech_chunks:
                        result = b''.join(self.audio_buffer)
                        self.reset()
                        return result
                    else:
                        # 太短，忽略
                        self.reset()
        
        return None
    
    def _process_variable_chunk(self, audio_bytes: bytes) -> bytes | None:
        """處理不是標準大小的 chunk"""
        result = None
        
        # 分割成標準大小的 chunks
        offset = 0
        while offset + self.chunk_bytes <= len(audio_bytes):
            chunk = audio_bytes[offset:offset + self.chunk_bytes]
            chunk_result = self.process(chunk)
            if chunk_result is not None:
                result = chunk_result
            offset += self.chunk_bytes
        
        return result
    
    def finalize(self) -> bytes | None:
        """
        結束處理，返回任何剩餘的語音
        """
        if self.is_speaking and self.speech_chunks >= self.min_speech_chunks:
            result = b''.join(self.audio_buffer)
            self.reset()
            return result
        
        self.reset()
        return None
