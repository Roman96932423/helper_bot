from aiogram.fsm.state import StatesGroup, State


class PDFStates(StatesGroup):
    waiting_for_filename = State()
    waiting_for_recipes = State()
    

class RecipeStates(StatesGroup):
    waiting_for_recipe_name = State()
    waiting_for_recipe_ingredients = State()
    

class EditRecipeName(StatesGroup):
    waiting_for_new_recipe_title = State()
    

class EditRecipeIngredientName(StatesGroup):
    waiting_for_new_ingredient_name = State()
    

class AddIngredientToRecipe(StatesGroup):
    waiting_for_ing_to_recipe = State()
    