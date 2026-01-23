import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from handlers import user


load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
    
    
async def main() -> None:
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.include_router(user)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
