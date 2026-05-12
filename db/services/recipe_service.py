from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.repositories import RecipeRepository, UserRepository, IngredientRepository
from db.models import Recipe, Ingredient
from logger import logger


class RecipeService:
    def __init__(self, recipe_repo: RecipeRepository, user_repo: UserRepository=None, ing_repo: IngredientRepository=None):
        self.recipe_repo = recipe_repo
        self.user_repo = user_repo
        self.ing_repo = ing_repo
        
    async def add_recipe(self, user_id, title: str, ingredients: list) -> None:
        logger.info(f'Started adding recipe "{title}"')
        user = await self.user_repo.get(user_id)
        
        if not user:
            logger.warning(f'User {user_id} not found')
            
            return
        
        recipe = Recipe(
            title=title,
            user_id=user.id
        )
        recipe.ingredients = [
            Ingredient(name=ing, position=i)
            for i, ing in enumerate(ingredients)
        ]
        
        if not recipe or len(recipe.ingredients) == 0:
            logger.info(f'Recipe "{title}" or ingredients not found')
            
            return
        
        await self.recipe_repo.add(recipe)
        
        logger.info(f'Recipe "{title}" by user {user.id} added successfully')
        
    async def add_ingredient(self, recipe_id: int, ing_name: str) -> None:
        logger.info(f'Started adding ingredient to recipe {recipe_id}')
        recipe = await self.recipe_repo.get_recipe_by_id(recipe_id)
        max_position = await self.ing_repo.get_max_position(recipe_id)
        
        if not recipe:
            logger.warning(f'Recipe {recipe_id} not found')
            
            return
        
        recipe.ingredients.append(Ingredient(name=ing_name, position=max_position + 1))
        logger.info(f'Ingredient {ing_name} added successfully')
        
    async def delete_recipe(self, recipe_id: int) -> None:
        logger.info(f'Starting delete recipe {recipe_id}')
        recipe = await self.recipe_repo.get_recipe_by_id(recipe_id)
        
        if not recipe:
            logger.warning(f'Recipe {recipe_id} not found')
            
            return
        
        await self.recipe_repo.delete(recipe)
        
        logger.info(f'Recipe {recipe_id} deleting successfully')
        
    async def get_recipes_by_user(self, user_id: int) -> list[Recipe]:
        logger.info(f'Fetching recipes to user {user_id}')
        user = await self.user_repo.get(user_id)
        recipes = await self.recipe_repo.get_by_user(user.id)
        
        if not user or len(recipes) == 0:
            logger.warning(f'User {user_id} or recipes not found')
            
            return
        
        logger.info(f'Recipes for user {user_id} fetching successfully')
        
        return recipes
    
    async def update_name(self, recipe_id: int, new_title: str) -> None:
        logger.info(f'Started updating recipe {recipe_id}')
        recipe = await self.recipe_repo.get_recipe_by_id(recipe_id)
        
        if not recipe:
            logger.warning(f'Recipe {recipe_id} not found')
            
            return
        
        recipe.title = new_title
        logger.info(f'Recipe {recipe_id} updating successfully')
        