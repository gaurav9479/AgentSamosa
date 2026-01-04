"""
Command Suggestions Service
Provides autocomplete and command templates for the AI command panel
Properly organized by role with appropriate actions
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CommandTemplate:
    command: str
    description: str
    template: str
    examples: List[str]
    category: str
    roles: List[str]  # super_admin, admin, customer
    action_type: str = "execute"  # execute, prefill_form


# ============== SUPER ADMIN COMMANDS ==============
# Focus: Platform management, shop verification, categories, user management
# NO product creation (too complex, delegate to shop admin)

SUPER_ADMIN_COMMANDS: List[CommandTemplate] = [
    # Shop Management
    CommandTemplate(
        command="prefill_shop_form",
        description="Fill shop registration form with details",
        template='add shop "{name}" owner "{owner}" email {email} city "{city}"',
        examples=[
            'add shop "Tech Hub" owner "John Doe" email john@test.com city "Mumbai"',
            'register shop "Beauty Palace" owner "Jane Smith" email jane@shop.com',
            'create shop "Fresh Mart" in category 3 owner "Bob"',
        ],
        category="Shop Registration",
        roles=["super_admin"],
        action_type="prefill_form"
    ),
    CommandTemplate(
        command="verify_shop",
        description="Verify/approve a pending shop",
        template="verify shop {id}",
        examples=[
            "verify shop 5",
            "approve shop 12",
            'approve shop "Tech Store"',
            "verify pending shop 8",
        ],
        category="Shop Management",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="suspend_shop",
        description="Suspend an active shop",
        template="suspend shop {id}",
        examples=[
            "suspend shop 5",
            'suspend shop "Bad Store"',
        ],
        category="Shop Management",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="activate_shop",
        description="Activate a suspended shop",
        template="activate shop {id}",
        examples=[
            "activate shop 5",
            "reactivate shop 12",
        ],
        category="Shop Management",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="get_pending_shops",
        description="View shops pending verification",
        template="show pending shops",
        examples=[
            "show pending shops",
            "list shops waiting for approval",
            "pending verifications",
        ],
        category="Shop Management",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="list_shops",
        description="List all shops",
        template="list shops",
        examples=[
            "list shops",
            "show all shops",
            "list shops in Mumbai",
            "show verified shops",
        ],
        category="Shop Management",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="get_shop",
        description="View shop details and stats",
        template="show shop {id}",
        examples=[
            "show shop 5",
            'get shop "Tech Hub" stats',
            "view shop 12 details",
        ],
        category="Shop Management",
        roles=["super_admin"]
    ),

    # Platform Stats
    CommandTemplate(
        command="get_platform_stats",
        description="View platform statistics",
        template="show platform stats",
        examples=[
            "show platform stats",
            "platform overview",
            "show dashboard",
        ],
        category="Platform",
        roles=["super_admin"]
    ),

    # User Management
    CommandTemplate(
        command="list_users",
        description="List all users",
        template="list users",
        examples=[
            "list users",
            "show all users",
            "list admin users",
            "show customers",
        ],
        category="User Management",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="get_user",
        description="View user details",
        template="show user {id}",
        examples=[
            "show user 5",
            'get user "john@test.com"',
        ],
        category="User Management",
        roles=["super_admin"]
    ),

    # Category Management
    CommandTemplate(
        command="list_shop_categories",
        description="List shop categories",
        template="list shop categories",
        examples=[
            "list shop categories",
            "show business types",
        ],
        category="Categories",
        roles=["super_admin"]
    ),
    CommandTemplate(
        command="create_shop_category",
        description="Create a new shop category",
        template='create category "{name}"',
        examples=[
            'create category "Electronics"',
            'add shop category "Pharmacy" description "Medical stores"',
        ],
        category="Categories",
        roles=["super_admin"]
    ),
]


# ============== SHOP ADMIN COMMANDS ==============
# Focus: Product management, order management, inventory, shop dashboard

SHOP_ADMIN_COMMANDS: List[CommandTemplate] = [
    # Dashboard
    CommandTemplate(
        command="get_shop_dashboard",
        description="View your shop dashboard",
        template="show dashboard",
        examples=[
            "show dashboard",
            "my shop stats",
            "shop overview",
        ],
        category="Dashboard",
        roles=["admin"]
    ),

    # Product Management
    CommandTemplate(
        command="create_product",
        description="Create a new product with cost and selling price",
        template='create product "{name}" cost {cost} price {price} quantity {qty}',
        examples=[
            'create product "iPhone 15" cost 700 price 999 quantity 50',
            'add product "Shampoo" cost 70 price 150 min 90 quantity 100',
            'new product "T-Shirt" cost 200 price 499 quantity 50',
        ],
        category="Products",
        roles=["admin"]
    ),
    CommandTemplate(
        command="update_product",
        description="Update product details",
        template="update product {id} {field} {value}",
        examples=[
            "update product 5 price 89.99",
            "update product 12 quantity 100",
            "change product 8 name 'Premium Widget'",
        ],
        category="Products",
        roles=["admin"]
    ),
    CommandTemplate(
        command="restock_product",
        description="Add stock to a product",
        template="restock product {id} add {qty}",
        examples=[
            "restock product 5 add 100",
            "add 50 units to product 12",
            "increase stock of product 8 by 200",
        ],
        category="Products",
        roles=["admin"]
    ),
    CommandTemplate(
        command="set_product_price",
        description="Update product price",
        template="set price of product {id} to {price}",
        examples=[
            "set price of product 5 to 49.99",
            "change price of product 12 to 29.99",
        ],
        category="Products",
        roles=["admin"]
    ),
    CommandTemplate(
        command="list_products",
        description="List all products",
        template="list products",
        examples=[
            "list products",
            "show all products",
            "list products in category 3",
        ],
        category="Products",
        roles=["admin"]
    ),
    CommandTemplate(
        command="get_low_stock",
        description="View low stock products",
        template="show low stock",
        examples=[
            "show low stock products",
            "what needs restocking",
            "low inventory",
        ],
        category="Products",
        roles=["admin"]
    ),
    CommandTemplate(
        command="delete_product",
        description="Delete a product",
        template="delete product {id}",
        examples=[
            "delete product 5",
            "remove product 12",
        ],
        category="Products",
        roles=["admin"]
    ),

    # Order Management
    CommandTemplate(
        command="list_orders",
        description="List all orders",
        template="list orders",
        examples=[
            "list orders",
            "show all orders",
            "list pending orders",
            "show today's orders",
        ],
        category="Orders",
        roles=["admin"]
    ),
    CommandTemplate(
        command="get_order",
        description="View order details",
        template="show order {id}",
        examples=[
            "show order 123",
            "order details 456",
        ],
        category="Orders",
        roles=["admin"]
    ),
    CommandTemplate(
        command="confirm_order",
        description="Confirm a pending order",
        template="confirm order {id}",
        examples=[
            "confirm order 123",
            "approve order 456",
        ],
        category="Orders",
        roles=["admin"]
    ),
    CommandTemplate(
        command="ship_order",
        description="Mark order as shipped",
        template="ship order {id}",
        examples=[
            "ship order 123",
            "mark order 456 as shipped",
            'ship order 789 tracking "TRK123"',
        ],
        category="Orders",
        roles=["admin"]
    ),
    CommandTemplate(
        command="deliver_order",
        description="Mark order as delivered",
        template="deliver order {id}",
        examples=[
            "deliver order 123",
            "mark order 456 as delivered",
            "complete order 789",
        ],
        category="Orders",
        roles=["admin"]
    ),
    CommandTemplate(
        command="cancel_order",
        description="Cancel an order",
        template="cancel order {id}",
        examples=[
            "cancel order 123",
        ],
        category="Orders",
        roles=["admin"]
    ),

    # Customer Management
    CommandTemplate(
        command="list_customers",
        description="List all customers",
        template="list customers",
        examples=[
            "list customers",
            "show all customers",
        ],
        category="Customers",
        roles=["admin"]
    ),
    CommandTemplate(
        command="search_customers",
        description="Search customers",
        template='search customers "{query}"',
        examples=[
            'search customers "john"',
            'find customer "jane@test.com"',
        ],
        category="Customers",
        roles=["admin"]
    ),

    # Billing & Sales
    CommandTemplate(
        command="sell_at_price",
        description="Sell product at bargained price",
        template="sell product {id} at {price}",
        examples=[
            "sell product 5 at 100",
            "sell product 12 at 80 to customer Ram",
            "sold product 8 at 150 quantity 2",
        ],
        category="Billing",
        roles=["admin"]
    ),
    CommandTemplate(
        command="generate_bill",
        description="Generate bill for an order",
        template="generate bill for order {id}",
        examples=[
            "generate bill for order 123",
            "print bill for order 456",
            "make admin bill for order 789",
        ],
        category="Billing",
        roles=["admin"]
    ),
    CommandTemplate(
        command="get_daily_profit",
        description="View daily profit report",
        template="show today's profit",
        examples=[
            "show today's profit",
            "daily profit report",
            "profit for 2025-01-03",
        ],
        category="Billing",
        roles=["admin"]
    ),
    CommandTemplate(
        command="get_product_profit",
        description="View profit by product",
        template="show product profit",
        examples=[
            "show product profit",
            "profit by product",
            "which products are most profitable",
        ],
        category="Billing",
        roles=["admin"]
    ),
    CommandTemplate(
        command="get_profit_summary",
        description="View overall profit summary",
        template="show profit summary",
        examples=[
            "show profit summary",
            "my profit",
            "today's earnings",
        ],
        category="Billing",
        roles=["admin"]
    ),
]


# ============== CUSTOMER COMMANDS ==============
# Focus: Browsing, searching, placing orders, managing their orders

CUSTOMER_COMMANDS: List[CommandTemplate] = [
    # Browsing
    CommandTemplate(
        command="list_shop_categories",
        description="Browse shop categories",
        template="browse categories",
        examples=[
            "browse categories",
            "show shop categories",
            "what can I shop for",
        ],
        category="Browse",
        roles=["customer"]
    ),
    CommandTemplate(
        command="list_shops",
        description="Browse shops",
        template="browse shops",
        examples=[
            "browse shops",
            "show shops in Beauty",
            "find shops in Mumbai",
        ],
        category="Browse",
        roles=["customer"]
    ),
    CommandTemplate(
        command="search_products",
        description="Search for products",
        template='search "{query}"',
        examples=[
            'search "phone"',
            'find "organic shampoo"',
            'search for "laptop"',
        ],
        category="Browse",
        roles=["customer"]
    ),

    # Order Management
    CommandTemplate(
        command="place_order",
        description="Place a new order",
        template="order product {id} quantity {qty}",
        examples=[
            "order product 5 quantity 2",
            "buy 3 of product 12",
            "place order for product 8",
        ],
        category="My Orders",
        roles=["customer"]
    ),
    CommandTemplate(
        command="list_my_orders",
        description="View my orders",
        template="show my orders",
        examples=[
            "show my orders",
            "my order history",
            "list my orders",
        ],
        category="My Orders",
        roles=["customer"]
    ),
    CommandTemplate(
        command="get_order",
        description="Track an order",
        template="track order {id}",
        examples=[
            "track order 123",
            "where is my order 456",
            "order status 789",
        ],
        category="My Orders",
        roles=["customer"]
    ),
    CommandTemplate(
        command="update_order",
        description="Update order quantity",
        template="update order {id} quantity {qty}",
        examples=[
            "update order 123 quantity 5",
            "change order 456 to 3 items",
        ],
        category="My Orders",
        roles=["customer"]
    ),
    CommandTemplate(
        command="cancel_order",
        description="Cancel an order",
        template="cancel order {id}",
        examples=[
            "cancel order 123",
            "cancel my order 456",
        ],
        category="My Orders",
        roles=["customer"]
    ),
]


# Combine all templates
COMMAND_TEMPLATES: List[CommandTemplate] = (
    SUPER_ADMIN_COMMANDS + SHOP_ADMIN_COMMANDS + CUSTOMER_COMMANDS
)


class CommandSuggestionService:
    """Service for providing command suggestions and autocomplete"""

    def __init__(self):
        self.templates = COMMAND_TEMPLATES

    def get_suggestions(
        self,
        query: str,
        role: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get command suggestions based on partial query and user role"""
        query = query.lower().strip()
        suggestions = []

        # Filter by role
        role_templates = [t for t in self.templates if role in t.roles]

        if not query:
            return self._get_popular_commands(role, limit)

        for template in role_templates:
            score = 0

            if query in template.command.lower():
                score += 3
            if query in template.description.lower():
                score += 2
            for example in template.examples:
                if query in example.lower():
                    score += 1
                    break
            if query in template.category.lower():
                score += 1

            if score > 0:
                suggestions.append({
                    "command": template.command,
                    "description": template.description,
                    "template": template.template,
                    "examples": template.examples[:2],
                    "category": template.category,
                    "action_type": template.action_type,
                    "score": score
                })

        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:limit]

    def get_all_commands(self, role: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available commands grouped by category for a role"""
        role_templates = [t for t in self.templates if role in t.roles]

        grouped = {}
        for template in role_templates:
            if template.category not in grouped:
                grouped[template.category] = []
            grouped[template.category].append({
                "command": template.command,
                "description": template.description,
                "template": template.template,
                "examples": template.examples,
                "action_type": template.action_type,
            })

        return grouped

    def get_quick_actions(self, role: str) -> List[Dict[str, Any]]:
        """Get quick action buttons based on role"""
        quick_actions = {
            "super_admin": [
                {"label": "Pending Shops", "command": "show pending shops", "icon": "clock"},
                {"label": "Platform Stats", "command": "show platform stats", "icon": "chart"},
                {"label": "All Shops", "command": "list shops", "icon": "store"},
                {"label": "All Users", "command": "list users", "icon": "users"},
                {"label": "Add Shop", "command": "add shop ", "icon": "plus"},
                {"label": "Categories", "command": "list shop categories", "icon": "grid"},
            ],
            "admin": [
                {"label": "Dashboard", "command": "show dashboard", "icon": "chart"},
                {"label": "Low Stock", "command": "show low stock", "icon": "alert"},
                {"label": "Pending Orders", "command": "list pending orders", "icon": "clock"},
                {"label": "All Products", "command": "list products", "icon": "box"},
                {"label": "All Orders", "command": "list orders", "icon": "list"},
                {"label": "Customers", "command": "list customers", "icon": "users"},
            ],
            "customer": [
                {"label": "Browse", "command": "browse categories", "icon": "grid"},
                {"label": "Search", "command": "search ", "icon": "search"},
                {"label": "My Orders", "command": "show my orders", "icon": "list"},
            ],
        }
        return quick_actions.get(role, [])

    def _get_popular_commands(self, role: str, limit: int) -> List[Dict[str, Any]]:
        """Get popular commands for a role"""
        popular = {
            "super_admin": [
                "get_pending_shops", "get_platform_stats", "list_shops",
                "verify_shop", "list_users", "list_shop_categories"
            ],
            "admin": [
                "get_shop_dashboard", "list_orders", "get_low_stock",
                "list_products", "confirm_order", "ship_order"
            ],
            "customer": [
                "list_shop_categories", "search_products", "list_my_orders",
                "place_order"
            ],
        }

        popular_commands = popular.get(role, [])
        suggestions = []

        for cmd in popular_commands[:limit]:
            for template in self.templates:
                if template.command == cmd and role in template.roles:
                    suggestions.append({
                        "command": template.command,
                        "description": template.description,
                        "template": template.template,
                        "examples": template.examples[:2],
                        "category": template.category,
                        "action_type": template.action_type,
                    })
                    break

        return suggestions

    def get_command_help(self, command: str) -> Optional[Dict[str, Any]]:
        """Get detailed help for a specific command"""
        for template in self.templates:
            if template.command == command:
                return {
                    "command": template.command,
                    "description": template.description,
                    "template": template.template,
                    "examples": template.examples,
                    "category": template.category,
                    "roles": template.roles,
                    "action_type": template.action_type,
                }
        return None
