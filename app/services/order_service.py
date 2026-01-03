from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: OrderCreate) -> Optional[Order]:
        # Get product to calculate total
        result = await self.db.execute(
            select(Product).where(Product.id == data.product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            return None

        unit_price = product.price
        total_amount = unit_price * data.quantity

        order = Order(
            shop_id=product.shop_id,  # Set shop from product
            product_id=data.product_id,
            product_name=product.name,  # Snapshot product name
            unit_price=unit_price,  # Snapshot price at order time
            quantity=data.quantity,
            total_amount=total_amount,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        query = select(Order)
        if status:
            query = query.where(Order.status == status)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, order_id: int, data: OrderUpdate
    ) -> Optional[Order]:
        order = await self.get_by_id(order_id)
        if not order:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def cancel(self, order_id: int) -> Optional[Order]:
        order = await self.get_by_id(order_id)
        if not order:
            return None

        if order.status in [OrderStatus.SHIPPED.value, OrderStatus.DELIVERED.value]:
            return None  # Cannot cancel shipped/delivered orders

        order.status = OrderStatus.CANCELLED.value
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_last_order(self) -> Optional[Order]:
        result = await self.db.execute(
            select(Order).order_by(Order.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_shop(
        self, shop_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all orders for a specific shop"""
        conditions = [Order.shop_id == shop_id]
        if status:
            conditions.append(Order.status == status)

        result = await self.db.execute(
            select(Order)
            .where(and_(*conditions))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
