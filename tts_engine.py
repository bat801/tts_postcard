"""Обёртка над Silero TTS: загрузка модели, синтез, список голосов."""
import torch
from pathlib import Path
from typing import List, Optional

from config import (
    PROJECT_ROOT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    AVAILABLE_VOICES,
    SAMPLE_RATE,
)


class TTSEngine:
    """Движок синтеза речи на базе Silero TTS.
    
    Модель загружается один раз при инициализации.
    Определяет доступное устройство (CUDA/CPU) автоматически.
    """
    
    def __init__(self) -> None:
        self._model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._sample_rate = SAMPLE_RATE
        print(f"[TTSEngine] Устройство: {self._device}")
        if self._device == "cuda":
            print(f"[TTSEngine] GPU: {torch.cuda.get_device_name(0)}")
        self._load_model()
    
    def _load_model(self) -> None:
        """Загружает модель Silero TTS через torch.hub."""
        print("[TTSEngine] Загрузка модели Silero TTS...")
        print(f"[TTSEngine] Кэш моделей: {PROJECT_ROOT / '.cache' / 'torch'}")
        
        try:
            # Silero загружается через torch.hub
            self._model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language=DEFAULT_LANGUAGE,
                speaker=DEFAULT_MODEL,
                trust_repo=True,
            )
            self._model.to(self._device)
            print("[TTSEngine] Модель загружена успешно")
        except Exception as e:
            print(f"[TTSEngine] Ошибка загрузки модели: {e}")
            raise
    
    @property
    def sample_rate(self) -> int:
        return self._sample_rate
    
    @property
    def device(self) -> str:
        return self._device
    
    def list_voices(self) -> List[str]:
        """Возвращает список доступных голосов."""
        return AVAILABLE_VOICES.copy()
    
    def synthesize(self, text: str, speaker: str) -> torch.Tensor:
        """Синтезирует речь из текста.
        
        Args:
            text: Текст для синтеза (не пустой).
            speaker: Идентификатор голоса (из list_voices()).
        
        Returns:
            Тензор с аудио (1, samples) на устройстве CPU.
        
        Raises:
            ValueError: Если голос недоступен.
            RuntimeError: При ошибке синтеза.
        """
        if speaker not in AVAILABLE_VOICES:
            raise ValueError(
                f"Голос '{speaker}' недоступен. Доступные: {', '.join(AVAILABLE_VOICES)}"
            )
        
        if not text or not text.strip():
            raise ValueError("Текст для синтеза не может быть пустым")
        
        try:
            with torch.no_grad():
                # Новый API: text=... (строка), не texts=[...]
                audio = self._model.apply_tts(
                    text=text.strip(),
                    speaker=speaker,
                    sample_rate=self._sample_rate,
                )
            # audio — тензор (samples,) на CPU
            return audio.cpu()
        except Exception as e:
            raise RuntimeError(f"Ошибка синтеза: {e}") from e