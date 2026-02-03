from database import engine, Base
from models import User, Recipe, Ingredient


Base.metadata.create_all(engine)

print("таблицы созданы")
