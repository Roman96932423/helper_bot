from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Ingredient


class IngredientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_by_id(self, ing_id: int) -> Ingredient:
        return await self.session.execute(select(Ingredient).options(selectinload(Ingredient.recipe)).where(Ingredient.id == ing_id))
        
    async def delete(self, ing: Ingredient) -> None:
        await self.session.delete(ing)
        
    async def get_positions(self, recipe_id: int) -> list[int]:
        result = await self.session.execute(select(Ingredient).where(Ingredient.recipe_id == recipe_id).order_by(Ingredient.position))
        
        return result.scalars().all()
    
    async def get_max_position(self, recipe_id: int) -> None:
        result = await self.session.execute(select(func.max(Ingredient.position)).where(Ingredient.recipe_id == recipe_id))
        
        return result.scalar()
        