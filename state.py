from aiogram.fsm.state import StatesGroup, State


class PDFStates(StatesGroup):
    waiting_for_filename = State()
    waiting_for_recipes = State()
    

class RecipeStates(StatesGroup):
    waiting_for_recipe_name = State()
    waiting_for_recipe_ingredients = State()
    