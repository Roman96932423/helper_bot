from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from state import RecipeStates, EditRecipeName
from keyboards import build_reply_kb, build_inline_kb
from services import create_recipe_service
from utils import format


router = Router()


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
    recipe_service = create_recipe_service(session)
    
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
    recipe_service = create_recipe_service(session)
    
    recipes = await recipe_service.get_recipes_by_user(message.from_user.id)
    
    await message.answer('🗑️ Выбери рецепт для удаления: ', reply_markup=build_inline_kb(recipes, 2, lambda r: r.title, lambda r: f'del_recipe:{r.id}'))
    

# Обработка нажатия кнопки для удаления
@router.callback_query(F.data.startswith('del_recipe:'))
async def delete_recipe(callback, session: AsyncSession):
    recipe_service = create_recipe_service(session)
    
    recipe_id = int(callback.data.split(':')[1])
    
    await recipe_service.delete_recipe(recipe_id)
    
    await session.commit()
    
    await callback.message.edit_text('✅ Рецепт удалён')
    
    
# Логика изменения рецепта (в том числе ингридиента и его добавление)
@router.message(F.text == 'изменить рецепт')
async def edit_recipe(message: Message):
    await message.answer('💠Выбери действие', reply_markup=build_inline_kb(
        [('Изменить название рецепта', 'choose_edit_recipe:'), ('Изменить название ингредиента', 'choose_edit_ing:'), ('Добавить ингредиент', 'choose_add_ing:')],
        1,
        lambda name: name[0],
        lambda cb: cb[1]
    ))
    
    
# Выбрать рецепт для изменения названия 1.
@router.callback_query(F.data.startswith('choose_edit_recipe:'))
async def edit_name_recipe_first(callback, session: AsyncSession):
    recipe_service = create_recipe_service(session)
    
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
    recipe_service = create_recipe_service(session)
    
    new_recipe_title = message.text
    data = await state.get_data()
    recipe_id = data['recipe_id']
    
    await recipe_service.update_name(recipe_id, new_recipe_title)
    
    await session.commit()
    await message.answer('Название успешно изменено!✅')
    await state.clear()
    
    
# Показать рецепты пользователя в БД
@router.message(F.text == 'рецепты')
async def show_recipes(message: Message, session: AsyncSession) -> None:
    recipe_service = create_recipe_service(session)
    
    recipes = await recipe_service.get_recipes_by_user(message.from_user.id)
    
    if len(recipes) == 0:
        await message.answer('😊 У тебя ещё нет рецептов')
        
        return
        
    format_text = format(recipes)
                
    await message.answer(f'📄 Твои рецепты:\n\n{format_text}')
    