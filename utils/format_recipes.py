from db.models import Recipe


def format(recipes: list[Recipe]) -> str:
    text = ''
    
    for recipe in recipes:
        text += f'🍣 {recipe.title.capitalize()}\n'
        
        for ing in recipe.ingredients:
            text += f'      • {ing.name.lower()}\n'
            
        text += '\n'
        
    return text
    