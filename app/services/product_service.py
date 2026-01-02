from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        result = await self.db.execute(
            select(Product)
            .where(Product.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self, product_id: int, data: ProductUpdate
    ) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False

        await self.db.delete(product)
        await self.db.commit()
        return True

    async def count(self) -> int:
        result = await self.db.execute(
            select(Product).where(Product.is_active == True)
        )
        return len(list(result.scalars().all()))
