"""Голосовая открытка — консольное приложение для синтеза речи Silero TTS."""
import os
import sys
from pathlib import Path

# ВАЖНО: Установка переменных окружения для кэша ДО импорта torch
PROJECT_ROOT = Path(__file__).parent.resolve()
os.environ["TORCH_HOME"] = str(PROJECT_ROOT / ".cache" / "torch")
os.environ["HF_HOME"] = str(PROJECT_ROOT / ".cache" / "huggingface")

import torch
from config import (
    ensure_venv, check_python_version,
    AVAILABLE_VOICES, DEFAULT_VOICE,
    LONG_TEXT_THRESHOLD, MAX_CHUNK_CHARS, SILENCE_BETWEEN_CHUNKS_MS,
    INPUT_DIR
)
from tts_engine import TTSEngine
from postcard import Postcard


class Tee:
    """Перенаправляет stdout/stderr и в консоль, и в файл."""
    def __init__(self, *streams):
        self.streams = streams
        self._closed = False
    
    def write(self, data):
        if self._closed:
            return
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except ValueError:
                pass  # stream closed
    
    def flush(self):
        if self._closed:
            return
        for s in self.streams:
            try:
                s.flush()
            except ValueError:
                pass
    
    def close(self):
        self._closed = True


def print_header() -> None:
    print("=" * 50)
    print("  [Voice]  ГОЛОСОВАЯ ОТКРЫТКА  --  Silero TTS")
    print("=" * 50)
    print()


def print_menu() -> None:
    print("Menu:")
    print("  [1] Create postcard (manual input)")
    print("  [2] List voices")
    print("  [3] Create postcard from file")
    print("  [0] Exit")
    print()


def print_voices() -> None:
    print("\nAvailable voices:")
    for i, voice in enumerate(AVAILABLE_VOICES, 1):
        marker = " <- default" if voice == DEFAULT_VOICE else ""
        print(f"  {i:2}. {voice}{marker}")
    print()


def get_user_input(prompt: str, default: str = "") -> str:
    """Получает ввод пользователя с поддержкой значения по умолчанию."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    try:
        value = input(prompt).strip()
        return value if value else default
    except (KeyboardInterrupt, EOFError):
        print("\n[Interrupted]")
        return ""


def resolve_input_path(user_input: str) -> Path:
    """Преобразует пользовательский ввод в путь к файлу."""
    path = Path(user_input).expanduser()
    
    # Если абсолютный путь — используем как есть
    if path.is_absolute():
        return path
    
    # Если путь содержит разделители директорий — относительно PROJECT_ROOT
    if path.parts != (path.name,):
        return (PROJECT_ROOT / path).resolve()
    
    # Иначе ищем в INPUT_DIR
    return (INPUT_DIR / path).resolve()


def read_text_file(filepath: Path) -> str:
    """Читает текстовый файл с автоопределением кодировки (UTF-8 -> CP1251)."""
    # Сначала пробуем UTF-8
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass
    
    # Затем CP1251
    try:
        return filepath.read_text(encoding="cp1251")
    except UnicodeDecodeError:
        pass
    
    raise UnicodeDecodeError(
        "utf-8", b"", 0, 1, 
        "File encoding not supported. Please save as UTF-8 or CP1251."
    )


def count_sentences(text: str) -> int:
    """Грубая оценка количества предложений."""
    import re
    return len(re.findall(r'[.!?…]+', text))


def create_postcard_interactive(engine: TTSEngine, postcard: Postcard) -> None:
    """Интерактивное создание открытки (ручной ввод текста)."""
    print("\n--- Create Postcard (Manual) ---")
    
    # Текст
    text = get_user_input("Enter postcard text")
    if not text:
        print("[ERROR] Text cannot be empty")
        return
    
    # Показ длины и предупреждение о чанках
    text_len = len(text)
    print(f"[INFO] Text length: {text_len} characters")
    if text_len > LONG_TEXT_THRESHOLD:
        print(f"[INFO] Long text detected (> {LONG_TEXT_THRESHOLD} chars). Will split into chunks.")
        print(f"[INFO] Max chunk size: {MAX_CHUNK_CHARS} chars, silence between chunks: {SILENCE_BETWEEN_CHUNKS_MS} ms")
    
    # Голос
    print_voices()
    voice_choice = get_user_input("Select voice number or name", str(AVAILABLE_VOICES.index(DEFAULT_VOICE) + 1))
    
    try:
        idx = int(voice_choice) - 1
        if 0 <= idx < len(AVAILABLE_VOICES):
            speaker = AVAILABLE_VOICES[idx]
        else:
            speaker = voice_choice
    except ValueError:
        speaker = voice_choice
    
    if speaker not in AVAILABLE_VOICES:
        print(f"[WARN] Voice '{speaker}' unavailable. Using '{DEFAULT_VOICE}'")
        speaker = DEFAULT_VOICE
    
    # Имя файла
    filename = get_user_input("Filename (no extension)", "postcard")
    
    # Создание
    try:
        output_path = postcard.create(text=text, speaker=speaker, filename=filename)
        print(f"\n[OK] Postcard created: {output_path}")
    except (ValueError, RuntimeError) as e:
        print(f"\n[ERROR] {e}")


def create_postcard_from_file(engine: TTSEngine, postcard: Postcard) -> None:
    """Создание открытки из текстового файла."""
    print("\n--- Create Postcard from File ---")
    
    # 1. Запрос пути к файлу
    file_input = get_user_input("Enter file path (e.g. story.txt or input/story.txt or full path)")
    if not file_input:
        print("[ERROR] No file path provided")
        return
    
    # 2. Разрешение пути
    filepath = resolve_input_path(file_input)
    
    # 3. Проверка существования
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        return
    
    if not filepath.is_file():
        print(f"[ERROR] Not a file: {filepath}")
        return
    
    # 4. Проверка размера (предупреждение для > 1MB)
    file_size = filepath.stat().st_size
    if file_size > 1_000_000:
        print(f"[WARN] File is large ({file_size / 1024 / 1024:.1f} MB). Synthesis may take long.")
        confirm = get_user_input("Continue? (y/n)", "n").lower()
        if confirm != "y":
            print("Cancelled.")
            return
    
    # 5. Чтение файла с автоопределением кодировки
    try:
        text = read_text_file(filepath)
    except UnicodeDecodeError as e:
        print(f"[ERROR] {e}")
        return
    except PermissionError:
        print(f"[ERROR] Permission denied: {filepath}")
        return
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return
    
    # 6. Валидация содержимого
    if not text or not text.strip():
        print("[ERROR] File is empty or contains only whitespace")
        return
    
    text = text.strip()
    
    # 7. Показ информации о файле
    char_count = len(text)
    line_count = len(text.splitlines())
    sentence_count = count_sentences(text)
    
    print(f"\nFile: {filepath}")
    print(f"Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
    print(f"Characters: {char_count}")
    print(f"Lines: {line_count}")
    print(f"Sentences (approx): {sentence_count}")
    
    if char_count > LONG_TEXT_THRESHOLD:
        print(f"[INFO] Long text detected (> {LONG_TEXT_THRESHOLD} chars). Will split into chunks.")
        print(f"[INFO] Max chunk size: {MAX_CHUNK_CHARS} chars, silence between chunks: {SILENCE_BETWEEN_CHUNKS_MS} ms")
    
    # 8. Подтверждение для очень длинных текстов (>50000 символов)
    if char_count > 50000:
        print(f"[WARN] Very long text ({char_count} chars). Synthesis will take significant time.")
        confirm = get_user_input("Continue? (y/n)", "n").lower()
        if confirm != "y":
            print("Cancelled.")
            return
    
    # 9. Выбор голоса
    print_voices()
    voice_choice = get_user_input("Select voice number or name", str(AVAILABLE_VOICES.index(DEFAULT_VOICE) + 1))
    
    try:
        idx = int(voice_choice) - 1
        if 0 <= idx < len(AVAILABLE_VOICES):
            speaker = AVAILABLE_VOICES[idx]
        else:
            speaker = voice_choice
    except ValueError:
        speaker = voice_choice
    
    if speaker not in AVAILABLE_VOICES:
        print(f"[WARN] Voice '{speaker}' unavailable. Using '{DEFAULT_VOICE}'")
        speaker = DEFAULT_VOICE
    
    # 10. Имя выходного файла (по умолчанию — имя входного без расширения)
    default_filename = filepath.stem
    filename = get_user_input("Output filename (no extension)", default_filename)
    
    # 11. Создание
    try:
        output_path = postcard.create(text=text, speaker=speaker, filename=filename)
        # Показать дополнительную информацию
        output_file = Path(output_path)
        out_size = output_file.stat().st_size
        # Оценка длительности (sample_rate = 48000)
        import soundfile as sf
        data, sr = sf.read(output_path)
        duration = len(data) / sr
        print(f"\n[OK] Postcard created: {output_path}")
        print(f"     Duration: {duration:.1f}s, Size: {out_size / 1024:.1f} KB")
    except (ValueError, RuntimeError) as e:
        print(f"\n[ERROR] {e}")


def main() -> int:
    # --- Tee logging to run.log ---
    log_path = PROJECT_ROOT / "run.log"
    log_file = open(log_path, "w", encoding="utf-8")
    tee_out = Tee(sys.stdout, log_file)
    tee_err = Tee(sys.stderr, log_file)
    sys.stdout = tee_out
    sys.stderr = tee_err
    # -------------------------------
    
    print_header()
    
    # Проверка окружения
    if not check_python_version():
        log_file.close()
        tee_out.close()
        tee_err.close()
        return 1
    
    if not ensure_venv():
        print("Activate venv and restart.")
        log_file.close()
        tee_out.close()
        tee_err.close()
        return 1
    
    print(f"[main] Python: {sys.version.split()[0]}")
    print(f"[main] Torch: {torch.__version__}")
    print(f"[main] CUDA available: {torch.cuda.is_available()}")
    print()
    
    # Инициализация движка
    try:
        engine = TTSEngine()
    except Exception as e:
        print(f"[ERROR] Failed to init TTS: {e}")
        log_file.close()
        tee_out.close()
        tee_err.close()
        return 1
    
    postcard = Postcard(engine)
    
    # Основной цикл
    while True:
        try:
            print_menu()
            choice = get_user_input("Choose action")
            
            if choice == "1":
                create_postcard_interactive(engine, postcard)
            elif choice == "2":
                print_voices()
            elif choice == "3":
                create_postcard_from_file(engine, postcard)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("[ERROR] Invalid choice. Enter 0, 1, 2 or 3.")
        
        except KeyboardInterrupt:
            print("\n\n[Interrupted by user]")
            break
        except EOFError:
            print("\n\n[Input ended]")
            break
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
    
    log_file.close()
    tee_out.close()
    tee_err.close()
    print(f"[INFO] Log saved to: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())