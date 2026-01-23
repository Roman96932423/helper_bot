import os
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from pdf import generate_pdf
from state import PDFStates


user = Router()
    

@user.message(Command('pdf'))
async def start_pdf_process(message: Message, state: FSMContext) -> None:
    await message.answer('Напиши название файла, например tech_karty.pdf')
    await state.set_state(PDFStates.waiting_for_filename)
    
    
@user.message(PDFStates.waiting_for_filename)
async def get_filename(message: Message, state: FSMContext) -> None:
    # if not message.text.endswith('.pdf'):
    #     await message.answer('Неверный формат ввода.')
        
    #     return
    
    filename = message.text.strip()
    
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    await state.update_data(filename=filename)
    await message.answer('Теперь отправь список заготовок')
    await state.set_state(PDFStates.waiting_for_recipes)
    
    
@user.message(PDFStates.waiting_for_recipes)
async def get_recipes(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    filename = user_data['filename']
    
    items = [line.strip() for line in message.text.splitlines() if line.strip()]
    
    if len(items) % 2 != 0:
        await message.answer('Неверный формат. Каждая заготовка должна иметь 2 строки')
        
        return
    
    recipe_list = [(items[i], items[i + 1]) for i in range(0, len(items), 2)]
    
    try:
        path = generate_pdf(recipe_list, filename)
    except Exception as error:
        await message.answer('Ошибка при создании PDF.')
        print(error)
        await state.clear()
        return

    file = FSInputFile(path)
    
    await message.answer_document(file)
    await state.clear()
    
    os.remove(path)
