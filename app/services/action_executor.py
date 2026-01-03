import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.command import ParsedIntent, CommandResponse, MultiStepPlan
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.product_service import ProductService
from app.services.order_service import OrderService


class ActionExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
        self.order_service = OrderService(db)
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
            # Order actions
            "create_order": self._create_order,
            "update_order": self._update_order,
            "cancel_order": self._cancel_order,
            "list_orders": self._list_orders,
            "get_order": self._get_order,
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
