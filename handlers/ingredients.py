from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories import RecipeRepository
from services import create_recipe_service, create_ingredient_service
from keyboards import build_inline_kb
from state import EditRecipeIngredientName, AddIngredientToRecipe


router = Router()


# Удаление ингридиента
# Показать список рецептов для выбора
@router.message(F.text == 'удалить ингридиент')
async def delete_ingredient_start(message: Message, session: AsyncSession):
    recipe_service = create_recipe_service(session)
    
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
    ing_service = create_ingredient_service(session)
    
    ingredient_id = int(callback.data.split(':')[1])
    
    await ing_service.delete(ingredient_id)
    
    await session.commit()
    
    await callback.message.edit_text('Ингредиент удалён✅')
    
    
# Изменить название ингридиента 1.
# Показать список рецептов
@router.callback_query(F.data.startswith('choose_edit_ing:'))
async def edit_recipe_ingredient_name_start(callback, session: AsyncSession):
    recipe_service = create_recipe_service(session)
    
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
    ing_service = create_ingredient_service(session)
    
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
    recipe_service = create_recipe_service(session)
    
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
    recipe_service = create_recipe_service(session)
    
    ing_name = message.text
    data = await state.get_data()
    recipe_id = data['recipe_id']
    
    await recipe_service.add_ingredient(recipe_id, ing_name)
    
    await session.commit()
    await message.answer('Ингридиент успешно добавлен✅')
    await state.clear()
    
    