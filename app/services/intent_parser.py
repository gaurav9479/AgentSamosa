import json
import re
import google.generativeai as genai
from typing import Dict, Any, Optional, List, Union

from app.core.config import settings
from app.schemas.command import ParsedIntent, MultiStepPlan


class FallbackParser:
    """Rule-based fallback parser for when AI API is unavailable (rate limits, errors)"""

    # Hindi/Hinglish keyword mappings to actions
    KEYWORD_PATTERNS = {
        # Product commands
        'list_products': [
            r'(?:सभी|सारे|all)\s*(?:प्रोडक्ट|products?|प्रोडक्ट्स)',
            r'(?:प्रोडक्ट|products?|प्रोडक्ट्स)\s*(?:दिखाओ|दिखा|dikhao|list|show|batao|बताओ)',
            r'(?:show|list|दिखाओ|dikhao)\s*(?:all\s*)?(?:प्रोडक्ट|products?|प्रोडक्ट्स)',
            r'products?\s*(?:list|show|दिखाओ)',
        ],
        'get_low_stock': [
            r'(?:low|कम|kam)\s*(?:stock|स्टॉक)',
            r'(?:stock|स्टॉक)\s*(?:कम|low|kam)',
            r'(?:कम|low)\s*(?:stock|स्टॉक)\s*(?:दिखाओ|dikhao|show|batao)?',
            r'low\s*stock\s*(?:products?|items?|प्रोडक्ट)?',
        ],
        'search_products': [
            r'(?:search|खोजो|khojo|ढूंढो|dhundho|find)\s+(.+)',
            r'(.+)\s*(?:खोजो|khojo|ढूंढो|dhundho|search)',
        ],

        # Order commands
        'list_orders': [
            r'(?:सभी|सारे|all)\s*(?:orders?|ऑर्डर|ऑर्डर्स)',
            r'(?:orders?|ऑर्डर)\s*(?:दिखाओ|दिखा|dikhao|list|show|batao|बताओ)',
            r'(?:show|list|दिखाओ|dikhao)\s*(?:all\s*)?(?:orders?|ऑर्डर)',
            r'(?:pending|confirmed|shipped)\s*orders?',
            r'(?:पेंडिंग|कन्फर्म|शिप)\s*(?:orders?|ऑर्डर)',
        ],
        'list_my_orders': [
            r'(?:मेरे|mere|my)\s*(?:orders?|ऑर्डर)',
            r'(?:my|मेरे)\s*(?:orders?|ऑर्डर)\s*(?:दिखाओ|dikhao|show)?',
        ],

        # Dashboard/Stats commands
        'get_shop_dashboard': [
            r'(?:dashboard|डैशबोर्ड)',
            r'(?:shop|दुकान|store)\s*(?:stats?|statistics|स्टैट्स)',
            r'(?:my|मेरी|मेरा)\s*(?:stats?|dashboard|डैशबोर्ड)',
            r'(?:stats?|स्टैट्स)\s*(?:दिखाओ|dikhao|show)?',
        ],
        'get_platform_stats': [
            r'(?:platform|प्लेटफॉर्म)\s*(?:stats?|statistics|स्टैट्स)',
            r'(?:overall|total|कुल)\s*(?:stats?|statistics|स्टैट्स)',
        ],
        'get_daily_profit': [
            r'(?:आज\s*का|aaj\s*ka|today\'?s?)\s*(?:profit|प्रॉफिट|मुनाफा)',
            r'(?:daily|रोज़|रोज)\s*(?:profit|प्रॉफिट|मुनाफा)',
            r'(?:profit|प्रॉफिट)\s*(?:आज|today|daily)',
        ],
        'get_profit_summary': [
            r'(?:profit|प्रॉफिट|मुनाफा)\s*(?:summary|report|दिखाओ|dikhao|show|batao)?',
            r'(?:show|दिखाओ|dikhao)\s*(?:profit|प्रॉफिट|मुनाफा)',
            r'(?:मेरा|mera|my)\s*(?:profit|प्रॉफिट|मुनाफा)',
        ],

        # Shop commands (Super Admin)
        'list_shops': [
            r'(?:सभी|सारे|all)\s*(?:shops?|दुकान|दुकानें|stores?)',
            r'(?:shops?|दुकान|दुकानें)\s*(?:दिखाओ|दिखा|dikhao|list|show|batao)',
            r'(?:show|list|दिखाओ|dikhao)\s*(?:all\s*)?(?:shops?|दुकान)',
        ],
        'get_pending_shops': [
            r'(?:pending|पेंडिंग)\s*(?:shops?|दुकान|दुकानें)',
            r'(?:shops?|दुकान)\s*(?:pending|पेंडिंग|verification)',
            r'(?:unverified|अनवेरिफाइड)\s*(?:shops?|दुकान)',
        ],
        'verify_shop': [
            r'(?:verify|वेरिफाई|approve|अप्रूव)\s*(?:shop|दुकान)\s*(.+)?',
            r'(?:shop|दुकान)\s*(.+)?\s*(?:verify|वेरिफाई|approve|अप्रूव)\s*(?:करो|karo)?',
        ],

        # Customer commands
        'list_customers': [
            r'(?:सभी|सारे|all)\s*(?:customers?|ग्राहक|कस्टमर)',
            r'(?:customers?|ग्राहक|कस्टमर)\s*(?:दिखाओ|dikhao|list|show|batao)',
            r'(?:show|list|दिखाओ|dikhao)\s*(?:all\s*)?(?:customers?|ग्राहक)',
        ],

        # User commands
        'list_users': [
            r'(?:सभी|सारे|all)\s*(?:users?|यूज़र)',
            r'(?:users?|यूज़र)\s*(?:दिखाओ|dikhao|list|show)',
        ],

        # Category commands
        'list_shop_categories': [
            r'(?:categories|कैटेगरी|श्रेणी)\s*(?:दिखाओ|dikhao|list|show)?',
            r'(?:shop|दुकान)\s*(?:categories|कैटेगरी)',
        ],
    }

    # Entity mapping based on action
    ACTION_ENTITY_MAP = {
        'list_products': 'product',
        'get_low_stock': 'product',
        'search_products': 'product',
        'list_orders': 'order',
        'list_my_orders': 'order',
        'get_shop_dashboard': 'shop',
        'get_platform_stats': 'platform',
        'get_daily_profit': 'shop',
        'get_profit_summary': 'shop',
        'list_shops': 'shop',
        'get_pending_shops': 'shop',
        'verify_shop': 'shop',
        'list_customers': 'customer',
        'list_users': 'user',
        'list_shop_categories': 'category',
    }

    @classmethod
    def parse(cls, user_input: str) -> Optional[ParsedIntent]:
        """Try to parse user input using rule-based patterns"""
        text = user_input.lower().strip()

        for action, patterns in cls.KEYWORD_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
                if match:
                    parameters = {}

                    # Extract parameters from captured groups
                    if match.groups():
                        query = match.group(1)
                        if query and query.strip():
                            if action == 'search_products':
                                parameters['query'] = query.strip()
                            elif action == 'verify_shop':
                                parameters['name'] = query.strip()

                    # Extract status filters for orders
                    if action == 'list_orders':
                        if any(s in text for s in ['pending', 'पेंडिंग']):
                            parameters['status'] = 'pending'
                        elif any(s in text for s in ['confirmed', 'कन्फर्म']):
                            parameters['status'] = 'confirmed'
                        elif any(s in text for s in ['shipped', 'शिप']):
                            parameters['status'] = 'shipped'
                        elif any(s in text for s in ['delivered', 'डिलीवर']):
                            parameters['status'] = 'delivered'

                    entity = cls.ACTION_ENTITY_MAP.get(action)

                    return ParsedIntent(
                        action=action,
                        entity=entity,
                        parameters=parameters,
                        requires_confirmation=False
                    )

        return None


class IntentParser:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        self.system_prompt = """You are an intent parser for a command execution system.
Your job is to parse natural language commands into structured JSON actions.
You understand both English and Hindi (including Hinglish - mixed Hindi-English).

IMPORTANT: You can understand commands in:
- English: "add product iPhone price 50000"
- Hindi (Devanagari): "प्रोडक्ट जोड़ो iPhone कीमत 50000"
- Hinglish (Romanized Hindi): "product add karo iPhone price 50000"
- Mixed: "show all pending orders yaar" or "sab orders dikhao"

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

Hindi/Hinglish Command Patterns (treat same as English equivalents):
- "प्रोडक्ट जोड़ो/बनाओ" or "product add karo/banao" -> create_product
- "प्रोडक्ट दिखाओ/लिस्ट करो" or "products dikhao/list karo" -> list_products
- "प्रोडक्ट अपडेट करो/बदलो" or "product update karo/badlo" -> update_product
- "प्रोडक्ट हटाओ/डिलीट करो" or "product hatao/delete karo" -> delete_product
- "स्टॉक बढ़ाओ/जोड़ो" or "stock badhao/add karo" -> restock_product
- "कम स्टॉक दिखाओ" or "low stock dikhao/batao" -> get_low_stock
- "ऑर्डर दिखाओ" or "orders dikhao/list karo" -> list_orders
- "ऑर्डर कन्फर्म करो" or "order confirm karo" -> confirm_order
- "ऑर्डर भेजो/शिप करो" or "order ship karo/bhejo" -> ship_order
- "ऑर्डर डिलीवर करो" or "order deliver karo" -> deliver_order
- "ऑर्डर कैंसल करो" or "order cancel karo" -> cancel_order
- "दुकान जोड़ो/बनाओ" or "shop add karo/banao/register karo" -> prefill_shop_form
- "दुकान वेरिफाई करो" or "shop verify karo/approve karo" -> verify_shop
- "पेंडिंग दुकानें दिखाओ" or "pending shops dikhao" -> get_pending_shops
- "मेरे ऑर्डर दिखाओ" or "mere orders dikhao" -> list_my_orders
- "खरीदना है/ऑर्डर करना है" or "kharidna hai/order karna hai" -> place_order
- "डैशबोर्ड दिखाओ" or "dashboard dikhao" -> get_shop_dashboard
- "प्लेटफॉर्म स्टैट्स" or "platform stats dikhao" -> get_platform_stats
- "इस दाम पर बेचो" or "is price pe becho/sell karo" -> sell_at_price
- "बिल बनाओ" or "bill banao/generate karo" -> generate_bill
- "आज का प्रॉफिट" or "aaj ka profit/daily profit" -> get_daily_profit
- "प्रॉफिट दिखाओ" or "profit dikhao/batao" -> get_profit_summary
- "ग्राहक दिखाओ" or "customers dikhao" -> list_customers
- "सर्च करो" or "search karo/dhundho" -> search_products

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
            # Try fallback parser for JSON decode errors
            fallback_result = FallbackParser.parse(user_input)
            if fallback_result:
                return fallback_result
            return ParsedIntent(
                action="error",
                entity=None,
                parameters={"error": f"Failed to parse intent: {str(e)}"},
            )
        except Exception as e:
            # Try fallback parser when AI API fails (rate limits, errors)
            error_str = str(e)
            fallback_result = FallbackParser.parse(user_input)
            if fallback_result:
                # Add note that fallback was used
                fallback_result.parameters = fallback_result.parameters or {}
                fallback_result.parameters['_fallback'] = True
                return fallback_result

            # If fallback also fails, return error
            return ParsedIntent(
                action="error",
                entity=None,
                parameters={"error": f"Intent parsing failed: {error_str}"},
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
