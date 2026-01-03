from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.customer import Customer


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get overall dashboard statistics"""
        # Total products
        products_result = await self.db.execute(select(func.count(Product.id)))
        total_products = products_result.scalar() or 0

        # Total orders
        orders_result = await self.db.execute(select(func.count(Order.id)))
        total_orders = orders_result.scalar() or 0

        # Total customers
        customers_result = await self.db.execute(select(func.count(Customer.id)))
        total_customers = customers_result.scalar() or 0

        # Total revenue (excluding cancelled orders)
        revenue_result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(
                Order.status != OrderStatus.CANCELLED.value
            )
        )
        total_revenue = revenue_result.scalar() or 0.0

        # Pending orders
        pending_result = await self.db.execute(
            select(func.count(Order.id)).where(
                Order.status == OrderStatus.PENDING.value
            )
        )
        pending_orders = pending_result.scalar() or 0

        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_revenue": round(total_revenue, 2),
            "pending_orders": pending_orders,
            "avg_order_value": round(avg_order_value, 2),
        }

    async def get_order_status_distribution(self) -> List[Dict[str, Any]]:
        """Get order count by status for pie chart"""
        result = await self.db.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )
        rows = result.all()
        return [{"status": row[0], "count": row[1]} for row in rows]

    async def get_revenue_by_day(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily revenue for the last N days"""
        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date(Order.created_at).label("date"),
                func.sum(Order.total_amount).label("revenue"),
                func.count(Order.id).label("orders")
            )
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        rows = result.all()

        # Fill in missing days with zero
        date_data = {str(row[0]): {"revenue": float(row[1]), "orders": row[2]} for row in rows}

        all_days = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-1-i)).strftime("%Y-%m-%d")
            if date in date_data:
                all_days.append({
                    "date": date,
                    "revenue": date_data[date]["revenue"],
                    "orders": date_data[date]["orders"]
                })
            else:
                all_days.append({"date": date, "revenue": 0, "orders": 0})

        return all_days

    async def get_top_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top selling products by quantity sold"""
        result = await self.db.execute(
            select(
                Order.product_name,
                func.sum(Order.quantity).label("total_sold"),
                func.sum(Order.total_amount).label("total_revenue")
            )
            .where(Order.status != OrderStatus.CANCELLED.value)
            .group_by(Order.product_name)
            .order_by(func.sum(Order.quantity).desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "product_name": row[0],
                "total_sold": int(row[1]),
                "total_revenue": float(row[2])
            }
            for row in rows
        ]

    async def get_top_customers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top customers by total spent"""
        result = await self.db.execute(
            select(Customer)
            .where(Customer.is_active == True)
            .order_by(Customer.total_spent.desc())
            .limit(limit)
        )
        customers = result.scalars().all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "total_orders": c.total_orders,
                "total_spent": c.total_spent
            }
            for c in customers
        ]

    async def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent orders"""
        result = await self.db.execute(
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        orders = result.scalars().all()
        return [
            {
                "id": o.id,
                "customer_name": o.customer_name,
                "product_name": o.product_name,
                "total_amount": o.total_amount,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None
            }
            for o in orders
        ]

    async def get_monthly_comparison(self) -> Dict[str, Any]:
        """Compare this month vs last month"""
        now = datetime.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        # This month revenue
        this_month_result = await self.db.execute(
            select(func.sum(Order.total_amount), func.count(Order.id))
            .where(
                and_(
                    Order.created_at >= this_month_start,
                    Order.status != OrderStatus.CANCELLED.value
                )
            )
        )
        this_month = this_month_result.one()

        # Last month revenue
        last_month_result = await self.db.execute(
            select(func.sum(Order.total_amount), func.count(Order.id))
            .where(
                and_(
                    Order.created_at >= last_month_start,
                    Order.created_at < this_month_start,
                    Order.status != OrderStatus.CANCELLED.value
                )
            )
        )
        last_month = last_month_result.one()

        this_revenue = this_month[0] or 0
        last_revenue = last_month[0] or 0

        growth = 0
        if last_revenue > 0:
            growth = ((this_revenue - last_revenue) / last_revenue) * 100

        return {
            "this_month": {
                "revenue": float(this_revenue),
                "orders": this_month[1] or 0
            },
            "last_month": {
                "revenue": float(last_revenue),
                "orders": last_month[1] or 0
            },
            "growth_percentage": round(growth, 1)
        }
