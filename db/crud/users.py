from sqlalchemy import select

from db.models import User


async def get_user(session, tg_id: int):
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    
    return result.scalar_one_or_none()


async def create_user(session, tg_id: int):
    user = User(tg_id=tg_id)
    session.add(user)
    await session.commit()
    
    return user
