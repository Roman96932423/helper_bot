from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Recipe(Base):
    __tablename__ = 'recipes'
    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='uq_user_recipe_title'),
        )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(35), nullable=False)
    ingredients: Mapped[list['Ingredient']] = relationship(
		back_populates='recipe',
		cascade='all, delete-orphan',
		order_by='Ingredient.position'
	)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    user: Mapped['User'] = relationship(back_populates='recipes')
    
    def __str__(self):
        return self.title
    
    def __repr__(self):
        return f'<Recipe id:{self.id} title:{self.title}>'
