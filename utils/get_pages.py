from math import ceil


def get_pages(recipes: list) -> dict:
    result = ceil(len(recipes) / 3)
    
    return result
