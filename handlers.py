import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from db.crud.users import get_user, create_user
from db.crud.get_recipes import get_user_recipes
from services.pdf_generator import generate_pdf
from state import PDFStates, RecipeStates
from keyboards import menu
from db.models import Recipe, Ingredient


router = Router()
    
@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await get_user(session, int(message.from_user.id))
        
        if not user:
            user = await create_user(session, int(message.from_user.id))
    
        await message.answer('Ты зарегистрирован', reply_markup=menu)
        

@router.message(F.text == 'добавить')
async def add_recipe(message: Message, state: FSMContext) -> None:
    await message.answer('Напиши название заготовки')
    await state.set_state(RecipeStates.waiting_for_recipe_name)
    

@router.message(RecipeStates.waiting_for_recipe_name)
async def get_recipe_name(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text, ingredients=[])
    await state.set_state(RecipeStates.waiting_for_recipe_ingredients)
    await message.answer(f'Напиши ингридиенты по одному\nНапиши /готово по окончанию')
    

@router.message(RecipeStates.waiting_for_recipe_ingredients, F.text != '/готово')
async def get_recipe_ingredients(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ingredients = data.get('ingredients', [])
    ingredients.append(message.text)
    
    await state.update_data(ingredients=ingredients)
    await message.answer(f'Добавлено: {message.text}')
    

@router.message(RecipeStates.waiting_for_recipe_ingredients, F.text == '/готово')
async def create_recipe(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    
    title = data.get('title')
    ingredients = data.get('ingredients', [])
    
    if not title or not ingredients:
        await message.answer('Данные потеряны')
        
        return
    
    user = await get_user(session, message.from_user.id)
    recipe = Recipe(
        title=title,
        user_id=user.id
    )
    
    recipe.ingredients = [
        Ingredient(name=ing, position=i)
        for i, ing in enumerate(ingredients, start=1)
    ]
    
    try:
        session.add(recipe)
        await session.commit()
    except Exception:
        await session.rollback()
        await message.answer('Ошибка при сохранении')
        
        return
    
    await message.answer('Рецепт сохранён')
    await state.clear()
    
    
@router.message(F.text == 'рецепты')
async def show_recipes(message: Message) -> None:
    async with async_session() as session:
        user = await get_user(session, message.from_user.id)
        recipes = await get_user_recipes(session, user.id)
        
        text = ''
        
        for recipe in recipes:
            text += f'{recipe.title.capitalize()}\n'
            
            for ing in recipe.ingredients:
                text += f' - {ing.name}\n'
            
            text += '\n'
                
        await message.answer(f'Твои рецепты:\n\n{text}')
    

@router.message(Command('pdf'))
async def start_pdf_process(message: Message, state: FSMContext) -> None:
    await message.answer('Напиши название файла, например tech_karty.pdf')
    await state.set_state(PDFStates.waiting_for_filename)
    
    
@router.message(PDFStates.waiting_for_filename)
async def get_filename(message: Message, state: FSMContext) -> None:
    async with async_session() as session:
        filename = message.text.strip()
        
        if not filename.endswith('.pdf'):
            filename += '.pdf'
            
        user = await get_user(session, message.from_user.id)
            
        recipes_list = await get_user_recipes(session, user.id)
            
        try:
            path = generate_pdf(recipes_list, filename)
        except Exception as error:
            await message.answer('Ошибка при создании PDF.')
            print(error)
            await state.clear()
            
            return

        file = FSInputFile(path)
        
        await message.answer_document(file)
        await state.clear()
        
        os.remove(path)
