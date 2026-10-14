"""Бизнес-логика: создание голосовой открытки, валидация, сохранение.
Поддержка длинных текстов через разбивку на чанки."""
import re
import numpy as np
import soundfile as sf
import torch
from pathlib import Path
from typing import List, Tuple

from config import (
    OUTPUT_DIR, AVAILABLE_VOICES, DEFAULT_VOICE,
    MAX_CHUNK_CHARS, SILENCE_BETWEEN_CHUNKS_MS,
    LONG_TEXT_THRESHOLD, ABBREVIATIONS
)
from tts_engine import TTSEngine


class Postcard:
    """Создание и сохранение голосовой открытки."""

    def __init__(self, engine: TTSEngine) -> None:
        self._engine = engine
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        text: str,
        speaker: str = DEFAULT_VOICE,
        filename: str = "postcard",
    ) -> str:
        """Создаёт голосовую открытку и сохраняет в WAV.
        
        Автоматически определяет: короткий текст -> один синтез,
        длинный текст -> разбивка на чанки с прогрессом.
        """
        # Валидация текста
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Валидация голоса
        if speaker not in AVAILABLE_VOICES:
            raise ValueError(
                f"Voice '{speaker}' unavailable. Available: {', '.join(AVAILABLE_VOICES)}"
            )
        
        # Валидация имени файла
        safe_name = self._sanitize_filename(filename)
        if not safe_name:
            raise ValueError("Filename cannot be empty after sanitization")
        
        output_path = OUTPUT_DIR / f"{safe_name}.wav"
        text = text.strip()
        
        # Выбор стратегии: короткий или длинный текст
        if len(text) <= LONG_TEXT_THRESHOLD:
            return self._create_short(text, speaker, output_path)
        else:
            return self._create_long(text, speaker, output_path)

    def _create_short(self, text: str, speaker: str, output_path: Path) -> str:
        """Синтез короткого текста одним вызовом (старое поведение).
        Если модель сообщает 'too long' — фоллбэк на чанки."""
        print(f"[Postcard] Synthesizing with voice '{speaker}'...")
        try:
            audio_tensor = self._engine.synthesize(text, speaker)
        except RuntimeError as e:
            if "too long" in str(e).lower():
                print(f"[Postcard] Text too long for single call, falling back to chunks...")
                return self._create_long(text, speaker, output_path)
            raise
        self._save_audio(audio_tensor, output_path)
        print(f"[Postcard] Saved: {output_path}")
        return str(output_path.resolve())

    def _create_long(self, text: str, speaker: str, output_path: Path) -> str:
        """Синтез длинного текста с разбивкой на чанки."""
        print(f"[Postcard] Long text ({len(text)} chars) - splitting into chunks...")
        
        chunks = self._split_into_chunks(text)
        total = len(chunks)
        print(f"[Postcard] Chunks: {total} (max {MAX_CHUNK_CHARS} chars)")
        
        audio_chunks: List[torch.Tensor] = []
        failed_chunks: List[Tuple[int, str]] = []
        
        for i, chunk_text in enumerate(chunks, 1):
            # Safe preview for console (cp1251 may not support all chars)
            preview = chunk_text[:60].encode('ascii', 'replace').decode('ascii')
            print(f"  [{i}/{total}] Synthesis: {preview}...")
            try:
                audio = self._engine.synthesize(chunk_text, speaker)
                audio_chunks.append(audio)
            except Exception as e:
                print(f"  [ERROR] Chunk {i} failed: {e}")
                failed_chunks.append((i, str(e)))
        
        if not audio_chunks:
            raise RuntimeError("Все чанки упали с ошибкой")
        
        if failed_chunks:
            print(f"[WARN] Failed chunks: {len(failed_chunks)}/{total}")
            for idx, err in failed_chunks:
                print(f"    Chunk {idx}: {err}")
        
        # Склейка с тишиной между чанками
        print("[Postcard] Concatenating chunks...")
        final_audio = self._concatenate_chunks(audio_chunks)
        
        self._save_audio(final_audio, output_path)
        print(f"[Postcard] Saved: {output_path} (duration: {len(final_audio)/48000:.1f}s)")
        return str(output_path.resolve())

    def _split_into_chunks(self, text: str) -> List[str]:
        """Разбивает текст на чанки по предложениям с защитой аббревиатур."""
        # 1. Защита аббревиатур
        protected = text
        placeholders = {}
        for i, abbr in enumerate(ABBREVIATIONS):
            placeholder = f"__ABBR_{i}__"
            if abbr in protected:
                protected = protected.replace(abbr, placeholder)
                placeholders[placeholder] = abbr
        
        # 2. Разбивка по концам предложений
        # Регулярка: точка/воскл/вопр/многоточие, за которыми пробел или конец строки
        sentences = re.split(r'(?<=[.!?…])\s+', protected)
        
        # 3. Восстановление аббревиатур
        restored = []
        for sent in sentences:
            for ph, abbr in placeholders.items():
                sent = sent.replace(ph, abbr)
            s = sent.strip()
            if s:
                restored.append(s)
        
        # 4. Упаковка в чанки по MAX_CHUNK_CHARS
        chunks = []
        current = ""
        for sent in restored:
            # Если предложение само по себе больше лимита — режем дополнительно
            if len(sent) > MAX_CHUNK_CHARS:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_long_sentence(sent))
                continue
            
            # Обычная упаковка
            if len(current) + len(sent) + 1 <= MAX_CHUNK_CHARS:
                current = (current + " " + sent).strip()
            else:
                if current:
                    chunks.append(current)
                current = sent
        
        if current:
            chunks.append(current)
        
        return chunks

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Дополнительная разбивка длинного предложения: по запятым, потом по словам."""
        chunks = []
        
        # Сначала по запятым
        parts = re.split(r'(?<=,)\s+', sentence)
        current = ""
        for part in parts:
            if len(part) > MAX_CHUNK_CHARS:
                if current:
                    chunks.append(current)
                    current = ""
                # Рекурсивно режем по словам
                chunks.extend(self._word_wrap(part))
                continue
            
            if len(current) + len(part) + 1 <= MAX_CHUNK_CHARS:
                current = (current + " " + part).strip()
            else:
                if current:
                    chunks.append(current)
                current = part
        
        if current:
            chunks.append(current)
        return chunks

    def _word_wrap(self, text: str) -> List[str]:
        """Разбивка по словам с ограничением длины."""
        words = text.split()
        chunks = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 <= MAX_CHUNK_CHARS:
                current = (current + " " + w).strip()
            else:
                if current:
                    chunks.append(current)
                current = w
        if current:
            chunks.append(current)
        return chunks

    def _concatenate_chunks(self, chunks: List[torch.Tensor]) -> torch.Tensor:
        """Склеивает аудио-чанки с тишиной между ними."""
        if len(chunks) == 1:
            return chunks[0]
        
        silence_samples = int(self._engine.sample_rate * SILENCE_BETWEEN_CHUNKS_MS / 1000)
        silence = torch.zeros(silence_samples, dtype=chunks[0].dtype)
        
        parts = []
        for i, chunk in enumerate(chunks):
            parts.append(chunk)
            if i < len(chunks) - 1:
                parts.append(silence)
        
        return torch.cat(parts)

    def _save_audio(self, audio_tensor: torch.Tensor, output_path: Path) -> None:
        """Сохраняет тензор в WAV через soundfile."""
        audio_numpy = audio_tensor.numpy()
        try:
            sf.write(
                file=output_path,
                data=audio_numpy,
                samplerate=self._engine.sample_rate,
                subtype="PCM_16",
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка сохранения WAV: {e}") from e

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Убирает недопустимые для Windows символы из имени файла."""
        forbidden = '<>:"/\\|?*'
        cleaned = "".join(c for c in name if c not in forbidden)
        return cleaned.strip().rstrip(".")[:200]