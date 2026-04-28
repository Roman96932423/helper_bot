import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from db.session import async_session
from handlers import router
from middlewares.session_middleware import DBSessionMiddleware


load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
    
    
async def main() -> None:
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.message.middleware(DBSessionMiddleware(async_session))
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
