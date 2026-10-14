# Голосовая открытка (Silero TTS)

Консольное приложение для синтеза речи на русском и башкирском языках с использованием модели **Silero TTS v5_cis_base_nostress**.

---

## ✅ Статус совместимости

**Python 3.14.7 проверен — работает.**  
Установлен `torch 2.14.1+cpu` (сборка под cp314 существует).  
Приложение запускается и синтезирует речь на CPU без ошибок.

---

## 📁 Структура проекта

```
voice_postcard/
├── venv/              # Виртуальное окружение (создаётся setup.bat, в .gitignore)
├── .cache/            # Кэш моделей Torch/HF (авто, в .gitignore)
├── output/            # Готовые WAV-файлы (авто, в .gitignore)
├── input/             # Текстовые файлы для синтеза (в .gitignore)
├── .gitignore
├── requirements.txt
├── config.py
├── tts_engine.py
├── postcard.py
├── main.py
├── setup.bat          # Автоматическая установка всего
├── run.bat            # Запуск приложения
└── README.md
```

---

## 🚀 Быстрый старт через .bat (рекомендуется)

### Вариант А: Полностью автоматический (два файла)

1. **Дважды кликните `setup.bat`** — создаст venv, установит torch, torchaudio и все зависимости.
2. **Дважды кликните `run.bat`** — запустит приложение.

> `setup.bat` делает всё: проверяет Python, создаёт venv, активирует его, ставит torch+torchaudio с CPU-индексом, затем `pip install -r requirements.txt`. В конце — `pause`, чтобы вы увидели результат.

### Вариант Б: Ручной (альтернатива)

Если хотите контролировать каждый шаг:

```cmd
:: 1. Создание виртуального окружения
python -m venv venv

:: 2. Активация виртуального окружения
venv\Scripts\activate.bat

:: 3. ПРОВЕРКА — venv должен быть активен!
where python
:: Ожидаемый вывод: D:\_OpenCodeProjects\tts_postcard\venv\Scripts\python.exe

:: 4. Установка PyTorch + Torchaudio (CPU)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

:: 5. Установка остальных зависимостей
pip install -r requirements.txt

:: 6. Запуск
python main.py
```

---

## 💡 Пример использования (ручной ввод)

```
==================================================
  [Voice]  ГОЛОСОВАЯ ОТКРЫТКА  --  Silero TTS
==================================================

Menu:
  [1] Create postcard (manual input)
  [2] List voices
  [3] Create postcard from file
  [0] Exit

Choose action: 1

--- Create Postcard (Manual) ---
Enter postcard text: Привет! Это тест голосовой открытки.
[INFO] Text length: 39 characters

Available voices:
   1. ru_alexandr <- default
   2. ru_ekaterina
   3. ru_roman
   4. ru_zinaida
   5. bak_alfia
   6. bak_aigul
   7. bak_miyau
   8. bak_ramilia

Select voice number or name [1]: 5
Filename (no extension) [postcard]: test_bashkir

[Postcard] Synthesizing with voice 'bak_alfia'...
[Postcard] Saved: D:\_OpenCodeProjects\tts_postcard\output\test_bashkir.wav

[OK] Postcard created: D:\_OpenCodeProjects\tts_postcard\output\test_bashkir.wav
```

---

## 📂 Создание открытки из файла (для длинных текстов)

**Проблема:** `cmd.exe` ограничивает ввод текста ~510 символами.  
**Решение:** Положите текст в `.txt` файл и используйте пункт меню **[3] Create postcard from file**.

### Подготовка

1. Создайте папку `input/` (если её нет — создастся автоматически).
2. Положите туда `.txt` файл с текстом (например, `ural_batyr.txt`).
3. Кодировка: **UTF-8** (рекомендуется) или **CP1251** (автоопределение).

### Запуск

```
Choose action: 3

--- Create Postcard from File ---
Enter file path: ural_batyr.txt

File: D:\_OpenCodeProjects\tts_postcard\input\ural_batyr.txt
Size: 12.5 KB
Characters: 8542
Lines: 156
Sentences (approx): 342
[INFO] Long text detected (> 500 chars). Will split into chunks.
[INFO] Max chunk size: 500 chars, silence between chunks: 250 ms

Available voices:
   1. ru_alexandr <- default
   ...
Select voice number or name [1]: 1
Output filename (no extension) [ural_batyr]:

[Postcard] Long text (8542 chars) - splitting into chunks...
[Postcard] Chunks: 18 (max 500 chars)
  [1/18] Synthesis: ??? ??????? ?????????...
  ...
[Postcard] Concatenating chunks...
[Postcard] Saved: D:\_OpenCodeProjects\tts_postcard\output\ural_batyr.wav (duration: 342.5s)
     Duration: 342.5s, Size: 16.2 MB

[OK] Postcard created: D:\_OpenCodeProjects\tts_postcard\output\ural_batyr.wav
```

### Поддерживаемые форматы путей

| Ввод пользователя | Куда будет искать |
|-------------------|-------------------|
| `story.txt` | `input/story.txt` |
| `texts/story.txt` | `texts/story.txt` (относительно корня проекта) |
| `C:\texts\story.txt` | Абсолютный путь как есть |

---

## 🗑 Как полностью удалить проект

```cmd
:: 1. Деактивируйте venv (если активен)
deactivate

:: 2. Удалите папку проекта
rmdir /s /q D:\_OpenCodeProjects\tts_postcard

:: 3. (Опционально) Очистка кэша pip
pip cache purge
```
> Никаких следов в реестре, автозагрузке или системных папках не остаётся. Вся изоляция — внутри папки проекта.

---

## 🔍 Проверка изоляции (что ничего не утекло вовне)

После первого запуска (`run.bat` или `python main.py`) выполните:

```cmd
:: 1. Python должен быть ТОЛЬКО в venv проекта
where python
:: Ожидается: D:\_OpenCodeProjects\tts_postcard\venv\Scripts\python.exe
:: НЕ должно быть: C:\Python314\... или %USERPROFILE%\AppData\...

:: 2. Кэш моделей — внутри проекта
dir .cache\torch
:: Должен существовать и содержать hub\snakers4_silero-models_master\...

:: 3. В системной папке пользователя кэша НЕТ
dir %USERPROFILE%\.cache\torch
:: Должен быть пуст или отсутствовать
```

Если всё совпадает — изоляция работает идеально.

---

## 🔧 Troubleshooting

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError: No module named 'torch'` | Забыли активировать venv или не выполнили установку torch. Проверьте `where python`. |
| `RuntimeError: CUDA out of memory` / нет GPU | Приложение автоматически падает на CPU. Ничего делать не нужно. |
| При первом запуске долго качает веса | Нормально. Веса (~90 MB) скачиваются в `.cache/torch/hub/` внутри проекта. |
| `ERROR: Could not find a version that satisfies requirement ...` | Устарел pip. Выполните: `python -m pip install --upgrade pip` |
| `soundfile.LibsndfileError` | На Windows `soundfile` обычно работает из коробки. Если нет — установите `libsndfile` из https://github.com/adamstark/libsndfile-windows и добавьте в PATH. |
| `torch.hub.load` падает с ошибкой сети | Проверьте интернет/прокси. Можно предскачать веса вручную и положить в `.cache/torch/hub/checkpoints/`. |
| Голос `bak_*` не работает | Модель `v5_cis_base_nostress` поддерживает башкирские голоса. Если ошибка — удалите `.cache/torch/hub/` и перезапустите. |
| `UnicodeDecodeError` при чтении файла | Сохраните `.txt` в UTF-8 (в Notepad++: Encoding → Convert to UTF-8). |
| Файл не найден при выборе пункта 3 | Проверьте имя файла и папку `input/`. Положите файл туда или укажите полный путь. |

---

## 📋 Детали реализации

- **Модель**: `silero_tts` (language=`ru`, speaker=`v5_cis_base_nostress`)
- **Sample rate**: 48000 Hz
- **Формат**: WAV (PCM_16)
- **Голоса**: 4 русские (`ru_*`) + 4 башкирские (`bak_*`)
- **Кэш**: перенаправлен в `.cache/` внутри проекта через `TORCH_HOME` / `HF_HOME`
- **Изоляция**: все зависимости только в `venv/`, никаких глобальных установок
- **Проверки**: валидация venv, версии Python, пустого текста, неверного голоса
- **Длинные тексты**: авто-разбивка на чанки по 500 символов, склейка с тишиной 250 мс

---

## 📄 Лицензия

Образовательный проект. Silero TTS — MIT License.