from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Recipe


class RecipeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    # Получить рецепты пользователя
    async def get_by_user(self, user_id) -> list[Recipe]:
        result = await self.session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.user_id == user_id))
        
        return result.scalars().all()
    
    # Получить рецепт по id
    async def get_recipe_by_id(self, recipe_id: int) -> Recipe:
        result = await self.session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id))
        
        return result.scalar_one_or_none()
    
    # Удаление рецепта
    async def delete(self, recipe: Recipe) -> None:
        await self.session.delete(recipe)
        
    # Добавление рецепта
    async def add(self, recipe: Recipe) -> None:
        self.session.add(recipe)
    
    
        