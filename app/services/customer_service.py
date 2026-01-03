from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
        )
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Customer]:
        query = select(Customer)
        if active_only:
            query = query.where(Customer.is_active == True)
        query = query.offset(skip).limit(limit).order_by(Customer.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, customer_id: int, data: CustomerUpdate
    ) -> Optional[Customer]:
        customer = await self.get_by_id(customer_id)
        if not customer:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def delete(self, customer_id: int) -> bool:
        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        await self.db.delete(customer)
        await self.db.commit()
        return True

    async def update_stats(self, customer_id: int, order_total: float) -> None:
        """Update customer stats when an order is placed"""
        customer = await self.get_by_id(customer_id)
        if customer:
            customer.total_orders += 1
            customer.total_spent += order_total
            await self.db.commit()

    async def get_top_customers(self, limit: int = 5) -> List[Customer]:
        """Get top customers by total spent"""
        result = await self.db.execute(
            select(Customer)
            .where(Customer.is_active == True)
            .order_by(Customer.total_spent.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(self, query: str) -> List[Customer]:
        """Search customers by name or email"""
        result = await self.db.execute(
            select(Customer).where(
                (Customer.name.ilike(f"%{query}%")) |
                (Customer.email.ilike(f"%{query}%"))
            )
        )
        return list(result.scalars().all())
