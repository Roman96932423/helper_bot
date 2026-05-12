from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories import UserRepository
from keyboards import build_reply_kb
from logger import logger


router = Router()
    
# Обработка команды старт
@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get(tg_id=message.from_user.id)
        
    if not user:
        user = await user_repo.create(tg_id=message.from_user.id)
        logger.info(f'Creating user {user.id}')
    
    await message.answer('Ты зарегистрирован', reply_markup=build_reply_kb(
        [
            '/pdf', 'рецепты', 'изменить рецепт', 'добавить рецепт', 'удалить рецепт', 'удалить ингридиент'
        ], 'Булдозер', 3
    ))
