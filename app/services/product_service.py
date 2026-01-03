from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List, Dict, Any

from app.models.product import Product, Category
from app.schemas.product import ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CategoryCreate) -> Category:
        category = Category(**data.model_dump())
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> List[Category]:
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)
        query = query.order_by(Category.sort_order, Category.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_product_count(self) -> List[Dict[str, Any]]:
        """Get categories with product counts"""
        result = await self.db.execute(
            select(
                Category,
                func.count(Product.id).label("product_count")
            )
            .outerjoin(Product, and_(Product.category_id == Category.id, Product.is_active == True))
            .where(Category.is_active == True)
            .group_by(Category.id)
            .order_by(Category.sort_order, Category.name)
        )
        rows = result.all()
        return [
            {
                "id": row[0].id,
                "name": row[0].name,
                "description": row[0].description,
                "image_url": row[0].image_url,
                "product_count": row[1]
            }
            for row in rows
        ]

    async def update(self, category_id: int, data: CategoryUpdate) -> Optional[Category]:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self.db.delete(category)
        await self.db.commit()
        return True


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

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.sku == sku)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        active_only: bool = True,
        include_inactive: bool = False
    ) -> List[Product]:
        query = select(Product)

        if active_only and not include_inactive:
            query = query.where(Product.is_active == True)

        if category_id:
            query = query.where(Product.category_id == category_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.brand.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.tags.ilike(search_term)
                )
            )

        query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_featured(self, limit: int = 10) -> List[Product]:
        result = await self.db.execute(
            select(Product)
            .where(and_(Product.is_active == True, Product.is_featured == True))
            .order_by(Product.sold_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(self, category_id: int, skip: int = 0, limit: int = 50) -> List[Product]:
        result = await self.db.execute(
            select(Product)
            .where(and_(Product.category_id == category_id, Product.is_active == True))
            .order_by(Product.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 20) -> List[Product]:
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.is_active == True,
                    or_(
                        Product.name.ilike(search_term),
                        Product.brand.ilike(search_term),
                        Product.description.ilike(search_term),
                        Product.tags.ilike(search_term)
                    )
                )
            )
            .order_by(Product.sold_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, product_id: int, data: ProductUpdate) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update_stock(self, product_id: int, quantity_change: int, sold: bool = False) -> Optional[Product]:
        """Update product stock. If sold=True, also increment sold_count"""
        product = await self.get_by_id(product_id)
        if not product:
            return None

        product.quantity += quantity_change
        if product.quantity < 0:
            product.quantity = 0

        if sold and quantity_change < 0:
            product.sold_count += abs(quantity_change)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def increment_view(self, product_id: int) -> None:
        """Increment product view count"""
        product = await self.get_by_id(product_id)
        if product:
            product.view_count += 1
            await self.db.commit()

    async def delete(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False

        await self.db.delete(product)
        await self.db.commit()
        return True

    async def count(self, active_only: bool = True) -> int:
        query = select(func.count(Product.id))
        if active_only:
            query = query.where(Product.is_active == True)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_low_stock(self) -> List[Product]:
        """Get products with stock at or below minimum level"""
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.is_active == True,
                    Product.quantity <= Product.min_stock_level
                )
            )
            .order_by(Product.quantity)
        )
        return list(result.scalars().all())

    async def get_out_of_stock(self) -> List[Product]:
        """Get products with zero stock"""
        result = await self.db.execute(
            select(Product)
            .where(and_(Product.is_active == True, Product.quantity == 0))
        )
        return list(result.scalars().all())

    async def get_inventory_stats(self) -> Dict[str, Any]:
        """Get inventory statistics"""
        total = await self.count()

        low_stock_result = await self.db.execute(
            select(func.count(Product.id))
            .where(
                and_(
                    Product.is_active == True,
                    Product.quantity <= Product.min_stock_level,
                    Product.quantity > 0
                )
            )
        )
        low_stock = low_stock_result.scalar() or 0

        out_of_stock_result = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(Product.is_active == True, Product.quantity == 0))
        )
        out_of_stock = out_of_stock_result.scalar() or 0

        total_value_result = await self.db.execute(
            select(func.sum(Product.price * Product.quantity))
            .where(Product.is_active == True)
        )
        inventory_value = total_value_result.scalar() or 0

        return {
            "total_products": total,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "in_stock": total - low_stock - out_of_stock,
            "inventory_value": round(inventory_value, 2)
        }
