from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.repositories import RecipeRepository, UserRepository, IngredientRepository
from db.models import Recipe, Ingredient


class RecipeService:
    def __init__(self, recipe_repo: RecipeRepository, user_repo: UserRepository=None, ing_repo: IngredientRepository=None):
        self.recipe_repo = recipe_repo
        self.user_repo = user_repo
        self.ing_repo = ing_repo
        
    async def add_recipe(self, user_id, title: str, ingredients: list) -> None:
        user = await self.user_repo.get(user_id)
        recipe = Recipe(
            title=title,
            user_id=user.id
        )
        recipe.ingredients = [
            Ingredient(name=ing, position=i)
            for i, ing in enumerate(ingredients)
        ]
        
        await self.recipe_repo.add(recipe)
        
    async def add_ingredient(self, recipe_id: int, ing_name: str) -> None:
        recipe = await self.recipe_repo.get_recipe_by_id(recipe_id)
        max_position = await self.ing_repo.get_max_position(recipe_id)
        
        recipe.ingredients.append(Ingredient(name=ing_name, position=max_position + 1))
        
    async def delete_recipe(self, recipe_id: int) -> None:
        recipe = await self.recipe_repo.get_recipe_by_id(recipe_id)
        
        await self.recipe_repo.delete(recipe)
        
    async def get_recipes_by_user(self, user_id: int) -> list[Recipe]:
        user = await self.user_repo.get(user_id)
        recipes = await self.recipe_repo.get_by_user(user.id)
        
        return recipes
    
    async def update_name(self, recipe_id, new_title) -> None:
        recipe = await self.recipe_repo.get_recipe_by_id(recipe_id)
        recipe.title = new_title
        