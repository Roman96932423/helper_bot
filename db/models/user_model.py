from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    recipes: Mapped[list['Recipe']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan'
        )
