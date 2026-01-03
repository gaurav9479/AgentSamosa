from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List

from app.core.database import get_db
from app.core.websocket import manager
from app.schemas.command import CommandInput, CommandResponse, ParsedIntent, MultiStepPlan
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.services.intent_parser import IntentParser
from app.services.action_executor import ActionExecutor
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.models.action_log import ActionLog

router = APIRouter()

# Session context storage (in production, use Redis)
session_context: Dict[str, Any] = {}


# ============== AGENT COMMAND ENDPOINT ==============

@router.post("/command", response_model=CommandResponse)
async def execute_command(
    command: CommandInput,
    db: AsyncSession = Depends(get_db)
):
    """
    Main endpoint for natural language commands.
    Parses intent using Gemini and executes the appropriate action.
    """
    parser = IntentParser()
    executor = ActionExecutor(db)

    # Merge user context with session context
    context = {**session_context, **(command.context or {})}

    # Parse the intent
    intent = await parser.parse(command.text, context)

    # Log the action
    log = ActionLog(
        user_input=command.text,
        parsed_intent=intent.model_dump() if isinstance(intent, ParsedIntent) else {"steps": [s.model_dump() for s in intent.steps]},
    )
    db.add(log)

    # Execute based on intent type
    if isinstance(intent, MultiStepPlan):
        results = await executor.execute_plan(intent)
        log.action_taken = "multi_step_plan"
        log.status = "completed" if all(r.success for r in results) else "partial"
        log.result = [r.model_dump() for r in results]
        await db.commit()

        # Broadcast all results
        for result in results:
            await manager.broadcast_action(
                result.action, result.success, result.data, result.message
            )

        # Return last result
        return results[-1] if results else CommandResponse(
            success=False, action="error", message="No actions executed"
        )
    else:
        result = await executor.execute(intent)
        log.action_taken = intent.action
        log.status = "completed" if result.success else "failed"
        log.result = result.model_dump()
        await db.commit()

        # Update session context
        if result.success and result.data:
            if "id" in result.data:
                session_context["last_entity_id"] = result.data["id"]
                session_context["last_entity_type"] = intent.entity

        # Broadcast result
        await manager.broadcast_action(
            result.action, result.success, result.data, result.message
        )

        return result


@router.post("/command/confirm/{confirmation_id}", response_model=CommandResponse)
async def confirm_command(
    confirmation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Confirm a pending destructive action."""
    executor = ActionExecutor(db)
    result = await executor.confirm_action(confirmation_id)

    await manager.broadcast_action(
        result.action, result.success, result.data, result.message
    )

    return result


# ============== PRODUCT ENDPOINTS ==============

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    return await service.get_all(skip, limit)


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    product = await service.create(data)
    await manager.broadcast_update("product", "created", {
        "id": product.id, "name": product.name, "price": product.price
    })
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    product = await service.update(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await manager.broadcast_update("product", "updated", {
        "id": product.id, "name": product.name, "price": product.price
    })
    return product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    success = await service.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    await manager.broadcast_update("product", "deleted", {"id": product_id})
    return {"message": "Product deleted"}


# ============== ORDER ENDPOINTS ==============

@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    service = OrderService(db)
    return await service.get_all(status, skip, limit)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = OrderService(db)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    service = OrderService(db)
    order = await service.create(data)
    if not order:
        raise HTTPException(status_code=400, detail="Failed to create order")
    await manager.broadcast_update("order", "created", {
        "id": order.id, "status": order.status, "total": order.total_amount
    })
    return order


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = OrderService(db)
    order = await service.update(order_id, data)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await manager.broadcast_update("order", "updated", {
        "id": order.id, "status": order.status, "total": order.total_amount
    })
    return order


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = OrderService(db)
    order = await service.cancel(order_id)
    if not order:
        raise HTTPException(status_code=400, detail="Cannot cancel order")
    await manager.broadcast_update("order", "cancelled", {
        "id": order.id, "status": order.status
    })
    return order


# ============== WEBSOCKET ENDPOINT ==============

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat/ping
            await manager.send_personal_message({"type": "pong", "data": data}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============== HEALTH CHECK ==============

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AgentSamosa"}
