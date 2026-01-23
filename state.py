from aiogram.fsm.state import StatesGroup, State


class PDFStates(StatesGroup):
    waiting_for_filename = State()
    waiting_for_recipes = State()
    