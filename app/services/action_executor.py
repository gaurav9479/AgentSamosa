import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.command import ParsedIntent, CommandResponse, MultiStepPlan
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.order import OrderCreate, OrderUpdate
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.shop import ShopCreate, ShopUpdate
from app.schemas.user import UserCreate, UserUpdate
from app.services.product_service import ProductService, CategoryService
from app.services.order_service import OrderService
from app.services.customer_service import CustomerService
from app.services.shop_service import ShopService, ShopCategoryService
from app.services.user_service import UserService
from app.services.analytics_service import AnalyticsService
from app.services.billing_service import BillingService


class ActionExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
        self.order_service = OrderService(db)
        self.customer_service = CustomerService(db)
        self.shop_service = ShopService(db)
        self.shop_category_service = ShopCategoryService(db)
        self.user_service = UserService(db)
        self.category_service = CategoryService(db)
        self.analytics_service = AnalyticsService(db)
        self.billing_service = BillingService(db)
        self.pending_confirmations: Dict[str, ParsedIntent] = {}

    async def execute(
        self, intent: ParsedIntent, confirmed: bool = False
    ) -> CommandResponse:
        # Check if confirmation is required
        if intent.requires_confirmation and not confirmed:
            confirmation_id = str(uuid.uuid4())
            self.pending_confirmations[confirmation_id] = intent
            return CommandResponse(
                success=False,
                action=intent.action,
                message=intent.confirmation_message or f"Are you sure you want to {intent.action}?",
                requires_confirmation=True,
                confirmation_id=confirmation_id,
            )

        # Route to appropriate handler
        action_handlers = {
            # Product actions
            "create_product": self._create_product,
            "update_product": self._update_product,
            "delete_product": self._delete_product,
            "list_products": self._list_products,
            "get_product": self._get_product,
            "search_products": self._search_products,
            "get_low_stock": self._get_low_stock,
            "restock_product": self._restock_product,
            "set_product_price": self._set_product_price,
            "toggle_product_status": self._toggle_product_status,
            "set_featured": self._set_featured,
            # Order actions
            "create_order": self._create_order,
            "update_order": self._update_order,
            "cancel_order": self._cancel_order,
            "list_orders": self._list_orders,
            "get_order": self._get_order,
            "confirm_order": self._confirm_order,
            "ship_order": self._ship_order,
            "deliver_order": self._deliver_order,
            "refund_order": self._refund_order,
            # Customer actions
            "create_customer": self._create_customer,
            "update_customer": self._update_customer,
            "delete_customer": self._delete_customer,
            "list_customers": self._list_customers,
            "get_customer": self._get_customer,
            "search_customers": self._search_customers,
            # Customer order actions
            "place_order": self._place_order,
            "list_my_orders": self._list_my_orders,
            # Shop actions (Super Admin)
            "prefill_shop_form": self._prefill_shop_form,
            "create_shop": self._create_shop,
            "update_shop": self._update_shop,
            "delete_shop": self._delete_shop,
            "list_shops": self._list_shops,
            "get_shop": self._get_shop,
            "verify_shop": self._verify_shop,
            "suspend_shop": self._suspend_shop,
            "activate_shop": self._activate_shop,
            "get_pending_shops": self._get_pending_shops,
            # Shop dashboard actions (Shop Admin)
            "get_shop_dashboard": self._get_shop_dashboard,
            "get_shop_low_stock": self._get_shop_low_stock,
            "get_shop_orders": self._get_shop_orders,
            # User actions (Super Admin)
            "create_user": self._create_user,
            "update_user": self._update_user,
            "delete_user": self._delete_user,
            "list_users": self._list_users,
            "get_user": self._get_user,
            # Platform actions (Super Admin)
            "get_platform_stats": self._get_platform_stats,
            # Category actions
            "list_shop_categories": self._list_shop_categories,
            "list_product_categories": self._list_product_categories,
            "create_shop_category": self._create_shop_category,
            "create_product_category": self._create_product_category,
            # Analytics actions
            "get_analytics": self._get_analytics,
            # Billing actions (Shop Admin)
            "sell_at_price": self._sell_at_price,
            "generate_bill": self._generate_bill,
            "get_daily_profit": self._get_daily_profit,
            "get_product_profit": self._get_product_profit,
            "get_profit_summary": self._get_profit_summary,
            # Error handling
            "error": self._handle_error,
        }

        handler = action_handlers.get(intent.action)
        if not handler:
            return CommandResponse(
                success=False,
                action=intent.action,
                message=f"Unknown action: {intent.action}",
            )

        return await handler(intent.parameters)

    async def confirm_action(self, confirmation_id: str) -> CommandResponse:
        intent = self.pending_confirmations.pop(confirmation_id, None)
        if not intent:
            return CommandResponse(
                success=False,
                action="confirm",
                message="Invalid or expired confirmation ID",
            )
        return await self.execute(intent, confirmed=True)

    async def execute_plan(self, plan: MultiStepPlan) -> List[CommandResponse]:
        results = []
        for step in plan.steps:
            result = await self.execute(step)
            results.append(result)
            if not result.success and not result.requires_confirmation:
                break  # Stop on failure
        return results

    # Product handlers
    async def _create_product(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            data = ProductCreate(
                name=params["name"],
                price=params["price"],
                description=params.get("description"),
                quantity=params.get("quantity", 0),
            )
            product = await self.product_service.create(data)
            return CommandResponse(
                success=True,
                action="create_product",
                message=f"Created product '{product.name}' with ID {product.id}",
                data={"id": product.id, "name": product.name, "price": product.price},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_product",
                message=f"Missing required parameter: {e}",
            )

    async def _update_product(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        if not product_id:
            return CommandResponse(
                success=False,
                action="update_product",
                message="Product ID is required",
            )

        update_data = {k: v for k, v in params.items() if k != "product_id" and v is not None}
        data = ProductUpdate(**update_data)
        product = await self.product_service.update(product_id, data)

        if not product:
            return CommandResponse(
                success=False,
                action="update_product",
                message=f"Product {product_id} not found",
            )

        return CommandResponse(
            success=True,
            action="update_product",
            message=f"Updated product {product.id}",
            data={"id": product.id, "name": product.name, "price": product.price},
        )

    async def _delete_product(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        if not product_id:
            return CommandResponse(
                success=False,
                action="delete_product",
                message="Product ID is required",
            )

        success = await self.product_service.delete(product_id)
        if not success:
            return CommandResponse(
                success=False,
                action="delete_product",
                message=f"Product {product_id} not found",
            )

        return CommandResponse(
            success=True,
            action="delete_product",
            message=f"Deleted product {product_id}",
        )

    async def _list_products(self, params: Dict[str, Any]) -> CommandResponse:
        products = await self.product_service.get_all()
        return CommandResponse(
            success=True,
            action="list_products",
            message=f"Found {len(products)} products",
            data=[{"id": p.id, "name": p.name, "price": p.price, "quantity": p.quantity} for p in products],
        )

    async def _get_product(self, params: Dict[str, Any]) -> CommandResponse:
        product = None
        if "product_id" in params:
            product = await self.product_service.get_by_id(params["product_id"])
        elif "name" in params:
            product = await self.product_service.get_by_name(params["name"])

        if not product:
            return CommandResponse(
                success=False,
                action="get_product",
                message="Product not found",
            )

        return CommandResponse(
            success=True,
            action="get_product",
            message=f"Found product: {product.name}",
            data={"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity},
        )

    # Order handlers
    async def _create_order(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            data = OrderCreate(
                product_id=params["product_id"],
                quantity=params["quantity"],
                customer_name=params["customer_name"],
                customer_email=params.get("customer_email"),
            )
            order = await self.order_service.create(data)
            if not order:
                return CommandResponse(
                    success=False,
                    action="create_order",
                    message="Failed to create order. Product may not exist.",
                )

            return CommandResponse(
                success=True,
                action="create_order",
                message=f"Created order #{order.id} for {order.customer_name}",
                data={"id": order.id, "total": order.total_amount, "status": order.status},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_order",
                message=f"Missing required parameter: {e}",
            )

    async def _update_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        if not order_id:
            return CommandResponse(
                success=False,
                action="update_order",
                message="Order ID is required",
            )

        update_data = {k: v for k, v in params.items() if k != "order_id" and v is not None}
        data = OrderUpdate(**update_data)
        order = await self.order_service.update(order_id, data)

        if not order:
            return CommandResponse(
                success=False,
                action="update_order",
                message=f"Order {order_id} not found",
            )

        return CommandResponse(
            success=True,
            action="update_order",
            message=f"Updated order #{order.id}",
            data={"id": order.id, "status": order.status, "total": order.total_amount},
        )

    async def _cancel_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        if not order_id:
            return CommandResponse(
                success=False,
                action="cancel_order",
                message="Order ID is required",
            )

        order = await self.order_service.cancel(order_id)
        if not order:
            return CommandResponse(
                success=False,
                action="cancel_order",
                message=f"Cannot cancel order {order_id}. It may not exist or has already been shipped.",
            )

        return CommandResponse(
            success=True,
            action="cancel_order",
            message=f"Cancelled order #{order.id}",
            data={"id": order.id, "status": order.status},
        )

    async def _list_orders(self, params: Dict[str, Any]) -> CommandResponse:
        status = params.get("status")
        orders = await self.order_service.get_all(status=status)
        return CommandResponse(
            success=True,
            action="list_orders",
            message=f"Found {len(orders)} orders",
            data=[{
                "id": o.id,
                "status": o.status,
                "total": o.total_amount,
                "customer": o.customer_name,
                "product_name": o.product_name,
                "unit_price": o.unit_price,
                "quantity": o.quantity
            } for o in orders],
        )

    async def _get_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        if not order_id:
            return CommandResponse(
                success=False,
                action="get_order",
                message="Order ID is required",
            )

        order = await self.order_service.get_by_id(order_id)
        if not order:
            return CommandResponse(
                success=False,
                action="get_order",
                message=f"Order {order_id} not found",
            )

        return CommandResponse(
            success=True,
            action="get_order",
            message=f"Found order #{order.id}",
            data={"id": order.id, "status": order.status, "total": order.total_amount, "customer": order.customer_name},
        )

    async def _handle_error(self, params: Dict[str, Any]) -> CommandResponse:
        return CommandResponse(
            success=False,
            action="error",
            message=params.get("error", "An unknown error occurred"),
        )

    # Customer handlers
    async def _create_customer(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            data = CustomerCreate(
                name=params["name"],
                email=params["email"],
                phone=params.get("phone"),
                address=params.get("address"),
            )
            # Check if email already exists
            existing = await self.customer_service.get_by_email(data.email)
            if existing:
                return CommandResponse(
                    success=False,
                    action="create_customer",
                    message=f"Customer with email {data.email} already exists",
                )
            customer = await self.customer_service.create(data)
            return CommandResponse(
                success=True,
                action="create_customer",
                message=f"Created customer '{customer.name}' with ID {customer.id}",
                data={"id": customer.id, "name": customer.name, "email": customer.email},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_customer",
                message=f"Missing required parameter: {e}",
            )

    async def _update_customer(self, params: Dict[str, Any]) -> CommandResponse:
        customer_id = params.get("customer_id")
        if not customer_id:
            return CommandResponse(
                success=False,
                action="update_customer",
                message="Customer ID is required",
            )

        update_data = {k: v for k, v in params.items() if k != "customer_id" and v is not None}
        data = CustomerUpdate(**update_data)
        customer = await self.customer_service.update(customer_id, data)

        if not customer:
            return CommandResponse(
                success=False,
                action="update_customer",
                message=f"Customer {customer_id} not found",
            )

        return CommandResponse(
            success=True,
            action="update_customer",
            message=f"Updated customer {customer.id}",
            data={"id": customer.id, "name": customer.name, "email": customer.email},
        )

    async def _delete_customer(self, params: Dict[str, Any]) -> CommandResponse:
        customer_id = params.get("customer_id")
        if not customer_id:
            return CommandResponse(
                success=False,
                action="delete_customer",
                message="Customer ID is required",
            )

        success = await self.customer_service.delete(customer_id)
        if not success:
            return CommandResponse(
                success=False,
                action="delete_customer",
                message=f"Customer {customer_id} not found",
            )

        return CommandResponse(
            success=True,
            action="delete_customer",
            message=f"Deleted customer {customer_id}",
        )

    async def _list_customers(self, params: Dict[str, Any]) -> CommandResponse:
        customers = await self.customer_service.get_all()
        return CommandResponse(
            success=True,
            action="list_customers",
            message=f"Found {len(customers)} customers",
            data=[{
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "total_orders": c.total_orders,
                "total_spent": c.total_spent
            } for c in customers],
        )

    async def _get_customer(self, params: Dict[str, Any]) -> CommandResponse:
        customer = None
        if "customer_id" in params:
            customer = await self.customer_service.get_by_id(params["customer_id"])
        elif "email" in params:
            customer = await self.customer_service.get_by_email(params["email"])

        if not customer:
            return CommandResponse(
                success=False,
                action="get_customer",
                message="Customer not found",
            )

        return CommandResponse(
            success=True,
            action="get_customer",
            message=f"Found customer: {customer.name}",
            data={"id": customer.id, "name": customer.name, "email": customer.email, "phone": customer.phone},
        )

    async def _search_customers(self, params: Dict[str, Any]) -> CommandResponse:
        query = params.get("query")
        if not query:
            return CommandResponse(
                success=False,
                action="search_customers",
                message="Search query is required",
            )

        customers = await self.customer_service.search(query)
        return CommandResponse(
            success=True,
            action="search_customers",
            message=f"Found {len(customers)} customers matching '{query}'",
            data=[{"id": c.id, "name": c.name, "email": c.email} for c in customers],
        )

    # Additional Product handlers
    async def _search_products(self, params: Dict[str, Any]) -> CommandResponse:
        query = params.get("query")
        if not query:
            return CommandResponse(
                success=False,
                action="search_products",
                message="Search query is required",
            )
        limit = params.get("limit", 20)
        products = await self.product_service.search(query, limit)
        return CommandResponse(
            success=True,
            action="search_products",
            message=f"Found {len(products)} products matching '{query}'",
            data=[{"id": p.id, "name": p.name, "price": p.price, "quantity": p.quantity} for p in products],
        )

    async def _get_low_stock(self, params: Dict[str, Any]) -> CommandResponse:
        shop_id = params.get("shop_id")
        products = await self.product_service.get_low_stock(shop_id)
        return CommandResponse(
            success=True,
            action="get_low_stock",
            message=f"Found {len(products)} low stock products",
            data=[{
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "quantity": p.quantity,
                "min_stock_level": p.min_stock_level
            } for p in products],
        )

    async def _restock_product(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        quantity = params.get("quantity")
        if not product_id:
            return CommandResponse(
                success=False,
                action="restock_product",
                message="Product ID is required",
            )
        if not quantity or quantity <= 0:
            return CommandResponse(
                success=False,
                action="restock_product",
                message="Quantity must be a positive number",
            )

        product = await self.product_service.get_by_id(product_id)
        if not product:
            return CommandResponse(
                success=False,
                action="restock_product",
                message=f"Product {product_id} not found",
            )

        await self.product_service.update_stock(product_id, quantity)
        updated_product = await self.product_service.get_by_id(product_id)

        return CommandResponse(
            success=True,
            action="restock_product",
            message=f"Added {quantity} units to '{product.name}'. New stock: {updated_product.quantity}",
            data={"id": product_id, "name": product.name, "quantity": updated_product.quantity},
        )

    async def _set_product_price(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        price = params.get("price")
        if not product_id:
            return CommandResponse(
                success=False,
                action="set_product_price",
                message="Product ID is required",
            )
        if price is None or price < 0:
            return CommandResponse(
                success=False,
                action="set_product_price",
                message="Price must be a valid positive number",
            )

        product = await self.product_service.get_by_id(product_id)
        if not product:
            return CommandResponse(
                success=False,
                action="set_product_price",
                message=f"Product {product_id} not found",
            )

        old_price = product.price
        data = ProductUpdate(price=price)
        updated = await self.product_service.update(product_id, data)

        return CommandResponse(
            success=True,
            action="set_product_price",
            message=f"Updated '{product.name}' price from ${old_price} to ${price}",
            data={"id": product_id, "name": product.name, "old_price": old_price, "new_price": price},
        )

    async def _toggle_product_status(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        is_active = params.get("is_active")
        if not product_id:
            return CommandResponse(
                success=False,
                action="toggle_product_status",
                message="Product ID is required",
            )

        product = await self.product_service.get_by_id(product_id)
        if not product:
            return CommandResponse(
                success=False,
                action="toggle_product_status",
                message=f"Product {product_id} not found",
            )

        # If is_active not specified, toggle current status
        new_status = is_active if is_active is not None else not product.is_active
        data = ProductUpdate(is_active=new_status)
        await self.product_service.update(product_id, data)

        status_text = "activated" if new_status else "deactivated"
        return CommandResponse(
            success=True,
            action="toggle_product_status",
            message=f"Product '{product.name}' has been {status_text}",
            data={"id": product_id, "name": product.name, "is_active": new_status},
        )

    async def _set_featured(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        is_featured = params.get("is_featured", True)
        if not product_id:
            return CommandResponse(
                success=False,
                action="set_featured",
                message="Product ID is required",
            )

        product = await self.product_service.get_by_id(product_id)
        if not product:
            return CommandResponse(
                success=False,
                action="set_featured",
                message=f"Product {product_id} not found",
            )

        data = ProductUpdate(is_featured=is_featured)
        await self.product_service.update(product_id, data)

        status_text = "marked as featured" if is_featured else "removed from featured"
        return CommandResponse(
            success=True,
            action="set_featured",
            message=f"Product '{product.name}' has been {status_text}",
            data={"id": product_id, "name": product.name, "is_featured": is_featured},
        )

    # Order status handlers
    async def _confirm_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        if not order_id:
            return CommandResponse(
                success=False,
                action="confirm_order",
                message="Order ID is required",
            )

        order = await self.order_service.get_by_id(order_id)
        if not order:
            return CommandResponse(
                success=False,
                action="confirm_order",
                message=f"Order {order_id} not found",
            )

        if order.status != "pending":
            return CommandResponse(
                success=False,
                action="confirm_order",
                message=f"Order {order_id} cannot be confirmed. Current status: {order.status}",
            )

        from app.schemas.order import OrderUpdate
        data = OrderUpdate(status="confirmed")
        updated = await self.order_service.update(order_id, data)

        return CommandResponse(
            success=True,
            action="confirm_order",
            message=f"Order #{order_id} has been confirmed",
            data={"id": order_id, "status": "confirmed", "customer": order.customer_name},
        )

    async def _ship_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        tracking_number = params.get("tracking_number")
        if not order_id:
            return CommandResponse(
                success=False,
                action="ship_order",
                message="Order ID is required",
            )

        order = await self.order_service.get_by_id(order_id)
        if not order:
            return CommandResponse(
                success=False,
                action="ship_order",
                message=f"Order {order_id} not found",
            )

        if order.status not in ["pending", "confirmed"]:
            return CommandResponse(
                success=False,
                action="ship_order",
                message=f"Order {order_id} cannot be shipped. Current status: {order.status}",
            )

        from app.schemas.order import OrderUpdate
        data = OrderUpdate(status="shipped")
        updated = await self.order_service.update(order_id, data)

        msg = f"Order #{order_id} has been marked as shipped"
        if tracking_number:
            msg += f" (Tracking: {tracking_number})"

        return CommandResponse(
            success=True,
            action="ship_order",
            message=msg,
            data={"id": order_id, "status": "shipped", "tracking_number": tracking_number},
        )

    async def _deliver_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        if not order_id:
            return CommandResponse(
                success=False,
                action="deliver_order",
                message="Order ID is required",
            )

        order = await self.order_service.get_by_id(order_id)
        if not order:
            return CommandResponse(
                success=False,
                action="deliver_order",
                message=f"Order {order_id} not found",
            )

        if order.status not in ["shipped", "confirmed"]:
            return CommandResponse(
                success=False,
                action="deliver_order",
                message=f"Order {order_id} cannot be marked as delivered. Current status: {order.status}",
            )

        from app.schemas.order import OrderUpdate
        data = OrderUpdate(status="delivered")
        updated = await self.order_service.update(order_id, data)

        return CommandResponse(
            success=True,
            action="deliver_order",
            message=f"Order #{order_id} has been delivered to {order.customer_name}",
            data={"id": order_id, "status": "delivered", "customer": order.customer_name},
        )

    async def _refund_order(self, params: Dict[str, Any]) -> CommandResponse:
        order_id = params.get("order_id")
        reason = params.get("reason", "Customer request")
        if not order_id:
            return CommandResponse(
                success=False,
                action="refund_order",
                message="Order ID is required",
            )

        order = await self.order_service.get_by_id(order_id)
        if not order:
            return CommandResponse(
                success=False,
                action="refund_order",
                message=f"Order {order_id} not found",
            )

        if order.status == "refunded":
            return CommandResponse(
                success=False,
                action="refund_order",
                message=f"Order {order_id} has already been refunded",
            )

        from app.schemas.order import OrderUpdate
        data = OrderUpdate(status="refunded")
        updated = await self.order_service.update(order_id, data)

        return CommandResponse(
            success=True,
            action="refund_order",
            message=f"Order #{order_id} has been refunded. Reason: {reason}",
            data={"id": order_id, "status": "refunded", "amount": order.total_amount, "reason": reason},
        )

    # Customer order handlers
    async def _place_order(self, params: Dict[str, Any]) -> CommandResponse:
        product_id = params.get("product_id")
        quantity = params.get("quantity", 1)

        if not product_id:
            return CommandResponse(
                success=False,
                action="place_order",
                message="Product ID is required to place an order",
            )

        product = await self.product_service.get_by_id(product_id)
        if not product:
            return CommandResponse(
                success=False,
                action="place_order",
                message=f"Product {product_id} not found",
            )

        if product.quantity < quantity:
            return CommandResponse(
                success=False,
                action="place_order",
                message=f"Not enough stock. Available: {product.quantity}, Requested: {quantity}",
            )

        # Create order
        order_data = OrderCreate(
            product_id=product_id,
            quantity=quantity,
            customer_name=params.get("customer_name", "Customer"),
            customer_email=params.get("customer_email"),
            shop_id=product.shop_id,
        )
        order = await self.order_service.create(order_data)

        return CommandResponse(
            success=True,
            action="place_order",
            message=f"Order placed successfully! Order #{order.id} for {quantity}x {product.name}",
            data={
                "id": order.id,
                "product": product.name,
                "quantity": quantity,
                "total": order.total_amount,
                "status": order.status
            },
        )

    async def _list_my_orders(self, params: Dict[str, Any]) -> CommandResponse:
        customer_id = params.get("customer_id")
        customer_email = params.get("customer_email")

        orders = await self.order_service.get_all()

        # Filter by customer if provided
        if customer_email:
            orders = [o for o in orders if o.customer_email == customer_email]

        return CommandResponse(
            success=True,
            action="list_my_orders",
            message=f"Found {len(orders)} orders",
            data=[{
                "id": o.id,
                "product": o.product_name,
                "quantity": o.quantity,
                "total": o.total_amount,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None
            } for o in orders],
        )

    # Shop form pre-fill handler (Super Admin)
    async def _prefill_shop_form(self, params: Dict[str, Any]) -> CommandResponse:
        """Return form data for frontend to pre-fill the shop registration form"""
        form_data = {
            "name": params.get("name", ""),
            "description": params.get("description", ""),
            "category_id": params.get("category_id", ""),
            "owner_name": params.get("owner_name", ""),
            "owner_email": params.get("owner_email", ""),
            "owner_phone": params.get("owner_phone", ""),
            "address": params.get("address", ""),
            "city": params.get("city", ""),
            "pincode": params.get("pincode", ""),
            "gst_number": params.get("gst_number", ""),
        }

        # Build a message showing what will be pre-filled
        filled_fields = [k for k, v in form_data.items() if v]
        message = "Opening shop registration form"
        if filled_fields:
            message += f" with: {', '.join(filled_fields)}"

        return CommandResponse(
            success=True,
            action="prefill_shop_form",
            message=message,
            data={
                "action_type": "prefill_form",
                "form_type": "shop_registration",
                "form_data": form_data
            },
        )

    # Shop handlers (Super Admin)
    async def _create_shop(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            data = ShopCreate(
                name=params["name"],
                description=params.get("description"),
                category_id=params.get("category_id"),
                owner_name=params.get("owner_name", ""),
                owner_email=params.get("owner_email", ""),
                owner_phone=params.get("owner_phone"),
                address=params.get("address"),
                city=params.get("city"),
                pincode=params.get("pincode"),
                gst_number=params.get("gst_number"),
            )
            shop = await self.shop_service.create(data)
            return CommandResponse(
                success=True,
                action="create_shop",
                message=f"Created shop '{shop.name}' with ID {shop.id}. Status: Pending verification.",
                data={"id": shop.id, "name": shop.name, "is_verified": shop.is_verified},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_shop",
                message=f"Missing required parameter: {e}",
            )

    async def _update_shop(self, params: Dict[str, Any]) -> CommandResponse:
        shop_id = params.get("shop_id")
        if not shop_id:
            return CommandResponse(
                success=False,
                action="update_shop",
                message="Shop ID is required",
            )
        update_data = {k: v for k, v in params.items() if k != "shop_id" and v is not None}
        data = ShopUpdate(**update_data)
        shop = await self.shop_service.update(shop_id, data)
        if not shop:
            return CommandResponse(
                success=False,
                action="update_shop",
                message=f"Shop {shop_id} not found",
            )
        return CommandResponse(
            success=True,
            action="update_shop",
            message=f"Updated shop '{shop.name}'",
            data={"id": shop.id, "name": shop.name},
        )

    async def _delete_shop(self, params: Dict[str, Any]) -> CommandResponse:
        shop_id = params.get("shop_id")
        if not shop_id:
            return CommandResponse(
                success=False,
                action="delete_shop",
                message="Shop ID is required",
            )
        success = await self.shop_service.delete(shop_id)
        if not success:
            return CommandResponse(
                success=False,
                action="delete_shop",
                message=f"Shop {shop_id} not found",
            )
        return CommandResponse(
            success=True,
            action="delete_shop",
            message=f"Deleted shop {shop_id}",
        )

    async def _list_shops(self, params: Dict[str, Any]) -> CommandResponse:
        category_id = params.get("category_id")
        city = params.get("city")
        search = params.get("search")
        is_verified = params.get("is_verified")
        is_active = params.get("is_active")

        shops = await self.shop_service.get_all(
            category_id=category_id,
            city=city,
            search=search,
            active_only=False
        )

        # Filter by verification status if specified
        if is_verified is not None:
            shops = [s for s in shops if s.is_verified == is_verified]
        if is_active is not None:
            shops = [s for s in shops if s.is_active == is_active]

        return CommandResponse(
            success=True,
            action="list_shops",
            message=f"Found {len(shops)} shops",
            data=[{
                "id": s.id,
                "name": s.name,
                "city": s.city,
                "is_verified": s.is_verified,
                "is_active": s.is_active,
                "rating": s.rating
            } for s in shops],
        )

    async def _get_shop(self, params: Dict[str, Any]) -> CommandResponse:
        shop = None
        if "shop_id" in params:
            shop = await self.shop_service.get_by_id(params["shop_id"])
        elif "name" in params:
            shop = await self.shop_service.get_by_name(params["name"])

        if not shop:
            return CommandResponse(
                success=False,
                action="get_shop",
                message="Shop not found",
            )
        return CommandResponse(
            success=True,
            action="get_shop",
            message=f"Found shop: {shop.name}",
            data={
                "id": shop.id,
                "name": shop.name,
                "description": shop.description,
                "city": shop.city,
                "is_verified": shop.is_verified,
                "is_active": shop.is_active,
                "rating": shop.rating,
                "total_orders": shop.total_orders,
                "total_revenue": shop.total_revenue
            },
        )

    async def _verify_shop(self, params: Dict[str, Any]) -> CommandResponse:
        shop = None
        if "shop_id" in params:
            shop = await self.shop_service.get_by_id(params["shop_id"])
        elif "name" in params:
            shop = await self.shop_service.get_by_name(params["name"])

        if not shop:
            return CommandResponse(
                success=False,
                action="verify_shop",
                message="Shop not found",
            )

        if shop.is_verified:
            return CommandResponse(
                success=False,
                action="verify_shop",
                message=f"Shop '{shop.name}' is already verified",
            )

        shop.is_verified = True
        await self.db.commit()
        await self.db.refresh(shop)

        return CommandResponse(
            success=True,
            action="verify_shop",
            message=f"Shop '{shop.name}' has been verified and approved",
            data={"id": shop.id, "name": shop.name, "is_verified": True},
        )

    async def _suspend_shop(self, params: Dict[str, Any]) -> CommandResponse:
        shop = None
        if "shop_id" in params:
            shop = await self.shop_service.get_by_id(params["shop_id"])
        elif "name" in params:
            shop = await self.shop_service.get_by_name(params["name"])

        if not shop:
            return CommandResponse(
                success=False,
                action="suspend_shop",
                message="Shop not found",
            )

        if not shop.is_active:
            return CommandResponse(
                success=False,
                action="suspend_shop",
                message=f"Shop '{shop.name}' is already suspended",
            )

        shop.is_active = False
        await self.db.commit()
        await self.db.refresh(shop)

        return CommandResponse(
            success=True,
            action="suspend_shop",
            message=f"Shop '{shop.name}' has been suspended",
            data={"id": shop.id, "name": shop.name, "is_active": False},
        )

    async def _activate_shop(self, params: Dict[str, Any]) -> CommandResponse:
        shop = None
        if "shop_id" in params:
            shop = await self.shop_service.get_by_id(params["shop_id"])
        elif "name" in params:
            shop = await self.shop_service.get_by_name(params["name"])

        if not shop:
            return CommandResponse(
                success=False,
                action="activate_shop",
                message="Shop not found",
            )

        if shop.is_active:
            return CommandResponse(
                success=False,
                action="activate_shop",
                message=f"Shop '{shop.name}' is already active",
            )

        shop.is_active = True
        await self.db.commit()
        await self.db.refresh(shop)

        return CommandResponse(
            success=True,
            action="activate_shop",
            message=f"Shop '{shop.name}' has been activated",
            data={"id": shop.id, "name": shop.name, "is_active": True},
        )

    async def _get_pending_shops(self, params: Dict[str, Any]) -> CommandResponse:
        shops = await self.shop_service.get_all(active_only=False)
        pending_shops = [s for s in shops if not s.is_verified]

        return CommandResponse(
            success=True,
            action="get_pending_shops",
            message=f"Found {len(pending_shops)} shops pending verification",
            data=[{
                "id": s.id,
                "name": s.name,
                "owner_name": s.owner_name,
                "owner_email": s.owner_email,
                "city": s.city,
                "created_at": s.created_at.isoformat() if s.created_at else None
            } for s in pending_shops],
        )

    # Shop Dashboard handlers (Shop Admin)
    async def _get_shop_dashboard(self, params: Dict[str, Any]) -> CommandResponse:
        shop_id = params.get("shop_id")
        if not shop_id:
            return CommandResponse(
                success=False,
                action="get_shop_dashboard",
                message="Shop ID is required",
            )

        shop = await self.shop_service.get_by_id(shop_id)
        if not shop:
            return CommandResponse(
                success=False,
                action="get_shop_dashboard",
                message=f"Shop {shop_id} not found",
            )

        stats = await self.shop_service.get_dashboard_stats(shop_id)
        return CommandResponse(
            success=True,
            action="get_shop_dashboard",
            message=f"Dashboard stats for '{shop.name}'",
            data=stats,
        )

    async def _get_shop_low_stock(self, params: Dict[str, Any]) -> CommandResponse:
        shop_id = params.get("shop_id")
        if not shop_id:
            return CommandResponse(
                success=False,
                action="get_shop_low_stock",
                message="Shop ID is required",
            )

        products = await self.product_service.get_low_stock(shop_id)
        return CommandResponse(
            success=True,
            action="get_shop_low_stock",
            message=f"Found {len(products)} low stock products",
            data=[{
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "quantity": p.quantity,
                "min_stock_level": p.min_stock_level
            } for p in products],
        )

    async def _get_shop_orders(self, params: Dict[str, Any]) -> CommandResponse:
        shop_id = params.get("shop_id")
        if not shop_id:
            return CommandResponse(
                success=False,
                action="get_shop_orders",
                message="Shop ID is required",
            )

        status = params.get("status")
        orders = await self.order_service.get_by_shop(shop_id, status)
        return CommandResponse(
            success=True,
            action="get_shop_orders",
            message=f"Found {len(orders)} orders",
            data=[{
                "id": o.id,
                "status": o.status,
                "total": o.total_amount,
                "customer": o.customer_name,
                "product_name": o.product_name,
                "created_at": o.created_at.isoformat() if o.created_at else None
            } for o in orders],
        )

    # User handlers (Super Admin)
    async def _create_user(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            # Check if email exists
            existing = await self.user_service.get_by_email(params["email"])
            if existing:
                return CommandResponse(
                    success=False,
                    action="create_user",
                    message=f"User with email {params['email']} already exists",
                )

            data = UserCreate(
                name=params["name"],
                email=params["email"],
                password=params["password"],
                role=params.get("role", "customer"),
                phone=params.get("phone"),
                shop_id=params.get("shop_id"),
            )
            user = await self.user_service.create(data)
            return CommandResponse(
                success=True,
                action="create_user",
                message=f"Created user '{user.name}' with role '{user.role}'",
                data={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_user",
                message=f"Missing required parameter: {e}",
            )

    async def _update_user(self, params: Dict[str, Any]) -> CommandResponse:
        user_id = params.get("user_id")
        if not user_id:
            return CommandResponse(
                success=False,
                action="update_user",
                message="User ID is required",
            )

        update_data = {k: v for k, v in params.items() if k != "user_id" and v is not None}
        data = UserUpdate(**update_data)
        user = await self.user_service.update(user_id, data)

        if not user:
            return CommandResponse(
                success=False,
                action="update_user",
                message=f"User {user_id} not found",
            )
        return CommandResponse(
            success=True,
            action="update_user",
            message=f"Updated user '{user.name}'",
            data={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        )

    async def _delete_user(self, params: Dict[str, Any]) -> CommandResponse:
        user_id = params.get("user_id")
        if not user_id:
            return CommandResponse(
                success=False,
                action="delete_user",
                message="User ID is required",
            )

        success = await self.user_service.delete(user_id)
        if not success:
            return CommandResponse(
                success=False,
                action="delete_user",
                message=f"User {user_id} not found",
            )
        return CommandResponse(
            success=True,
            action="delete_user",
            message=f"Deleted user {user_id}",
        )

    async def _list_users(self, params: Dict[str, Any]) -> CommandResponse:
        role = params.get("role")
        users = await self.user_service.get_all(role=role)
        return CommandResponse(
            success=True,
            action="list_users",
            message=f"Found {len(users)} users",
            data=[{
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active
            } for u in users],
        )

    async def _get_user(self, params: Dict[str, Any]) -> CommandResponse:
        user = None
        if "user_id" in params:
            user = await self.user_service.get_by_id(params["user_id"])
        elif "email" in params:
            user = await self.user_service.get_by_email(params["email"])

        if not user:
            return CommandResponse(
                success=False,
                action="get_user",
                message="User not found",
            )
        return CommandResponse(
            success=True,
            action="get_user",
            message=f"Found user: {user.name}",
            data={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "phone": user.phone,
                "is_active": user.is_active,
                "shop_id": user.shop_id
            },
        )

    # Platform handlers (Super Admin)
    async def _get_platform_stats(self, params: Dict[str, Any]) -> CommandResponse:
        stats = await self.user_service.get_platform_stats()
        return CommandResponse(
            success=True,
            action="get_platform_stats",
            message="Platform statistics retrieved",
            data=stats,
        )

    # Category handlers
    async def _list_shop_categories(self, params: Dict[str, Any]) -> CommandResponse:
        categories = await self.shop_category_service.get_with_shop_count()
        return CommandResponse(
            success=True,
            action="list_shop_categories",
            message=f"Found {len(categories)} shop categories",
            data=categories,
        )

    async def _list_product_categories(self, params: Dict[str, Any]) -> CommandResponse:
        categories = await self.category_service.get_with_product_count()
        return CommandResponse(
            success=True,
            action="list_product_categories",
            message=f"Found {len(categories)} product categories",
            data=categories,
        )

    async def _create_shop_category(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            from app.schemas.shop import ShopCategoryCreate
            data = ShopCategoryCreate(
                name=params["name"],
                description=params.get("description"),
                icon=params.get("icon"),
            )
            category = await self.shop_category_service.create(data)
            return CommandResponse(
                success=True,
                action="create_shop_category",
                message=f"Created shop category '{category.name}'",
                data={"id": category.id, "name": category.name},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_shop_category",
                message=f"Missing required parameter: {e}",
            )

    async def _create_product_category(self, params: Dict[str, Any]) -> CommandResponse:
        try:
            from app.schemas.product import CategoryCreate
            data = CategoryCreate(
                name=params["name"],
                description=params.get("description"),
            )
            category = await self.category_service.create(data)
            return CommandResponse(
                success=True,
                action="create_product_category",
                message=f"Created product category '{category.name}'",
                data={"id": category.id, "name": category.name},
            )
        except KeyError as e:
            return CommandResponse(
                success=False,
                action="create_product_category",
                message=f"Missing required parameter: {e}",
            )

    # Analytics handlers
    async def _get_analytics(self, params: Dict[str, Any]) -> CommandResponse:
        analytics_type = params.get("type", "dashboard")

        if analytics_type == "dashboard":
            data = await self.analytics_service.get_dashboard_stats()
        elif analytics_type == "revenue":
            days = params.get("days", 7)
            data = await self.analytics_service.get_revenue_by_day(days)
        elif analytics_type == "top_products":
            limit = params.get("limit", 5)
            data = await self.analytics_service.get_top_products(limit)
        elif analytics_type == "top_customers":
            limit = params.get("limit", 5)
            data = await self.analytics_service.get_top_customers(limit)
        else:
            return CommandResponse(
                success=False,
                action="get_analytics",
                message=f"Unknown analytics type: {analytics_type}",
            )

        return CommandResponse(
            success=True,
            action="get_analytics",
            message=f"Retrieved {analytics_type} analytics",
            data=data,
        )

    # Billing handlers (Shop Admin)
    async def _sell_at_price(self, params: Dict[str, Any]) -> CommandResponse:
        """Sell a product at a bargained price"""
        product_id = params.get("product_id")
        selling_price = params.get("price") or params.get("selling_price")
        quantity = params.get("quantity", 1)
        customer_name = params.get("customer_name", "Walk-in Customer")
        customer_phone = params.get("customer_phone")
        force = params.get("force", False)

        if not product_id:
            return CommandResponse(
                success=False,
                action="sell_at_price",
                message="Product ID is required",
            )
        if not selling_price:
            return CommandResponse(
                success=False,
                action="sell_at_price",
                message="Selling price is required",
            )

        result = self.billing_service.sell_at_price(
            product_id=product_id,
            selling_price=selling_price,
            quantity=quantity,
            customer_name=customer_name,
            customer_phone=customer_phone,
            force=force,
        )

        if not result["success"]:
            return CommandResponse(
                success=False,
                action="sell_at_price",
                message=result.get("error", "Failed to process sale"),
                requires_confirmation=result.get("requires_confirmation", False),
                data=result,
            )

        order = result["order"]
        profit_info = result["profit_info"]

        return CommandResponse(
            success=True,
            action="sell_at_price",
            message=f"Sale completed! Order #{order.id} - Sold at ₹{selling_price} (Profit: ₹{profit_info['profit']})",
            data={
                "order_id": order.id,
                "product": order.product_name,
                "quantity": quantity,
                "cost_price": profit_info["cost_price"],
                "listed_price": profit_info["listed_price"],
                "sold_at": profit_info["sold_at"],
                "profit": profit_info["profit"],
                "discount_given": profit_info["discount_given"],
            },
        )

    async def _generate_bill(self, params: Dict[str, Any]) -> CommandResponse:
        """Generate bill for an order - customer or admin view"""
        order_id = params.get("order_id")
        bill_type = params.get("bill_type", "customer")  # customer or admin

        if not order_id:
            return CommandResponse(
                success=False,
                action="generate_bill",
                message="Order ID is required",
            )

        if bill_type == "admin":
            result = self.billing_service.generate_admin_bill(order_id)
        else:
            result = self.billing_service.generate_customer_bill(order_id)

        if not result["success"]:
            return CommandResponse(
                success=False,
                action="generate_bill",
                message=result.get("error", "Failed to generate bill"),
            )

        bill = result["bill"]
        return CommandResponse(
            success=True,
            action="generate_bill",
            message=f"Generated {bill_type} bill for Order #{order_id}",
            data=bill,
        )

    async def _get_daily_profit(self, params: Dict[str, Any]) -> CommandResponse:
        """Get daily profit report for a shop"""
        shop_id = params.get("shop_id")
        date_str = params.get("date")  # Optional: YYYY-MM-DD format

        if not shop_id:
            return CommandResponse(
                success=False,
                action="get_daily_profit",
                message="Shop ID is required",
            )

        from datetime import datetime
        report_date = None
        if date_str:
            try:
                report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return CommandResponse(
                    success=False,
                    action="get_daily_profit",
                    message="Invalid date format. Use YYYY-MM-DD",
                )

        result = self.billing_service.get_daily_profit_report(shop_id, report_date)

        if not result["success"]:
            return CommandResponse(
                success=False,
                action="get_daily_profit",
                message=result.get("error", "Failed to get profit report"),
            )

        report = result["report"]
        return CommandResponse(
            success=True,
            action="get_daily_profit",
            message=f"Profit Report for {report['date']}: Revenue ₹{report['total_revenue']}, Profit ₹{report['total_profit']} ({report['avg_profit_margin']}% margin)",
            data=report,
        )

    async def _get_product_profit(self, params: Dict[str, Any]) -> CommandResponse:
        """Get profit report per product for a shop"""
        shop_id = params.get("shop_id")

        if not shop_id:
            return CommandResponse(
                success=False,
                action="get_product_profit",
                message="Shop ID is required",
            )

        result = self.billing_service.get_product_profit_report(shop_id)

        if not result["success"]:
            return CommandResponse(
                success=False,
                action="get_product_profit",
                message=result.get("error", "Failed to get product profit report"),
            )

        products = result["products"]
        total_profit = sum(p["total_profit"] for p in products)

        return CommandResponse(
            success=True,
            action="get_product_profit",
            message=f"Product Profit Report: {len(products)} products, Total Profit ₹{total_profit}",
            data={"products": products, "total_profit": total_profit},
        )

    async def _get_profit_summary(self, params: Dict[str, Any]) -> CommandResponse:
        """Get overall profit summary for shop dashboard"""
        shop_id = params.get("shop_id")

        if not shop_id:
            return CommandResponse(
                success=False,
                action="get_profit_summary",
                message="Shop ID is required",
            )

        result = self.billing_service.get_shop_profit_summary(shop_id)

        if not result["success"]:
            return CommandResponse(
                success=False,
                action="get_profit_summary",
                message=result.get("error", "Failed to get profit summary"),
            )

        summary = result["summary"]
        today = summary["today"]
        all_time = summary["all_time"]

        return CommandResponse(
            success=True,
            action="get_profit_summary",
            message=f"Today: ₹{today['profit']} profit ({today['orders']} orders) | All Time: ₹{all_time['profit']} profit",
            data=summary,
        )
