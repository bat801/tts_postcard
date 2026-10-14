"""Конфигурация проекта: константы, пути, проверка окружения."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# Перенаправляем кэш Torch и HuggingFace внутрь проекта
os.environ["TORCH_HOME"] = str(PROJECT_ROOT / ".cache" / "torch")
os.environ["HF_HOME"] = str(PROJECT_ROOT / ".cache" / "huggingface")

# Папки
OUTPUT_DIR = PROJECT_ROOT / "output"
INPUT_DIR = PROJECT_ROOT / "input"

# Аудио
SAMPLE_RATE = 48000

# Модель Silero
DEFAULT_LANGUAGE = "ru"
DEFAULT_MODEL = "v5_cis_base_nostress"

# Доступные голоса
AVAILABLE_VOICES = [
    "ru_alexandr",
    "ru_ekaterina",
    "ru_roman",
    "ru_zinaida",
    "bak_alfia",
    "bak_aigul",
    "bak_miyau",
    "bak_ramilia",
]

DEFAULT_VOICE = "ru_alexandr"

# === LONG TEXT HANDLING ===
# Максимальная длина чанка для одного вызова apply_tts
MAX_CHUNK_CHARS = 500
# Длительность тишины между чанками (мс)
SILENCE_BETWEEN_CHUNKS_MS = 250
# Порог: тексты длиннее этого будут разбиваться на чанки
# Silero v5_cis_base_nostress имеет лимит ~5000 токенов position encoding.
# Берем запас: 500 символов на чанк, порог 500 = всегда чанким длиннее 500.
LONG_TEXT_THRESHOLD = 500
# Аббревиатуры, которые не должны ломать предложения
ABBREVIATIONS = {
    "т.е.", "и т.д.", "т.к.", "т.д.", "пр.", "г.", "ул.", "д.", "кв.", "стр.",
    "н.э.", "до н.э.", "т.о.", "см.", "рис.", "табл.", "гл.", "ст.", "ч.", "п.",
    "№", "д.т.", "и т.п.", "напр.", "касающ.", "соотв.", "соотв-ю", "ф.", "л."
}


def ensure_venv() -> bool:
    """Проверяет, что скрипт запущен внутри виртуального окружения."""
    if sys.prefix == sys.base_prefix:
        print("[WARN] Virtual environment NOT activated!")
        print("   Run: venv\\Scripts\\activate.bat (cmd) or venv\\Scripts\\Activate.ps1 (PowerShell)")
        return False
    return True


def check_python_version() -> bool:
    """Проверяет совместимость версии Python."""
    major, minor = sys.version_info[:2]
    if major > 3 or (major == 3 and minor >= 14):
        print(f"[WARN] Python {major}.{minor} may not be fully compatible with PyTorch/Silero.")
        print("   Recommended: Python 3.11 or 3.12.")
        print("   Continuing anyway...")
    return True