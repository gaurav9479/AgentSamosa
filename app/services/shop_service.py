from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.shop import Shop, ShopCategory
from app.models.product import Product
from app.models.order import Order
from app.schemas.shop import ShopCreate, ShopUpdate, ShopCategoryCreate, ShopCategoryUpdate


class ShopCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ShopCategoryCreate) -> ShopCategory:
        category = ShopCategory(**data.model_dump())
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_by_id(self, category_id: int) -> Optional[ShopCategory]:
        result = await self.db.execute(
            select(ShopCategory).where(ShopCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ShopCategory]:
        result = await self.db.execute(
            select(ShopCategory).where(ShopCategory.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> List[ShopCategory]:
        query = select(ShopCategory)
        if active_only:
            query = query.where(ShopCategory.is_active == True)
        query = query.order_by(ShopCategory.sort_order, ShopCategory.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_shop_count(self) -> List[Dict[str, Any]]:
        """Get categories with shop counts"""
        result = await self.db.execute(
            select(
                ShopCategory,
                func.count(Shop.id).label("shop_count")
            )
            .outerjoin(Shop, and_(Shop.category_id == ShopCategory.id, Shop.is_active == True))
            .where(ShopCategory.is_active == True)
            .group_by(ShopCategory.id)
            .order_by(ShopCategory.sort_order, ShopCategory.name)
        )
        rows = result.all()
        return [
            {
                "id": row[0].id,
                "name": row[0].name,
                "description": row[0].description,
                "icon": row[0].icon,
                "image_url": row[0].image_url,
                "is_active": row[0].is_active,
                "sort_order": row[0].sort_order,
                "created_at": row[0].created_at,
                "shop_count": row[1]
            }
            for row in rows
        ]

    async def update(self, category_id: int, data: ShopCategoryUpdate) -> Optional[ShopCategory]:
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


class ShopService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ShopCreate) -> Shop:
        shop = Shop(**data.model_dump())
        self.db.add(shop)
        await self.db.commit()
        await self.db.refresh(shop)
        return shop

    async def get_by_id(self, shop_id: int) -> Optional[Shop]:
        result = await self.db.execute(
            select(Shop).where(Shop.id == shop_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Shop]:
        result = await self.db.execute(
            select(Shop).where(Shop.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[int] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[Shop]:
        query = select(Shop)

        if active_only:
            query = query.where(Shop.is_active == True)

        if category_id:
            query = query.where(Shop.category_id == category_id)

        if city:
            query = query.where(Shop.city.ilike(f"%{city}%"))

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Shop.name.ilike(search_term),
                    Shop.description.ilike(search_term)
                )
            )

        query = query.order_by(Shop.rating.desc(), Shop.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_category(self, category_id: int) -> List[Shop]:
        result = await self.db.execute(
            select(Shop)
            .where(and_(Shop.category_id == category_id, Shop.is_active == True))
            .order_by(Shop.rating.desc(), Shop.name)
        )
        return list(result.scalars().all())

    async def update(self, shop_id: int, data: ShopUpdate) -> Optional[Shop]:
        shop = await self.get_by_id(shop_id)
        if not shop:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shop, field, value)
        await self.db.commit()
        await self.db.refresh(shop)
        return shop

    async def delete(self, shop_id: int) -> bool:
        shop = await self.get_by_id(shop_id)
        if not shop:
            return False
        await self.db.delete(shop)
        await self.db.commit()
        return True

    async def get_dashboard_stats(self, shop_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard stats for a shop owner"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Product stats
        total_products = await self.db.execute(
            select(func.count(Product.id))
            .where(Product.shop_id == shop_id)
        )
        total_products = total_products.scalar() or 0

        active_products = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(Product.shop_id == shop_id, Product.is_active == True))
        )
        active_products = active_products.scalar() or 0

        low_stock = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(
                Product.shop_id == shop_id,
                Product.is_active == True,
                Product.quantity <= Product.min_stock_level,
                Product.quantity > 0
            ))
        )
        low_stock = low_stock.scalar() or 0

        out_of_stock = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(
                Product.shop_id == shop_id,
                Product.is_active == True,
                Product.quantity == 0
            ))
        )
        out_of_stock = out_of_stock.scalar() or 0

        # Inventory value
        inv_value = await self.db.execute(
            select(func.sum(Product.price * Product.quantity))
            .where(and_(Product.shop_id == shop_id, Product.is_active == True))
        )
        inventory_value = inv_value.scalar() or 0

        # Order stats
        total_orders = await self.db.execute(
            select(func.count(Order.id))
            .where(Order.shop_id == shop_id)
        )
        total_orders = total_orders.scalar() or 0

        pending_orders = await self.db.execute(
            select(func.count(Order.id))
            .where(and_(Order.shop_id == shop_id, Order.status == "pending"))
        )
        pending_orders = pending_orders.scalar() or 0

        today_orders = await self.db.execute(
            select(func.count(Order.id))
            .where(and_(Order.shop_id == shop_id, Order.created_at >= today))
        )
        today_orders = today_orders.scalar() or 0

        # Revenue
        total_revenue = await self.db.execute(
            select(func.sum(Order.total_amount))
            .where(and_(Order.shop_id == shop_id, Order.status != "cancelled"))
        )
        total_revenue = total_revenue.scalar() or 0

        today_revenue = await self.db.execute(
            select(func.sum(Order.total_amount))
            .where(and_(
                Order.shop_id == shop_id,
                Order.status != "cancelled",
                Order.created_at >= today
            ))
        )
        today_revenue = today_revenue.scalar() or 0

        # Unique customers
        total_customers = await self.db.execute(
            select(func.count(func.distinct(Order.customer_email)))
            .where(Order.shop_id == shop_id)
        )
        total_customers = total_customers.scalar() or 0

        return {
            "total_products": total_products,
            "active_products": active_products,
            "low_stock_count": low_stock,
            "out_of_stock_count": out_of_stock,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "today_orders": today_orders,
            "total_revenue": round(total_revenue, 2),
            "today_revenue": round(today_revenue, 2),
            "total_customers": total_customers,
            "inventory_value": round(inventory_value, 2)
        }

    async def update_shop_metrics(self, shop_id: int, order_amount: float):
        """Update shop metrics after an order"""
        shop = await self.get_by_id(shop_id)
        if shop:
            shop.total_orders += 1
            shop.total_revenue += order_amount
            await self.db.commit()
