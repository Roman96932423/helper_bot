from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get(self, tg_id: int) -> User:
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        
        return result.scalar_one_or_none()
    
    async def create(self, tg_id: int) -> User:
        user = User(tg_id=tg_id)
        self.session.add(user)
        
        await self.session.commit()
        
        return user
