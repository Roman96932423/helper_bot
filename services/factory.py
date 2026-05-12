from db.repositories import RecipeRepository, UserRepository, IngredientRepository
from db.services import RecipeService, IngredientService
from sqlalchemy.ext.asyncio import AsyncSession


def create_recipe_service(session: AsyncSession) -> RecipeService:
    recipe_repo = RecipeRepository(session)
    user_repo = UserRepository(session)
    ing_repo = IngredientRepository(session)
    
    return RecipeService(recipe_repo, user_repo, ing_repo)


def create_ingredient_service(session: AsyncSession) -> IngredientService:
    ing_repo = IngredientRepository(session)
    
    return IngredientService(ing_repo)
    