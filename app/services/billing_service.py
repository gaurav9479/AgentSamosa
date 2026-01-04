from typing import Dict, Any, Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop


class BillingService:
    """Service for handling billing with dynamic pricing and profit tracking"""

    def __init__(self, db: Session):
        self.db = db

    def create_order_with_pricing(
        self,
        product_id: int,
        quantity: int,
        customer_name: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        delivery_address: Optional[str] = None,
        selling_price: Optional[float] = None,  # Bargained price
        shop_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create an order with proper pricing breakdown.
        If selling_price is provided, it's the bargained price.
        Otherwise, uses MRP.
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "error": "Product not found"}

        if product.quantity < quantity:
            return {"success": False, "error": f"Insufficient stock. Available: {product.quantity}"}

        # Pricing calculation
        cost_price = product.cost_price or 0
        listed_price = product.price  # MRP
        final_price = selling_price if selling_price else listed_price

        # Check minimum price constraint
        if product.min_price and final_price < product.min_price:
            return {
                "success": False,
                "error": f"Price ₹{final_price} is below minimum acceptable price ₹{product.min_price}",
                "min_price": product.min_price
            }

        # Check if selling at loss
        if cost_price > 0 and final_price < cost_price:
            return {
                "success": False,
                "error": f"Warning: Selling at ₹{final_price} will result in loss of ₹{cost_price - final_price} per unit",
                "requires_confirmation": True,
                "loss_per_unit": cost_price - final_price
            }

        # Calculate totals
        total_amount = final_price * quantity
        total_cost = cost_price * quantity if cost_price else None
        profit = total_amount - total_cost if total_cost else None
        discount_given = (listed_price - final_price) * quantity

        # Create order
        order = Order(
            shop_id=shop_id or product.shop_id,
            product_id=product_id,
            product_name=product.name,
            quantity=quantity,
            cost_price=cost_price if cost_price else None,
            listed_price=listed_price,
            final_price=final_price,
            unit_price=final_price,
            total_amount=total_amount,
            total_cost=total_cost,
            profit=profit,
            discount_given=discount_given,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            status=OrderStatus.PENDING.value,
        )

        # Update product quantity
        product.quantity -= quantity
        product.sold_count += quantity

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return {
            "success": True,
            "order": order,
            "profit_info": {
                "cost_price": cost_price,
                "listed_price": listed_price,
                "sold_at": final_price,
                "profit": profit,
                "discount_given": discount_given,
            }
        }

    def generate_customer_bill(self, order_id: int) -> Dict[str, Any]:
        """Generate customer-facing bill (no profit info)"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        shop = self.db.query(Shop).filter(Shop.id == order.shop_id).first()
        shop_name = shop.name if shop else "Shop"

        bill = {
            "bill_type": "customer",
            "order_id": order.id,
            "shop_name": shop_name,
            "date": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": [
                {
                    "name": order.product_name,
                    "quantity": order.quantity,
                    "unit_price": order.unit_price,
                    "total": order.total_amount,
                }
            ],
            "subtotal": order.total_amount,
            "tax": 0,  # Add tax calculation if needed
            "grand_total": order.total_amount,
            "customer": {
                "name": order.customer_name,
                "phone": order.customer_phone,
                "email": order.customer_email,
            },
            "status": order.status,
        }

        return {"success": True, "bill": bill}

    def generate_admin_bill(self, order_id: int) -> Dict[str, Any]:
        """Generate admin-facing bill with full profit breakdown"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        shop = self.db.query(Shop).filter(Shop.id == order.shop_id).first()
        shop_name = shop.name if shop else "Shop"

        # Calculate profit margin
        profit_margin = 0
        if order.total_cost and order.total_cost > 0:
            profit_margin = round(((order.profit or 0) / order.total_cost) * 100, 2)

        bill = {
            "bill_type": "admin",
            "order_id": order.id,
            "shop_name": shop_name,
            "date": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": [
                {
                    "name": order.product_name,
                    "quantity": order.quantity,
                    "cost_price": order.cost_price,
                    "mrp": order.listed_price,
                    "sold_at": order.final_price,
                    "total_cost": order.total_cost,
                    "total_revenue": order.total_amount,
                    "profit": order.profit,
                }
            ],
            "summary": {
                "subtotal": order.total_amount,
                "total_cost": order.total_cost,
                "total_profit": order.profit,
                "discount_given": order.discount_given,
                "profit_margin_percent": profit_margin,
            },
            "customer": {
                "name": order.customer_name,
                "phone": order.customer_phone,
                "email": order.customer_email,
            },
            "status": order.status,
        }

        return {"success": True, "bill": bill}

    def get_daily_profit_report(
        self, shop_id: int, report_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get daily profit report for a shop"""
        if not report_date:
            report_date = date.today()

        orders = (
            self.db.query(Order)
            .filter(
                Order.shop_id == shop_id,
                func.date(Order.created_at) == report_date,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .all()
        )

        total_revenue = sum(o.total_amount for o in orders)
        total_cost = sum(o.total_cost or 0 for o in orders)
        total_profit = sum(o.profit or 0 for o in orders)
        total_discount = sum(o.discount_given or 0 for o in orders)

        avg_margin = 0
        if total_cost > 0:
            avg_margin = round((total_profit / total_cost) * 100, 2)

        return {
            "success": True,
            "report": {
                "date": report_date.strftime("%Y-%m-%d"),
                "total_orders": len(orders),
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_profit, 2),
                "total_discount_given": round(total_discount, 2),
                "avg_profit_margin": avg_margin,
            }
        }

    def get_product_profit_report(self, shop_id: int) -> Dict[str, Any]:
        """Get profit report per product for a shop"""
        # Group orders by product
        results = (
            self.db.query(
                Order.product_id,
                Order.product_name,
                func.sum(Order.quantity).label("units_sold"),
                func.sum(Order.total_amount).label("total_revenue"),
                func.sum(Order.total_cost).label("total_cost"),
                func.sum(Order.profit).label("total_profit"),
            )
            .filter(
                Order.shop_id == shop_id,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .group_by(Order.product_id, Order.product_name)
            .all()
        )

        products = []
        for r in results:
            units = r.units_sold or 0
            revenue = r.total_revenue or 0
            profit = r.total_profit or 0

            products.append({
                "product_id": r.product_id,
                "product_name": r.product_name,
                "units_sold": units,
                "total_revenue": round(revenue, 2),
                "total_cost": round(r.total_cost or 0, 2),
                "total_profit": round(profit, 2),
                "avg_selling_price": round(revenue / units, 2) if units > 0 else 0,
                "avg_profit_per_unit": round(profit / units, 2) if units > 0 else 0,
            })

        # Sort by profit descending
        products.sort(key=lambda x: x["total_profit"], reverse=True)

        return {"success": True, "products": products}

    def sell_at_price(
        self,
        product_id: int,
        selling_price: float,
        quantity: int,
        customer_name: str,
        customer_phone: Optional[str] = None,
        force: bool = False,  # Force sale even at loss
    ) -> Dict[str, Any]:
        """
        Quick sale at bargained price.
        This is the main command for "sell product X at Y price"
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "error": "Product not found"}

        cost_price = product.cost_price or 0

        # Check minimum price
        if product.min_price and selling_price < product.min_price and not force:
            return {
                "success": False,
                "error": f"Price ₹{selling_price} is below minimum ₹{product.min_price}",
                "requires_confirmation": True,
                "confirmation_type": "below_min_price",
            }

        # Check if selling at loss
        if cost_price > 0 and selling_price < cost_price and not force:
            loss = cost_price - selling_price
            return {
                "success": False,
                "error": f"Selling at ₹{selling_price} results in loss of ₹{loss}/unit",
                "requires_confirmation": True,
                "confirmation_type": "selling_at_loss",
                "loss_per_unit": loss,
            }

        # Create the order
        return self.create_order_with_pricing(
            product_id=product_id,
            quantity=quantity,
            customer_name=customer_name,
            customer_phone=customer_phone,
            selling_price=selling_price,
        )

    def get_shop_profit_summary(self, shop_id: int) -> Dict[str, Any]:
        """Get overall profit summary for shop dashboard"""
        # All time stats
        all_orders = (
            self.db.query(Order)
            .filter(
                Order.shop_id == shop_id,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .all()
        )

        # Today's stats
        today = date.today()
        today_orders = [
            o for o in all_orders
            if o.created_at.date() == today
        ]

        def calc_stats(orders):
            revenue = sum(o.total_amount for o in orders)
            cost = sum(o.total_cost or 0 for o in orders)
            profit = sum(o.profit or 0 for o in orders)
            discount = sum(o.discount_given or 0 for o in orders)
            margin = round((profit / cost) * 100, 2) if cost > 0 else 0
            return {
                "orders": len(orders),
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "profit": round(profit, 2),
                "discount_given": round(discount, 2),
                "margin_percent": margin,
            }

        return {
            "success": True,
            "summary": {
                "today": calc_stats(today_orders),
                "all_time": calc_stats(all_orders),
            }
        }
