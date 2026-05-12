from sqlalchemy import select

from db.repositories import IngredientRepository


class IngredientService:
    def __init__(self, ing_repo: IngredientRepository):
        self.ing_repo = ing_repo
        
    async def delete(self, ing_id: int) -> None:
        ingredient = await self.ing_repo.get_by_id(ing_id)
        recipe_id = ingredient.recipe_id
        
        await self.ing_repo.delete(ingredient)
        
        ing_positions = await self.ing_repo.get_positions(recipe_id)
        
        for index, ing in enumerate(ing_positions, start=1):
            ing.position = index
        
    async def update_name(self, ing_id: int, new_name: str) -> None:
        ingredient = await self.ing_repo.get_by_id(ing_id)
        ingredient.name = new_name
        