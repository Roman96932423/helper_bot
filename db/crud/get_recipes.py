from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models import Recipe


async def get_user_recipes(session, user_id: int) -> list[Recipe]:
    result = await session.execute(select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.user_id == user_id))
    
    return result.scalars().all()
