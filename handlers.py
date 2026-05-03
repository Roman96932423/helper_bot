import os
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from db.crud.users import get_user, create_user
from db.crud.get_recipes import get_user_recipes
from services.pdf_generator import generate_pdf
from state import PDFStates, RecipeStates, EditRecipeName, EditRecipeIngredientName, AddIngredientToRecipe
from keyboards import (
    build_reply_kb,
    build_inline_kb
    )
from db.models import Recipe, Ingredient


router = Router()
    
# Обработка команды старт
@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    user = await get_user(session, int(message.from_user.id))
        
    if not user:
        user = await create_user(session, int(message.from_user.id))
    
    await message.answer('Ты зарегистрирован', reply_markup=build_reply_kb(
        [
            '/pdf', 'рецепты', 'изменить рецепт', 'добавить рецепт', 'удалить рецепт', 'удалить ингридиент'
        ], 'Булдозер', 3
    ))
        

# Логика добавления заготовки в БД
@router.message(F.text == 'добавить рецепт')
async def add_recipe(message: Message, state: FSMContext) -> None:
    await message.answer('Напиши название заготовки')
    await state.set_state(RecipeStates.waiting_for_recipe_name)
    

@router.message(RecipeStates.waiting_for_recipe_name)
async def get_recipe_name(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text, ingredients=[])
    await state.set_state(RecipeStates.waiting_for_recipe_ingredients)
    await message.answer(f'Напиши ингридиенты по одному\nНажми /готово по окончанию')
    

@router.message(RecipeStates.waiting_for_recipe_ingredients, F.text != '/готово')
async def get_recipe_ingredients(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ingredients = data.get('ingredients', [])
    ingredients.append(message.text)
    
    await state.update_data(ingredients=ingredients)
    await message.answer(f'Добавлено: {message.text}', reply_markup=build_reply_kb(['/готово']))
    

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
        await message.answer('Ошибка при сохранении', reply_markup=build_reply_kb(
        [
            '/pdf', 'рецепты', 'изменить рецепт', 'добавить рецепт', 'удалить рецепт', 'удалить ингридиент'
        ], 'Булдозер', 3
    ))
        
        return
    
    await message.answer('Рецепт сохранён ✅', reply_markup=build_reply_kb(
        [
            '/pdf', 'рецепты', 'изменить рецепт', 'добавить рецепт', 'удалить рецепт', 'удалить ингридиент'
        ], 'Булдозер', 3
    ))
    await state.clear()
    

# Удалить рецепт из БД
# Хендлер показать список рецептов
@router.message(F.text == 'удалить рецепт')
async def delete_recipe_start(message: Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    recipes = await get_user_recipes(session, user.id)
    
    await message.answer('🗑️ Выбери рецепт для удаления: ', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'del_recipe:{r.id}'))
    

# Обработка нажатия кнопки для удаления
@router.callback_query(F.data.startswith('del_recipe:'))
async def delete_recipe(callback, session: AsyncSession):
    recipe_id = int(callback.data.split(':')[1])
    recipe = await session.get(Recipe, recipe_id)
    
    await session.delete(recipe)
    await session.commit()
    
    await callback.message.edit_text('✅ Рецепт удалён')
    
    
# Удаление ингридиента
# Показать список рецептов для выбора
@router.message(F.text == 'удалить ингридиент')
async def delete_ingredient_start(message: Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    recipes = await get_user_recipes(session, user.id)
    
    await message.answer('Выбери рецепт', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'choose_recipe:{r.id}'))
    

# Показать список ингридиента для удаления
@router.callback_query(F.data.startswith('choose_recipe:'))
async def delete_ingredient_second(callback, session: AsyncSession):
    recipe_id = int(callback.data.split(':')[1])
    result = await session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id))
    
    recipe = result.scalar_one()
    
    await callback.message.edit_text(f'👨‍🍳Выбери ингридиент для удаления рецепта: {recipe.title}', reply_markup=build_inline_kb(recipe.ingredients, 1, lambda ing: ing.name, lambda ing: f'del_ing:{ing.id}'))
    

# Удаление ингридиента
@router.callback_query(F.data.startswith('del_ing:'))
async def delete_ingredient(callback, session: AsyncSession):
    ingredient_id = int(callback.data.split(':')[1])
    ingredient = await session.get(Ingredient, ingredient_id)
    recipe_id = ingredient.recipe_id
    
    await session.delete(ingredient)
    
    result = await session.execute(select(Ingredient).where(Ingredient.recipe_id == recipe_id).order_by(Ingredient.position))
    
    ingredients_position = result.scalars().all()
    
    for index, ing in enumerate(ingredients_position, start=1):
        ing.position = index
    
    await session.commit()
    
    await callback.message.edit_text('Ингридиент удалён✅')
    

# Логика изменения рецепта (в том числе ингридиента и его добавление)
@router.message(F.text == 'изменить рецепт')
async def edit_recipe(message: Message, session: AsyncSession):
    await message.answer('💠Выбери действие', reply_markup=build_inline_kb(
        [('Изменить название рецепта', 'choose_edit_recipe:'), ('Изменить название ингридиента', 'choose_edit_ing:'), ('Добавить ингридиент', 'choose_add_ing:')],
        1,
        lambda name: name[0],
        lambda cb: cb[1]
    ))
    

# Выбрать рецепт для изменения названия 1.
@router.callback_query(F.data.startswith('choose_edit_recipe:'))
async def edit_name_recipe_first(callback, session: AsyncSession):
    user = await get_user(session, callback.from_user.id)
    recipes = await get_user_recipes(session, user.id)
    
    await callback.answer()
    await callback.message.edit_text('📄Выбери рецепт для изменения', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'edit_recipe:{r.id}'))
    
    
# Изменить название рецепта 2.
@router.callback_query(F.data.startswith('edit_recipe:'))
async def edit_name_recipe_second(callback, state: FSMContext):
    recipe_id = int(callback.data.split(':')[1])
    
    await state.update_data(recipe_id=recipe_id)
    await state.set_state(EditRecipeName.waiting_for_new_recipe_title)
    
    await callback.message.answer('Введи новое название рецепта')
    await callback.answer()
    

# Изменить название рецепта 3.
@router.message(EditRecipeName.waiting_for_new_recipe_title)
async def edit_recipe_name_last(message: Message, session: AsyncSession, state: FSMContext):
    new_recipe_title = message.text
    data = await state.get_data()
    recipe_id = data['recipe_id']
    recipe = await session.get(Recipe, recipe_id)
    recipe.title = new_recipe_title
    
    await session.commit()
    await message.answer('Имя успешно изменено!✅')
    await state.clear()


# Изменить название ингридиента 1.
# Показать список рецептов
@router.callback_query(F.data.startswith('choose_edit_ing:'))
async def edit_recipe_ingredient_name_start(callback, session: AsyncSession):
    user = await get_user(session, callback.from_user.id)
    recipes = await get_user_recipes(session, user.id)
    
    await callback.message.edit_text('⬇️Выбери рецепт', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'edit_recipe_ing_name:{r.id}'))
    await callback.answer()
    

# Изменить название ингридиента 2.
# Показать ингридиенты выбранного рецепта
@router.callback_query(F.data.startswith('edit_recipe_ing_name:'))
async def edit_recipe_ingredient_name_second(callback, session: AsyncSession):
    recipe_id = int(callback.data.split(':')[1])
    result = await session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id))
    
    recipe = result.scalar_one()
    
    
    await callback.message.edit_text('Выбери ингридиент для изменения', reply_markup=build_inline_kb(recipe.ingredients, 1, lambda ing: ing.name, lambda ing: f'edit_recipe_ing_name_end:{ing.id}'))
    await callback.answer()
    
    
# Изменить название ингридиента 3.
@router.callback_query(F.data.startswith('edit_recipe_ing_name_end:'))
async def edit_recipe_ingredient_name_four(callback, state: FSMContext):
    ing_id = int(callback.data.split(':')[1])
    
    await state.update_data(ing_id=ing_id)
    await state.set_state(EditRecipeIngredientName.waiting_for_new_ingredient_name)
    await callback.message.edit_text('Введи новое название ингридиента')
    await callback.answer()
    

# Изменить название ингридиента 4.
@router.message(EditRecipeIngredientName.waiting_for_new_ingredient_name)
async def edit_recipe_ingredient_name_last(message: Message, session: AsyncSession, state:FSMContext):
    new_ing_name = message.text
    data = await state.get_data()
    ing_id = data['ing_id']
    ingredient = await session.get(Ingredient, ing_id)
    ingredient.name = new_ing_name
    
    await session.commit()
    await message.answer('Ингридиент успешно изменён✅')
    await state.clear()
    
    
# Добавить ингридиент в рецепт 1.
@router.callback_query(F.data.startswith('choose_add_ing:'))
async def add_ing_to_recipe_start(callback, session: AsyncSession):
    user = await get_user(session, callback.from_user.id)
    recipes = await get_user_recipes(session, user.id)
    
    await callback.message.edit_text('Выбери рецепт⬇️', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'choose_recipe_for_add_ing:{r.id}'))
    
    
# Добавить ингридиент в рецепт 2.
@router.callback_query(F.data.startswith('choose_recipe_for_add_ing:'))
async def add_ing_to_recipe_second(callback, session: AsyncSession, state: FSMContext):
    recipe_id = int(callback.data.split(':')[1])
    result = await session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id))
    ingredients_str = ''
    
    recipe = result.scalar_one()
    
    for ing in recipe.ingredients:
        ingredients_str += f'• {ing.name}'
        ingredients_str += '\n'
    
    await state.update_data(recipe_id=recipe_id)
    await state.set_state(AddIngredientToRecipe.waiting_for_ing_to_recipe)
    await callback.message.edit_text(f'Текущие ингридиенты:\n{ingredients_str}\nВведи ингридиент')
    

# Добавить ингридиент в рецепт 3.
@router.message(AddIngredientToRecipe.waiting_for_ing_to_recipe)
async def add_ing_to_recipe_last(message: Message,  session: AsyncSession, state: FSMContext):
    ing_name = message.text
    data = await state.get_data()
    recipe_id = data['recipe_id']
    result_recipe = await session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id))
    result_ing = await session.execute(select(func.max(Ingredient.position)).where(Ingredient.recipe_id == recipe_id))
    
    recipe = result_recipe.scalar_one()
    max_ing_position = result_ing.scalar()
    
    recipe.ingredients.append(Ingredient(name=ing_name, position=max_ing_position + 1))
    
    await session.commit()
    await message.answer('Ингридиент успешно добавлен✅')
    await state.clear()
    

# Показать рецепты пользователя в БД
@router.message(F.text == 'рецепты')
async def show_recipes(message: Message) -> None:
    async with async_session() as session:
        user = await get_user(session, message.from_user.id)
        recipes = await get_user_recipes(session, user.id)
        
        text = ''
        
        for recipe in recipes:
            text += f'🍣 {recipe.title.capitalize()}\n'
            
            for ing in recipe.ingredients:
                text += f' • {ing.name}\n'
            
            text += '\n'
                
        await message.answer(f'📄 Твои рецепты:\n\n{text}')
        

# Логика генерации файла из данных
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
