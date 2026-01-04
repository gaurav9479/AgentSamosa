import json
import google.generativeai as genai
from typing import Dict, Any, Optional, List, Union

from app.core.config import settings
from app.schemas.command import ParsedIntent, MultiStepPlan


class IntentParser:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        self.system_prompt = """You are an intent parser for a command execution system.
Your job is to parse natural language commands into structured JSON actions.

Available actions:

=== PRODUCT COMMANDS (Shop Admin only) ===
- create_product: Create a new product (params: name, price, description?, quantity?, brand?, sku?, category_id?)
- update_product: Update a product (params: product_id, name?, price?, quantity?, description?, brand?, sku?)
- delete_product: Delete a product (params: product_id)
- list_products: List all products (params: shop_id?, category_id?, search?)
- get_product: Get a specific product (params: product_id or name)
- search_products: Search products (params: query, limit?)
- get_low_stock: Get low stock products (params: shop_id?)
- restock_product: Add stock to a product (params: product_id, quantity)
- set_product_price: Update product price (params: product_id, price)

=== ORDER COMMANDS (Shop Admin) ===
- list_orders: List all orders (params: status?, shop_id?)
- get_order: Get a specific order (params: order_id)
- confirm_order: Confirm a pending order (params: order_id)
- ship_order: Mark order as shipped (params: order_id, tracking_number?)
- deliver_order: Mark order as delivered (params: order_id)
- cancel_order: Cancel an order (params: order_id)
- refund_order: Process refund for order (params: order_id, reason?)

=== CUSTOMER ORDER COMMANDS (Customer) ===
- place_order: Place a new order (params: product_id, quantity)
- list_my_orders: List customer's own orders (params: customer_id?)
- update_order: Update order quantity (params: order_id, quantity)
- cancel_order: Cancel an order (params: order_id)

=== CUSTOMER MANAGEMENT (Shop Admin) ===
- list_customers: List all customers (params: none)
- get_customer: Get a specific customer (params: customer_id or email)
- search_customers: Search customers by name or email (params: query)

=== SHOP COMMANDS (Super Admin) ===
- prefill_shop_form: Pre-fill shop registration form - use when user says "add shop", "create shop", "register shop"
  (params: name?, description?, category_id?, owner_name?, owner_email?, owner_phone?, address?, city?, pincode?, gst_number?)
- update_shop: Update shop details (params: shop_id, name?, description?, address?, city?, pincode?)
- delete_shop: Delete a shop (params: shop_id)
- list_shops: List all shops (params: category_id?, city?, search?, is_verified?, is_active?)
- get_shop: Get shop details and stats (params: shop_id or name)
- verify_shop: Verify/approve a pending shop (params: shop_id or name)
- suspend_shop: Suspend a shop (params: shop_id or name)
- activate_shop: Activate a suspended shop (params: shop_id or name)
- get_pending_shops: Get all shops pending verification (params: none)

=== SHOP DASHBOARD COMMANDS (Shop Admin) ===
- get_shop_dashboard: Get shop dashboard stats (params: shop_id?)
- get_shop_low_stock: Get low stock products for shop (params: shop_id?)
- get_shop_orders: Get shop orders (params: shop_id?, status?)

=== USER COMMANDS (Super Admin) ===
- list_users: List all users (params: role?)
- get_user: Get user details (params: user_id or email)

=== PLATFORM COMMANDS (Super Admin) ===
- get_platform_stats: Get platform-wide statistics (params: none)

=== CATEGORY COMMANDS ===
- list_shop_categories: List shop categories (params: none)
- create_shop_category: Create shop category (params: name, description?, icon?)

=== BILLING & PROFIT COMMANDS (Shop Admin) ===
- sell_at_price: Sell product at bargained price (params: product_id, price/selling_price, quantity?, customer_name?, customer_phone?)
- generate_bill: Generate bill for order (params: order_id, bill_type: "customer"|"admin")
- get_daily_profit: Get daily profit report (params: shop_id, date?)
- get_product_profit: Get profit report by product (params: shop_id)
- get_profit_summary: Get overall profit summary (params: shop_id)

Rules:
1. Output ONLY valid JSON, no markdown or explanation
2. For destructive actions (delete, cancel, suspend), set requires_confirmation: true
3. When user says "add shop", "create shop", "register shop" -> use prefill_shop_form (NOT create_shop)
4. When user says "approve" or "verify" a shop -> use verify_shop
5. When user says "pending shops" -> use get_pending_shops
6. When user says "show my orders", "my orders" -> use list_my_orders
7. When user says "buy", "order", "purchase" a product -> use place_order
8. When user says "show dashboard", "my stats" -> use get_shop_dashboard
9. When user says "platform stats" -> use get_platform_stats
10. When user says "sell at", "sell for", "sold at" -> use sell_at_price
11. When user says "generate bill", "make bill", "print bill" -> use generate_bill
12. When user says "today's profit", "daily profit", "profit report" -> use get_daily_profit
13. When user says "product profit", "profit by product" -> use get_product_profit
14. When user says "profit summary", "my profit", "show profit" -> use get_profit_summary
15. For admin bill (with profit info), set bill_type: "admin". For customer bill, set bill_type: "customer"

Output format for single action:
{"action": "action_name", "entity": "product|order|shop|user|category", "parameters": {...}, "requires_confirmation": false}

Output format for multi-step:
{"steps": [{"action": "...", "entity": "...", "parameters": {...}}, ...]}
"""

    async def parse(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Union[ParsedIntent, MultiStepPlan]:
        context_str = ""
        if context:
            context_str = f"\n\nContext from previous interactions:\n{json.dumps(context)}"

        prompt = f"""{self.system_prompt}
{context_str}

User command: {user_input}

JSON output:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean up response if wrapped in markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            parsed = json.loads(response_text)

            # Check if it's a multi-step plan
            if "steps" in parsed:
                steps = [ParsedIntent(**step) for step in parsed["steps"]]
                return MultiStepPlan(steps=steps)

            return ParsedIntent(**parsed)

        except json.JSONDecodeError as e:
            return ParsedIntent(
                action="error",
                entity=None,
                parameters={"error": f"Failed to parse intent: {str(e)}"},
            )
        except Exception as e:
            return ParsedIntent(
                action="error",
                entity=None,
                parameters={"error": f"Intent parsing failed: {str(e)}"},
            )

    async def parse_with_retry(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        missing_params: Optional[List[str]] = None,
    ) -> ParsedIntent:
        """Re-parse with information about missing parameters"""
        retry_prompt = user_input
        if missing_params:
            retry_prompt = f"{user_input}\n\n[System: Previous attempt was missing: {', '.join(missing_params)}. Please ask the user for these values.]"

        result = await self.parse(retry_prompt, context)

        if isinstance(result, MultiStepPlan):
            return result.steps[0] if result.steps else ParsedIntent(
                action="error", parameters={"error": "Empty plan"}
            )
        return result
