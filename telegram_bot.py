# telegram_bot.py
import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from chat import AIbot
from config import TG_BOT_TOKEN
import logging

logging.basicConfig(level=logging.ERROR)

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()

ai_bot = None  # Явное объявление


async def initialize_bot():
    global ai_bot
    ai_bot = AIbot()
    await ai_bot.initialize()
    ai_bot.stats_db.start_cleaning()


@dp.message(CommandStart())
async def send_welcome(message: Message):
    """Отправляет приветственное сообщение при запуске бота."""
    await message.reply("Привет!\n"
                        "Задавай вопросы, а я отвечу на русском, используя методичку!\n"
                        "Команды:\n"
                        "/stats — показать статистику\n"
                        "/clean — удалить данные старше 30 дней")

@dp.message(Command("stats"))
async def send_stats(message: Message):
    stats = await ai_bot.get_stats()  # Добавлен await
    await message.reply(stats)

@dp.message(Command("clean"))
async def clean_stats(message: Message):
    await ai_bot.stats_db.clean_old_entries()  # Добавлен await
    await message.reply("Старые данные (старше 30 дней) удалены.")


@dp.message(lambda message: message.text is not None)
async def handle_message(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        question = message.text
        answer = await ai_bot.answer(question)
        await message.reply(answer)
    except Exception as e:
        logging.error(f"Ошибка в обработке сообщения: {e}")
        await message.reply(f"Ошибка: {e}")

async def main():
    """Основная функция запуска бота."""
    await initialize_bot()  # Инициализируем бота перед запуском polling
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен вручную.")
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        sys.exit(1)