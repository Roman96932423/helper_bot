import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from db.session import async_session
from handlers import main_router, recipes_router, ingredients_router, pdf_router
from middlewares.session_middleware import DBSessionMiddleware


load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
    
    
async def main() -> None:
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.update.middleware(DBSessionMiddleware(async_session))
    dp.include_router(main_router)
    dp.include_router(recipes_router)
    dp.include_router(ingredients_router)
    dp.include_router(pdf_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
