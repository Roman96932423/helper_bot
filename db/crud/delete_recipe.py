from sqlalchemy import select

from db.models import Recipe


async def delete_recipe(session, user_id: int) -> None:
    ...
