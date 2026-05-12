from sqlalchemy import select

from db.repositories import IngredientRepository
from logger import logger


class IngredientService:
    def __init__(self, ing_repo: IngredientRepository):
        self.ing_repo = ing_repo
        
    async def delete(self, ing_id: int) -> None:
        logger.info(f'Started deleting ingredient: {ing_id}')
        ingredient = await self.ing_repo.get_by_id(ing_id)
        
        if not ingredient:
            logger.warning(f'Ingredient {ing_id} not found')  
            
            return
              
        recipe_id = ingredient.recipe_id
        
        await self.ing_repo.delete(ingredient)
        
        ing_positions = await self.ing_repo.get_positions(recipe_id)
        
        for index, ing in enumerate(ing_positions, start=1):
            ing.position = index
            
        logger.info(f'Deleted ingredient {ingredient.name} | {ingredient.id} from recipe: {recipe_id} by user {ingredient.recipe.user_id}')
        
    async def update_name(self, ing_id: int, new_name: str) -> None:
        logger.info(f'Started updating ingredient {ing_id}')
        ingredient = await self.ing_repo.get_by_id(ing_id)
        
        if not ingredient:
            logger.warning(f'Ingredient {ing_id} not found')
            
            return
        
        ingredient.name = new_name
        logger.info(f'Updating {ing_id} successfully')
        