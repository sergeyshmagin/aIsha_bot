import os
import aiohttp
import subprocess
import logging
import shutil
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from uuid import uuid4
from dotenv import load_dotenv
from config import LOG_DIR

# Логирование ошибок
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOG_DIR, 'transcribe_errors.log'), level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TEMP_DIR = "storage"
os.makedirs(TEMP_DIR, exist_ok=True)

from handlers.general import bot  # Импортируем объект бота

MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24 МБ


def error_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Повторить"))
    return markup

@bot.message_handler(func=lambda m: m.text == "Повторить")
async def repeat_audio_instruction(message: Message):
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл или голосовое сообщение в этот чат ещё раз.",
        reply_markup=None
    )

@bot.message_handler(content_types=['voice', 'audio'])
async def transcribe_audio(message: Message):
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(message.chat.id, "⏳ Файл получен, начинаю обработку...")

    file_id = message.voice.file_id if message.voice else message.audio.file_id
    ext = ".ogg" if message.voice else ".mp3"
    temp_file = os.path.join(TEMP_DIR, f"{uuid4()}{ext}")

    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    with open(temp_file, "wb") as f:
        f.write(downloaded_file)

    # Конвертируем в mp3 для Whisper
    temp_file_mp3 = temp_file.rsplit('.', 1)[0] + '.mp3'
    subprocess.run(["ffmpeg", "-y", "-i", temp_file, temp_file_mp3])

    file_size = os.path.getsize(temp_file_mp3)
    # Оценка времени ожидания (примерно 1 минута на 5 минут аудио)
    approx_minutes = max(1, int(file_size / (1024 * 1024 * 2)))
    progress_msg = await bot.send_message(
        message.chat.id,
        f"⏳ Обработка аудиофайла...\nОжидаемое время: ~{approx_minutes} мин."
    )

    if file_size <= 25 * 1024 * 1024:
        try:
            await bot.edit_message_text(
                "📝 Расшифровка...",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id
            )
            transcription = await whisper_transcribe(temp_file_mp3)
            await send_long_message(bot, message.chat.id, f"📝 Расшифровка:\n\n{transcription}")
        except Exception as e:
            logging.error(f"Ошибка при расшифровке аудио: {e}")
            await bot.edit_message_text(
                f"❌ Ошибка при расшифровке аудио.\n\n{str(e)}",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id,
                reply_markup=error_keyboard()
            )
            raise e
        finally:
            os.remove(temp_file)
            os.remove(temp_file_mp3)
        return

    # Если файл большой — разбиваем по паузам через ffmpeg
    await bot.edit_message_text(
        "🔪 Нарезка аудио по паузам...",
        chat_id=message.chat.id,
        message_id=progress_msg.message_id
    )
    chunk_dir = os.path.join(TEMP_DIR, f"chunks_{uuid4()}")
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_paths = split_audio_by_silence_ffmpeg(temp_file, chunk_dir)
    os.remove(temp_file)
    os.remove(temp_file_mp3)

    await bot.edit_message_text(
        f"🔪 Нарезка завершена. Кусков: {len(chunk_paths)}. Начинаю расшифровку...",
        chat_id=message.chat.id,
        message_id=progress_msg.message_id
    )

    transcribed_text = ""
    for i, part_path in enumerate(chunk_paths):
        # Конвертируем каждый кусок в mp3
        part_path_mp3 = part_path.rsplit('.', 1)[0] + '.mp3'
        subprocess.run(["ffmpeg", "-y", "-i", part_path, part_path_mp3])
        # Проверяем размер каждого куска
        if os.path.getsize(part_path_mp3) > 25 * 1024 * 1024:
            await bot.send_message(message.chat.id, f"❌ Кусок {i+1} слишком большой для обработки. Пропущен.")
            os.remove(part_path)
            os.remove(part_path_mp3)
            continue
        try:
            await bot.edit_message_text(
                f"📝 Расшифровка части {i+1} из {len(chunk_paths)}...",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id
            )
            part_text = await whisper_transcribe(part_path_mp3)
            transcribed_text += f"\n--- Часть {i+1} ---\n{part_text}\n"
        except Exception as e:
            logging.error(f"Ошибка при расшифровке части {i+1}: {e}")
            await bot.send_message(
                message.chat.id,
                f"❌ Ошибка при расшифровке части {i+1}.\n\n{str(e)}",
                reply_markup=error_keyboard()
            )
            transcribed_text += f"\n--- Часть {i+1} ---\nОшибка при расшифровке.\n"
        finally:
            os.remove(part_path)
            os.remove(part_path_mp3)
    shutil.rmtree(chunk_dir, ignore_errors=True)
    await bot.edit_message_text(
        "✅ Обработка завершена! Отправляю результат...",
        chat_id=message.chat.id,
        message_id=progress_msg.message_id
    )
    await send_long_message(bot, message.chat.id, f"📝 Расшифровка по частям:\n{transcribed_text}")


def split_audio_by_silence_ffmpeg(input_path, output_dir, min_silence_len=0.7, silence_thresh=-30):
    """
    Нарезает аудиофайл на части по паузам с помощью ffmpeg.
    min_silence_len — минимальная длина тишины (секунды)
    silence_thresh — уровень тишины в dB (относительно 0)
    """
    # 1. Получаем длительность файла
    duration = get_audio_duration(input_path)
    # 2. Запускаем ffmpeg для поиска пауз
    command = [
        "ffmpeg", "-i", input_path,
        "-af", f"silencedetect=noise={silence_thresh}dB:d={min_silence_len}",
        "-f", "null", "-"
    ]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    silence_starts = []
    silence_ends = []
    for line in result.stderr.splitlines():
        if "silence_start" in line:
            silence_starts.append(float(line.split("silence_start: ")[-1]))
        if "silence_end" in line:
            silence_ends.append(float(line.split("silence_end: ")[-1].split(" |") [0]))
    # Формируем интервалы для нарезки
    segments = []
    prev_end = 0.0
    for start in silence_starts:
        segments.append((prev_end, start))
        prev_end = start
    # Добавляем последний кусок
    if prev_end < duration:
        segments.append((prev_end, duration))
    # Нарезаем аудио
    chunk_paths = []
    for i, (start, end) in enumerate(segments):
        out_path = os.path.join(output_dir, f"chunk_{i+1}.ogg")
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ss", str(start), "-to", str(end),
            "-c", "copy", out_path
        ])
        chunk_paths.append(out_path)
    return chunk_paths

def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, text=True
    )
    return float(result.stdout.strip())


async def whisper_transcribe(audio_path: str) -> str:
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    
    async with aiohttp.ClientSession() as session:
        with open(audio_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f, filename=os.path.basename(audio_path))
            form.add_field("model", "whisper-1")
            async with session.post(url, data=form, headers=headers) as resp:
                resp.raise_for_status()
                response = await resp.json()
                return response["text"]

async def send_long_message(bot, chat_id, text, **kwargs):
    max_length = 4096
    for i in range(0, len(text), max_length):
        await bot.send_message(chat_id, text[i:i+max_length], **kwargs)
