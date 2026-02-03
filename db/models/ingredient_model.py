from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Ingredient(Base):
    __tablename__ = 'ingredients'
    __table_args__ = (
		UniqueConstraint('recipe_id', 'position', name='uq_recipe_ingredient_position')
	)
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey('recipes.id', ondelete='CASCADE'),
        index=True, nullable=False
	)
    recipe: Mapped['Recipe'] = relationship(back_populates='ingredients')
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<Ingredient id:{self.id} name:{self.name} position:{self.position}>'
     