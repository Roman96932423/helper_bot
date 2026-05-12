import os
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from utils import format
from db.session import async_session
from db.repositories import RecipeRepository, UserRepository, IngredientRepository
from db.services import RecipeService, IngredientService
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
    user_repo = UserRepository(session)
    user = await user_repo.get(user_id=message.from_user.id)
        
    if not user:
        user = await user_repo.create(tg_id=message.from_user.id)
    
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
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    data = await state.get_data()
    
    title = data.get('title')
    ingredients = data.get('ingredients', [])
    
    if not title or not ingredients:
        await message.answer('Данные потеряны')
        
        return
    
    try:
        await recipe_service.add_recipe(message.from_user.id, title, ingredients)
        
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
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    recipes = await recipe_service.get_recipes_by_user(message.from_user.id)
    
    await message.answer('🗑️ Выбери рецепт для удаления: ', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'del_recipe:{r.id}'))
    

# Обработка нажатия кнопки для удаления
@router.callback_query(F.data.startswith('del_recipe:'))
async def delete_recipe(callback, session: AsyncSession):
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo)
    
    recipe_id = int(callback.data.split(':')[1])
    
    await recipe_service.delete_recipe(recipe_id)
    
    await session.commit()
    
    await callback.message.edit_text('✅ Рецепт удалён')
    
    
# Удаление ингридиента
# Показать список рецептов для выбора
@router.message(F.text == 'удалить ингридиент')
async def delete_ingredient_start(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    recipes = await recipe_service.get_recipes_by_user(message.from_user.id)
    
    await message.answer('Выбери рецепт', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'choose_recipe:{r.id}'))
    

# Показать список ингридиентов для удаления
@router.callback_query(F.data.startswith('choose_recipe:'))
async def delete_ingredient_second(callback, session: AsyncSession):
    recipe_repo = RecipeRepository(session)
    
    recipe_id = int(callback.data.split(':')[1])
    recipe = await recipe_repo.get_recipe_by_id(recipe_id)
    
    await callback.message.edit_text(f'👨‍🍳Выбери ингридиент для удаления рецепта: {recipe.title}', reply_markup=build_inline_kb(recipe.ingredients, 1, lambda ing: ing.name, lambda ing: f'del_ing:{ing.id}'))
    

# Удаление ингридиента
@router.callback_query(F.data.startswith('del_ing:'))
async def delete_ingredient(callback, session: AsyncSession):
    ing_repo = IngredientRepository(session)
    ing_service = IngredientService(ing_repo)
    
    ingredient_id = int(callback.data.split(':')[1])
    
    await ing_service.delete(ingredient_id)
    
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
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    recipes = await recipe_service.get_recipes_by_user(callback.from_user.id)
    
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
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo)
    
    new_recipe_title = message.text
    data = await state.get_data()
    recipe_id = data['recipe_id']
    
    await recipe_service.update_name(recipe_id, new_recipe_title)
    
    await session.commit()
    await message.answer('Название успешно изменено!✅')
    await state.clear()


# Изменить название ингридиента 1.
# Показать список рецептов
@router.callback_query(F.data.startswith('choose_edit_ing:'))
async def edit_recipe_ingredient_name_start(callback, session: AsyncSession):
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    recipes = await recipe_service.get_recipes_by_user(callback.from_user.id)
    
    await callback.message.edit_text('⬇️Выбери рецепт', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'edit_recipe_ing_name:{r.id}'))
    await callback.answer()
    

# Изменить название ингридиента 2.
# Показать ингридиенты выбранного рецепта
@router.callback_query(F.data.startswith('edit_recipe_ing_name:'))
async def edit_recipe_ingredient_name_second(callback, session: AsyncSession):
    recipe_repo = RecipeRepository(session)
    
    recipe_id = int(callback.data.split(':')[1])
    recipe = await recipe_repo.get_recipe_by_id(recipe_id)
    
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
    ing_repo = IngredientRepository(session)
    ing_service = IngredientService(ing_repo)
    
    new_ing_name = message.text
    data = await state.get_data()
    ing_id = data['ing_id']
    
    await ing_service.update_name(ing_id, new_ing_name)
    
    await session.commit()
    await message.answer('Ингридиент успешно изменён✅')
    await state.clear()
    
    
# Добавить ингридиент в рецепт 1.
@router.callback_query(F.data.startswith('choose_add_ing:'))
async def add_ing_to_recipe_start(callback, session: AsyncSession):
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    recipes = await recipe_service.get_recipes_by_user(callback.from_user.id)
    
    await callback.message.edit_text('Выбери рецепт⬇️', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'choose_recipe_for_add_ing:{r.id}'))
    
    
# Добавить ингридиент в рецепт 2.
@router.callback_query(F.data.startswith('choose_recipe_for_add_ing:'))
async def add_ing_to_recipe_second(callback, session: AsyncSession, state: FSMContext):
    recipe_repo = RecipeRepository(session)
    
    recipe_id = int(callback.data.split(':')[1])
    ingredients_str = ''
    
    recipe = await recipe_repo.get_recipe_by_id(recipe_id)
    
    for ing in recipe.ingredients:
        ingredients_str += f'• {ing.name}'
        ingredients_str += '\n'
    
    await state.update_data(recipe_id=recipe_id)
    await state.set_state(AddIngredientToRecipe.waiting_for_ing_to_recipe)
    await callback.message.edit_text(f'Текущие ингридиенты:\n{ingredients_str}\nВведи ингридиент')
    

# Добавить ингридиент в рецепт 3.
@router.message(AddIngredientToRecipe.waiting_for_ing_to_recipe)
async def add_ing_to_recipe_last(message: Message,  session: AsyncSession, state: FSMContext):
    ing_repo = IngredientRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo=recipe_repo, ing_repo=ing_repo)
    
    ing_name = message.text
    data = await state.get_data()
    recipe_id = data['recipe_id']
    
    await recipe_service.add_ingredient(recipe_id, ing_name)
    
    await session.commit()
    await message.answer('Ингридиент успешно добавлен✅')
    await state.clear()
    

# Показать рецепты пользователя в БД
@router.message(F.text == 'рецепты')
async def show_recipes(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
    recipes = await recipe_service.get_recipes_by_user(message.from_user.id)
        
    format_text = format(recipes)
                
    await message.answer(f'📄 Твои рецепты:\n\n{format_text}')
        

# Логика генерации файла из данных
@router.message(Command('pdf'))
async def start_pdf_process(message: Message, state: FSMContext) -> None:
    await message.answer('Напиши название файла, например tech_karty.pdf')
    await state.set_state(PDFStates.waiting_for_filename)
    
    
@router.message(PDFStates.waiting_for_filename)
async def get_filename(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    recipe_repo = RecipeRepository(session)
    recipe_service = RecipeService(recipe_repo, user_repo)
    
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
    