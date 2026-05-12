import os
from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from state import PDFStates
from services import generate_pdf, create_recipe_service


router = Router()


# Логика генерации файла из данных
@router.message(Command('pdf'))
async def start_pdf_process(message: Message, state: FSMContext) -> None:
    await message.answer('Напиши название файла, например tech_karty.pdf')
    await state.set_state(PDFStates.waiting_for_filename)
    
    
@router.message(PDFStates.waiting_for_filename)
async def get_filename(message: Message, state: FSMContext, session: AsyncSession) -> None:
    recipe_service = create_recipe_service(session)
    
    filename = message.text.strip()
        
    if not filename.endswith('.pdf'):
        filename += '.pdf'
            
    recipes = await recipe_service.get_recipes_by_user(message.from_user.id)
            
    try:
        path = generate_pdf(recipes, filename)
    except Exception as error:
        await message.answer('Ошибка при создании PDF.')
        print(error)
        await state.clear()
            
        return

    file = FSInputFile(path)
        
    await message.answer_document(file)
    await state.clear()
        
    os.remove(path)
    