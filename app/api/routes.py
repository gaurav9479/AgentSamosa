from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List

from app.core.database import get_db
from app.core.websocket import manager
from app.schemas.command import CommandInput, CommandResponse, ParsedIntent, MultiStepPlan
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.shop import (
    ShopCreate, ShopUpdate, ShopResponse,
    ShopCategoryCreate, ShopCategoryUpdate, ShopCategoryResponse
)
from app.services.intent_parser import IntentParser
from app.services.action_executor import ActionExecutor
from app.services.product_service import ProductService, CategoryService
from app.services.order_service import OrderService
from app.services.customer_service import CustomerService
from app.services.analytics_service import AnalyticsService
from app.services.shop_service import ShopService, ShopCategoryService
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, LoginResponse, ShopOwnerRegister,
    ForgotPasswordRequest, ForgotPasswordResponse, VerifyResetTokenRequest,
    VerifyResetTokenResponse, ResetPasswordRequest, ResetPasswordResponse
)
from app.models.action_log import ActionLog
from app.models.customer import Customer
from app.models.product import Category
from app.models.user import UserRole
from app.services.command_suggestions import CommandSuggestionService

router = APIRouter()
command_suggestion_service = CommandSuggestionService()

# Session context storage (in production, use Redis)
session_context: Dict[str, Any] = {}


# ============== AGENT COMMAND ENDPOINT ==============

@router.post("/command", response_model=CommandResponse)
async def execute_command(
    command: CommandInput,
    db: AsyncSession = Depends(get_db)
):
    """Main endpoint for natural language commands."""
    parser = IntentParser()
    executor = ActionExecutor(db)
    context = {**session_context, **(command.context or {})}
    intent = await parser.parse(command.text, context)

    log = ActionLog(
        user_input=command.text,
        parsed_intent=intent.model_dump() if isinstance(intent, ParsedIntent) else {"steps": [s.model_dump() for s in intent.steps]},
    )
    db.add(log)

    if isinstance(intent, MultiStepPlan):
        results = await executor.execute_plan(intent)
        log.action_taken = "multi_step_plan"
        log.status = "completed" if all(r.success for r in results) else "partial"
        log.result = [r.model_dump() for r in results]
        await db.commit()
        for result in results:
            await manager.broadcast_action(result.action, result.success, result.data, result.message)
        return results[-1] if results else CommandResponse(success=False, action="error", message="No actions executed")
    else:
        result = await executor.execute(intent)
        log.action_taken = intent.action
        log.status = "completed" if result.success else "failed"
        log.result = result.model_dump()
        await db.commit()
        if result.success and result.data and "id" in result.data:
            session_context["last_entity_id"] = result.data["id"]
            session_context["last_entity_type"] = intent.entity
        await manager.broadcast_action(result.action, result.success, result.data, result.message)
        return result


@router.post("/command/confirm/{confirmation_id}", response_model=CommandResponse)
async def confirm_command(confirmation_id: str, db: AsyncSession = Depends(get_db)):
    executor = ActionExecutor(db)
    result = await executor.confirm_action(confirmation_id)
    await manager.broadcast_action(result.action, result.success, result.data, result.message)
    return result


# ============== COMMAND SUGGESTIONS ==============

@router.get("/command/suggestions")
async def get_command_suggestions(
    query: str = "",
    role: str = "customer",
    limit: int = 5
):
    """Get command suggestions based on partial query and user role"""
    suggestions = command_suggestion_service.get_suggestions(query, role, limit)
    return {"suggestions": suggestions}


@router.get("/command/all")
async def get_all_commands(role: str = "customer"):
    """Get all available commands grouped by category for a role"""
    commands = command_suggestion_service.get_all_commands(role)
    return {"commands": commands}


@router.get("/command/quick-actions")
async def get_quick_actions(role: str = "customer"):
    """Get quick action buttons for a role"""
    actions = command_suggestion_service.get_quick_actions(role)
    return {"quick_actions": actions}


@router.get("/command/help/{command}")
async def get_command_help(command: str):
    """Get detailed help for a specific command"""
    help_info = command_suggestion_service.get_command_help(command)
    if not help_info:
        raise HTTPException(status_code=404, detail="Command not found")
    return help_info


# ============== CATEGORY ENDPOINTS ==============

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    return await service.get_all()


@router.get("/categories/with-counts")
async def list_categories_with_counts(db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    return await service.get_with_product_count()


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/categories", response_model=CategoryResponse)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    category = await service.create(data)
    await manager.broadcast_update("category", "created", {"id": category.id, "name": category.name})
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, data: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    category = await service.update(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await manager.broadcast_update("category", "updated", {"id": category.id, "name": category.name})
    return category


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    success = await service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    await manager.broadcast_update("category", "deleted", {"id": category_id})
    return {"message": "Category deleted"}


# ============== SHOP CATEGORY ENDPOINTS ==============

@router.get("/shop-categories", response_model=List[ShopCategoryResponse])
async def list_shop_categories(db: AsyncSession = Depends(get_db)):
    """List all shop categories (Beauty, Grocery, Clothing, etc.)"""
    service = ShopCategoryService(db)
    return await service.get_all()


@router.get("/shop-categories/with-counts")
async def list_shop_categories_with_counts(db: AsyncSession = Depends(get_db)):
    """List shop categories with shop counts"""
    service = ShopCategoryService(db)
    return await service.get_with_shop_count()


@router.get("/shop-categories/{category_id}", response_model=ShopCategoryResponse)
async def get_shop_category(category_id: int, db: AsyncSession = Depends(get_db)):
    service = ShopCategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Shop category not found")
    return category


@router.post("/shop-categories", response_model=ShopCategoryResponse)
async def create_shop_category(data: ShopCategoryCreate, db: AsyncSession = Depends(get_db)):
    service = ShopCategoryService(db)
    category = await service.create(data)
    return category


@router.put("/shop-categories/{category_id}", response_model=ShopCategoryResponse)
async def update_shop_category(category_id: int, data: ShopCategoryUpdate, db: AsyncSession = Depends(get_db)):
    service = ShopCategoryService(db)
    category = await service.update(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Shop category not found")
    return category


@router.delete("/shop-categories/{category_id}")
async def delete_shop_category(category_id: int, db: AsyncSession = Depends(get_db)):
    service = ShopCategoryService(db)
    success = await service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shop category not found")
    return {"message": "Shop category deleted"}


# ============== SHOP ENDPOINTS ==============

@router.get("/shops", response_model=List[ShopResponse])
async def list_shops(
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all shops, optionally filtered by category, city, or search"""
    service = ShopService(db)
    return await service.get_all(skip, limit, category_id, city, search)


@router.get("/shops/by-category/{category_id}")
async def get_shops_by_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Get all shops in a specific category"""
    service = ShopService(db)
    return await service.get_by_category(category_id)


@router.get("/shops/{shop_id}", response_model=ShopResponse)
async def get_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    service = ShopService(db)
    shop = await service.get_by_id(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/shops/{shop_id}/dashboard")
async def get_shop_dashboard(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Get dashboard stats for a shop owner"""
    service = ShopService(db)
    shop = await service.get_by_id(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return await service.get_dashboard_stats(shop_id)


@router.get("/shops/{shop_id}/products", response_model=List[ProductResponse])
async def get_shop_products(
    shop_id: int,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all products for a specific shop"""
    product_service = ProductService(db)
    return await product_service.get_all(
        skip, limit, shop_id, category_id, search,
        not include_inactive, include_inactive
    )


@router.get("/shops/{shop_id}/low-stock")
async def get_shop_low_stock(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Get low stock products for a specific shop"""
    product_service = ProductService(db)
    products = await product_service.get_low_stock(shop_id)
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "quantity": p.quantity,
            "min_stock_level": p.min_stock_level
        }
        for p in products
    ]


@router.get("/shops/{shop_id}/orders")
async def get_shop_orders(
    shop_id: int,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all orders for a specific shop"""
    order_service = OrderService(db)
    return await order_service.get_by_shop(shop_id, status, skip, limit)


@router.post("/shops", response_model=ShopResponse)
async def create_shop(data: ShopCreate, db: AsyncSession = Depends(get_db)):
    service = ShopService(db)
    shop = await service.create(data)
    return shop


@router.put("/shops/{shop_id}", response_model=ShopResponse)
async def update_shop(shop_id: int, data: ShopUpdate, db: AsyncSession = Depends(get_db)):
    service = ShopService(db)
    shop = await service.update(shop_id, data)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.delete("/shops/{shop_id}")
async def delete_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    service = ShopService(db)
    success = await service.delete(shop_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"message": "Shop deleted"}


# ============== PRODUCT ENDPOINTS ==============

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    return await service.get_all(skip, limit, category_id, search, not include_inactive, include_inactive)


@router.get("/products/featured")
async def get_featured_products(limit: int = 10, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_featured(limit)


@router.get("/products/low-stock")
async def get_low_stock_products(db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    products = await service.get_low_stock()
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "quantity": p.quantity,
            "min_stock_level": p.min_stock_level,
            "category_id": p.category_id
        }
        for p in products
    ]


@router.get("/products/search/{query}")
async def search_products(query: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.search(query, limit)


@router.get("/products/inventory-stats")
async def get_inventory_stats(db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_inventory_stats()


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Increment view count
    await service.increment_view(product_id)
    return product


@router.post("/products", response_model=ProductResponse)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    # Check for duplicate SKU
    if data.sku:
        existing = await service.get_by_sku(data.sku)
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    product = await service.create(data)
    await manager.broadcast_update("product", "created", {
        "id": product.id, "name": product.name, "price": product.price
    })
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.update(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await manager.broadcast_update("product", "updated", {
        "id": product.id, "name": product.name, "price": product.price
    })
    return product


@router.patch("/products/{product_id}/stock")
async def update_product_stock(
    product_id: int,
    quantity: int,
    adjustment_type: str = "set",
    db: AsyncSession = Depends(get_db)
):
    """Update product stock. adjustment_type: 'set', 'add', 'subtract'"""
    service = ProductService(db)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if adjustment_type == "set":
        product.quantity = quantity
    elif adjustment_type == "add":
        product.quantity += quantity
    elif adjustment_type == "subtract":
        product.quantity = max(0, product.quantity - quantity)

    await db.commit()
    await db.refresh(product)
    await manager.broadcast_update("product", "stock_updated", {
        "id": product.id, "name": product.name, "quantity": product.quantity
    })
    return {"id": product.id, "quantity": product.quantity}


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
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
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders", response_model=OrderResponse)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    order = await service.create(data)
    if not order:
        raise HTTPException(status_code=400, detail="Failed to create order")

    # Update product stock
    product_service = ProductService(db)
    await product_service.update_stock(data.product_id, -data.quantity, sold=True)

    await manager.broadcast_update("order", "created", {
        "id": order.id, "status": order.status, "total": order.total_amount
    })
    return order


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, data: OrderUpdate, db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    order = await service.update(order_id, data)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await manager.broadcast_update("order", "updated", {
        "id": order.id, "status": order.status, "total": order.total_amount
    })
    return order


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    order = await service.cancel(order_id)
    if not order:
        raise HTTPException(status_code=400, detail="Cannot cancel order")
    await manager.broadcast_update("order", "cancelled", {"id": order.id, "status": order.status})
    return order


# ============== CUSTOMER ENDPOINTS ==============

@router.get("/customers", response_model=List[CustomerResponse])
async def list_customers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = CustomerService(db)
    return await service.get_all(skip, limit)


@router.get("/customers/search/{query}")
async def search_customers(query: str, db: AsyncSession = Depends(get_db)):
    service = CustomerService(db)
    return await service.search(query)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    service = CustomerService(db)
    customer = await service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/customers", response_model=CustomerResponse)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    service = CustomerService(db)
    existing = await service.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this email already exists")
    customer = await service.create(data)
    await manager.broadcast_update("customer", "created", {
        "id": customer.id, "name": customer.name, "email": customer.email
    })
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    service = CustomerService(db)
    customer = await service.update(customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await manager.broadcast_update("customer", "updated", {
        "id": customer.id, "name": customer.name, "email": customer.email
    })
    return customer


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    service = CustomerService(db)
    success = await service.delete(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    await manager.broadcast_update("customer", "deleted", {"id": customer_id})
    return {"message": "Customer deleted"}


# ============== ANALYTICS ENDPOINTS ==============

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_dashboard_stats()


@router.get("/analytics/revenue")
async def get_revenue_analytics(days: int = 7, db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_revenue_by_day(days)


@router.get("/analytics/order-status")
async def get_order_status_distribution(db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_order_status_distribution()


@router.get("/analytics/top-products")
async def get_top_products(limit: int = 5, db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_top_products(limit)


@router.get("/analytics/top-customers")
async def get_top_customers(limit: int = 5, db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_top_customers(limit)


@router.get("/analytics/recent-orders")
async def get_recent_orders(limit: int = 10, db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_recent_orders(limit)


@router.get("/analytics/monthly-comparison")
async def get_monthly_comparison(db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_monthly_comparison()


# ============== SHOP STOREFRONT ENDPOINTS ==============

@router.get("/shop/products")
async def shop_list_products(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Public endpoint for customer-facing product listing"""
    service = ProductService(db)
    products = await service.get_all(skip, limit, category_id, search, active_only=True)
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "brand": p.brand,
            "price": p.price,
            "compare_at_price": p.compare_at_price,
            "image_url": p.image_url,
            "category_id": p.category_id,
            "in_stock": p.quantity > 0,
            "unit": p.unit
        }
        for p in products
    ]


@router.get("/shop/categories")
async def shop_list_categories(db: AsyncSession = Depends(get_db)):
    """Public endpoint for customer-facing category listing"""
    service = CategoryService(db)
    return await service.get_with_product_count()


@router.get("/shop/product/{product_id}")
async def shop_get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Public endpoint for customer-facing product details"""
    service = ProductService(db)
    product = await service.get_by_id(product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    await service.increment_view(product_id)

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "brand": product.brand,
        "price": product.price,
        "compare_at_price": product.compare_at_price,
        "image_url": product.image_url,
        "images": product.images,
        "category_id": product.category_id,
        "in_stock": product.quantity > 0,
        "unit": product.unit,
        "tags": product.tags
    }


# ============== WEBSOCKET ENDPOINT ==============

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message({"type": "pong", "data": data}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============== AUTH ENDPOINTS ==============

@router.post("/auth/login", response_model=LoginResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return user data"""
    service = UserService(db)
    user = await service.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return LoginResponse(user=user)


@router.post("/auth/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new customer account"""
    service = UserService(db)
    existing = await service.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Force customer role for public registration
    data.role = UserRole.CUSTOMER.value
    user = await service.create(data)
    return user


@router.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset token"""
    service = UserService(db)
    token = await service.generate_reset_token(data.email)

    if not token:
        # Don't reveal if email exists or not for security
        return ForgotPasswordResponse(
            message="If an account with this email exists, a reset link has been sent.",
            reset_token=None
        )

    # In production, send email with reset link
    # For demo purposes, we return the token directly
    return ForgotPasswordResponse(
        message="Password reset link generated. In production, this would be sent via email.",
        reset_token=token  # Remove this in production!
    )


@router.post("/auth/verify-reset-token", response_model=VerifyResetTokenResponse)
async def verify_reset_token(data: VerifyResetTokenRequest, db: AsyncSession = Depends(get_db)):
    """Verify if a reset token is valid"""
    service = UserService(db)
    user = await service.verify_reset_token(data.token)

    if not user:
        return VerifyResetTokenResponse(valid=False, email=None)

    # Mask email for privacy
    email = user.email
    masked_email = email[0:2] + "***" + email[email.index("@"):]

    return VerifyResetTokenResponse(valid=True, email=masked_email)


@router.post("/auth/reset-password", response_model=ResetPasswordResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using a valid token"""
    service = UserService(db)
    success = await service.reset_password(data.token, data.new_password)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    return ResetPasswordResponse(
        success=True,
        message="Password has been reset successfully. You can now login with your new password."
    )


# ============== USER MANAGEMENT (Super Admin only) ==============

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all users (Super Admin only)"""
    service = UserService(db)
    return await service.get_all(role, skip, limit)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user (Super Admin only)"""
    service = UserService(db)
    existing = await service.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await service.create(data)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.update(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    success = await service.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


# ============== PLATFORM STATS (Super Admin) ==============

@router.get("/platform/stats")
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    """Get platform-wide statistics for super admin"""
    service = UserService(db)
    return await service.get_platform_stats()


@router.get("/platform/shops")
async def get_all_platform_shops(
    is_verified: Optional[bool] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all shops with filters for super admin"""
    service = ShopService(db)
    shops = await service.get_all(skip, limit)
    # Filter based on parameters
    if is_verified is not None:
        shops = [s for s in shops if s.is_verified == is_verified]
    if is_active is not None:
        shops = [s for s in shops if s.is_active == is_active]
    return shops


@router.patch("/platform/shops/{shop_id}/verify")
async def verify_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Verify a shop (Super Admin only)"""
    service = ShopService(db)
    shop = await service.get_by_id(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.is_verified = True
    await db.commit()
    await db.refresh(shop)
    return {"message": f"Shop '{shop.name}' has been verified", "shop_id": shop_id}


@router.patch("/platform/shops/{shop_id}/suspend")
async def suspend_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Suspend a shop (Super Admin only)"""
    service = ShopService(db)
    shop = await service.get_by_id(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.is_active = False
    await db.commit()
    await db.refresh(shop)
    return {"message": f"Shop '{shop.name}' has been suspended", "shop_id": shop_id}


@router.patch("/platform/shops/{shop_id}/activate")
async def activate_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Activate a suspended shop (Super Admin only)"""
    service = ShopService(db)
    shop = await service.get_by_id(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.is_active = True
    await db.commit()
    await db.refresh(shop)
    return {"message": f"Shop '{shop.name}' has been activated", "shop_id": shop_id}


# ============== HEALTH CHECK ==============

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KommandAI"}
