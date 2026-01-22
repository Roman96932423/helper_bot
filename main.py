import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

from pdf import generate_pdf


load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(TOKEN)
dp = Dispatcher()

recipe_dict = {
    'Краб микс': "1кг краб 180гр японский майонез",
    'Мицукан': "10л мицукан 10кг сахар 400гр соль",
    'Васаби': "1кг васаби 1550мл воды",
    'Темпура': "1кг темпуры 1300л воды"
    }


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    path = generate_pdf(recipe_dict, 'test.pdf')
    file = FSInputFile(path)
    
    await message.answer_document(file)
    
    os.remove(path)
    
    
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
