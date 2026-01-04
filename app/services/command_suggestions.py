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
    description_hi: str  # Hindi description
    template: str
    template_hi: str  # Hindi template
    examples: List[str]
    examples_hi: List[str]  # Hindi/Hinglish examples
    category: str
    category_hi: str  # Hindi category
    roles: List[str]  # super_admin, admin, customer
    keywords_hi: List[str] = None  # Hindi keywords for search
    action_type: str = "execute"  # execute, prefill_form


# ============== SUPER ADMIN COMMANDS ==============
# Focus: Platform management, shop verification, categories, user management
# NO product creation (too complex, delegate to shop admin)

SUPER_ADMIN_COMMANDS: List[CommandTemplate] = [
    # Shop Management
    CommandTemplate(
        command="prefill_shop_form",
        description="Fill shop registration form with details",
        description_hi="दुकान रजिस्ट्रेशन फॉर्म भरें",
        template='add shop "{name}" owner "{owner}" email {email} city "{city}"',
        template_hi='दुकान जोड़ो "{name}" मालिक "{owner}" ईमेल {email} शहर "{city}"',
        examples=[
            'add shop "Tech Hub" owner "John Doe" email john@test.com city "Mumbai"',
            'register shop "Beauty Palace" owner "Jane Smith" email jane@shop.com',
            'create shop "Fresh Mart" in category 3 owner "Bob"',
        ],
        examples_hi=[
            'दुकान जोड़ो "Tech Hub" मालिक "राम" शहर "मुंबई"',
            'shop register karo "किराना स्टोर" owner "श्याम"',
            'naya shop banao "मोबाइल शॉप" city "दिल्ली"',
        ],
        category="Shop Registration",
        category_hi="दुकान रजिस्ट्रेशन",
        roles=["super_admin"],
        keywords_hi=["दुकान", "जोड़ो", "बनाओ", "रजिस्टर"],
        action_type="prefill_form"
    ),
    CommandTemplate(
        command="verify_shop",
        description="Verify/approve a pending shop",
        description_hi="पेंडिंग दुकान को वेरिफाई/अप्रूव करें",
        template="verify shop {id}",
        template_hi="दुकान वेरिफाई करो {id}",
        examples=[
            "verify shop 5",
            "approve shop 12",
            'approve shop "Tech Store"',
            "verify pending shop 8",
        ],
        examples_hi=[
            "shop 5 verify karo",
            "दुकान 12 approve करो",
            "shop verify karo 8",
        ],
        category="Shop Management",
        category_hi="दुकान प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["वेरिफाई", "अप्रूव", "मंजूरी"]
    ),
    CommandTemplate(
        command="suspend_shop",
        description="Suspend an active shop",
        description_hi="एक्टिव दुकान को सस्पेंड करें",
        template="suspend shop {id}",
        template_hi="दुकान सस्पेंड करो {id}",
        examples=[
            "suspend shop 5",
            'suspend shop "Bad Store"',
        ],
        examples_hi=[
            "shop 5 suspend karo",
            "दुकान बंद करो 12",
        ],
        category="Shop Management",
        category_hi="दुकान प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["सस्पेंड", "बंद"]
    ),
    CommandTemplate(
        command="activate_shop",
        description="Activate a suspended shop",
        description_hi="सस्पेंड दुकान को एक्टिवेट करें",
        template="activate shop {id}",
        template_hi="दुकान एक्टिवेट करो {id}",
        examples=[
            "activate shop 5",
            "reactivate shop 12",
        ],
        examples_hi=[
            "shop 5 activate karo",
            "दुकान चालू करो 12",
        ],
        category="Shop Management",
        category_hi="दुकान प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["एक्टिवेट", "चालू"]
    ),
    CommandTemplate(
        command="get_pending_shops",
        description="View shops pending verification",
        description_hi="वेरिफिकेशन के लिए पेंडिंग दुकानें देखें",
        template="show pending shops",
        template_hi="पेंडिंग दुकानें दिखाओ",
        examples=[
            "show pending shops",
            "list shops waiting for approval",
            "pending verifications",
        ],
        examples_hi=[
            "pending shops dikhao",
            "पेंडिंग दुकानें दिखाओ",
            "approval ke liye kaun si shops hai",
        ],
        category="Shop Management",
        category_hi="दुकान प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["पेंडिंग", "इंतज़ार"]
    ),
    CommandTemplate(
        command="list_shops",
        description="List all shops",
        description_hi="सभी दुकानें देखें",
        template="list shops",
        template_hi="सभी दुकानें दिखाओ",
        examples=[
            "list shops",
            "show all shops",
            "list shops in Mumbai",
            "show verified shops",
        ],
        examples_hi=[
            "sab shops dikhao",
            "सभी दुकानें दिखाओ",
            "Mumbai ki shops dikhao",
        ],
        category="Shop Management",
        category_hi="दुकान प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["दुकानें", "सभी", "लिस्ट"]
    ),
    CommandTemplate(
        command="get_shop",
        description="View shop details and stats",
        description_hi="दुकान की जानकारी देखें",
        template="show shop {id}",
        template_hi="दुकान दिखाओ {id}",
        examples=[
            "show shop 5",
            'get shop "Tech Hub" stats',
            "view shop 12 details",
        ],
        examples_hi=[
            "shop 5 ki details dikhao",
            "दुकान 12 की जानकारी",
        ],
        category="Shop Management",
        category_hi="दुकान प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["जानकारी", "डिटेल्स"]
    ),

    # Platform Stats
    CommandTemplate(
        command="get_platform_stats",
        description="View platform statistics",
        description_hi="प्लेटफॉर्म के आंकड़े देखें",
        template="show platform stats",
        template_hi="प्लेटफॉर्म स्टैट्स दिखाओ",
        examples=[
            "show platform stats",
            "platform overview",
            "show dashboard",
        ],
        examples_hi=[
            "platform stats dikhao",
            "प्लेटफॉर्म के आंकड़े दिखाओ",
            "dashboard dikhao",
        ],
        category="Platform",
        category_hi="प्लेटफॉर्म",
        roles=["super_admin"],
        keywords_hi=["आंकड़े", "स्टैट्स", "डैशबोर्ड"]
    ),

    # User Management
    CommandTemplate(
        command="list_users",
        description="List all users",
        description_hi="सभी यूज़र्स देखें",
        template="list users",
        template_hi="सभी यूज़र्स दिखाओ",
        examples=[
            "list users",
            "show all users",
            "list admin users",
            "show customers",
        ],
        examples_hi=[
            "sab users dikhao",
            "सभी यूज़र्स दिखाओ",
            "customers dikhao",
        ],
        category="User Management",
        category_hi="यूज़र प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["यूज़र्स", "ग्राहक"]
    ),
    CommandTemplate(
        command="get_user",
        description="View user details",
        description_hi="यूज़र की जानकारी देखें",
        template="show user {id}",
        template_hi="यूज़र दिखाओ {id}",
        examples=[
            "show user 5",
            'get user "john@test.com"',
        ],
        examples_hi=[
            "user 5 ki details dikhao",
            "यूज़र की जानकारी दो",
        ],
        category="User Management",
        category_hi="यूज़र प्रबंधन",
        roles=["super_admin"],
        keywords_hi=["यूज़र", "जानकारी"]
    ),

    # Category Management
    CommandTemplate(
        command="list_shop_categories",
        description="List shop categories",
        description_hi="दुकान कैटेगरी देखें",
        template="list shop categories",
        template_hi="दुकान कैटेगरी दिखाओ",
        examples=[
            "list shop categories",
            "show business types",
        ],
        examples_hi=[
            "shop categories dikhao",
            "दुकान कैटेगरी दिखाओ",
        ],
        category="Categories",
        category_hi="कैटेगरी",
        roles=["super_admin"],
        keywords_hi=["कैटेगरी", "प्रकार"]
    ),
    CommandTemplate(
        command="create_shop_category",
        description="Create a new shop category",
        description_hi="नई दुकान कैटेगरी बनाएं",
        template='create category "{name}"',
        template_hi='नई कैटेगरी बनाओ "{name}"',
        examples=[
            'create category "Electronics"',
            'add shop category "Pharmacy" description "Medical stores"',
        ],
        examples_hi=[
            'नई category बनाओ "इलेक्ट्रॉनिक्स"',
            'category add karo "दवाई की दुकान"',
        ],
        category="Categories",
        category_hi="कैटेगरी",
        roles=["super_admin"],
        keywords_hi=["नई", "बनाओ", "कैटेगरी"]
    ),
]


# ============== SHOP ADMIN COMMANDS ==============
# Focus: Product management, order management, inventory, shop dashboard

SHOP_ADMIN_COMMANDS: List[CommandTemplate] = [
    # Dashboard
    CommandTemplate(
        command="get_shop_dashboard",
        description="View your shop dashboard",
        description_hi="अपनी दुकान का डैशबोर्ड देखें",
        template="show dashboard",
        template_hi="डैशबोर्ड दिखाओ",
        examples=[
            "show dashboard",
            "my shop stats",
            "shop overview",
        ],
        examples_hi=[
            "dashboard dikhao",
            "मेरी दुकान के आंकड़े",
            "shop stats dikhao",
        ],
        category="Dashboard",
        category_hi="डैशबोर्ड",
        roles=["admin"],
        keywords_hi=["डैशबोर्ड", "आंकड़े", "स्टैट्स"]
    ),

    # Product Management
    CommandTemplate(
        command="create_product",
        description="Create a new product with cost and selling price",
        description_hi="नया प्रोडक्ट बनाएं (कॉस्ट और सेलिंग प्राइस के साथ)",
        template='create product "{name}" cost {cost} price {price} quantity {qty}',
        template_hi='प्रोडक्ट जोड़ो "{name}" कॉस्ट {cost} प्राइस {price} मात्रा {qty}',
        examples=[
            'create product "iPhone 15" cost 700 price 999 quantity 50',
            'add product "Shampoo" cost 70 price 150 min 90 quantity 100',
            'new product "T-Shirt" cost 200 price 499 quantity 50',
        ],
        examples_hi=[
            'product add karo "चावल" cost 40 price 60 quantity 100',
            'नया प्रोडक्ट "दाल" कीमत 80 मात्रा 50',
            'प्रोडक्ट जोड़ो "साबुन" cost 20 price 35',
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["प्रोडक्ट", "जोड़ो", "बनाओ", "नया"]
    ),
    CommandTemplate(
        command="update_product",
        description="Update product details",
        description_hi="प्रोडक्ट की जानकारी अपडेट करें",
        template="update product {id} {field} {value}",
        template_hi="प्रोडक्ट अपडेट करो {id} {field} {value}",
        examples=[
            "update product 5 price 89.99",
            "update product 12 quantity 100",
            "change product 8 name 'Premium Widget'",
        ],
        examples_hi=[
            "product 5 ki price update karo 89",
            "प्रोडक्ट 12 की मात्रा बदलो 100",
            "product 8 ka naam badlo",
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["अपडेट", "बदलो", "एडिट"]
    ),
    CommandTemplate(
        command="restock_product",
        description="Add stock to a product",
        description_hi="प्रोडक्ट में स्टॉक जोड़ें",
        template="restock product {id} add {qty}",
        template_hi="प्रोडक्ट {id} में {qty} स्टॉक जोड़ो",
        examples=[
            "restock product 5 add 100",
            "add 50 units to product 12",
            "increase stock of product 8 by 200",
        ],
        examples_hi=[
            "product 5 mein 100 stock add karo",
            "प्रोडक्ट 12 में 50 जोड़ो",
            "stock badhao product 8 mein 200",
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["स्टॉक", "जोड़ो", "बढ़ाओ", "रीस्टॉक"]
    ),
    CommandTemplate(
        command="set_product_price",
        description="Update product price",
        description_hi="प्रोडक्ट की कीमत बदलें",
        template="set price of product {id} to {price}",
        template_hi="प्रोडक्ट {id} की कीमत {price} करो",
        examples=[
            "set price of product 5 to 49.99",
            "change price of product 12 to 29.99",
        ],
        examples_hi=[
            "product 5 ki price 50 karo",
            "प्रोडक्ट 12 की कीमत 30 रखो",
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["कीमत", "प्राइस", "रेट"]
    ),
    CommandTemplate(
        command="list_products",
        description="List all products",
        description_hi="सभी प्रोडक्ट्स देखें",
        template="list products",
        template_hi="प्रोडक्ट्स दिखाओ",
        examples=[
            "list products",
            "show all products",
            "list products in category 3",
        ],
        examples_hi=[
            "sab products dikhao",
            "सभी प्रोडक्ट्स दिखाओ",
            "products ki list",
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["प्रोडक्ट्स", "सभी", "लिस्ट", "दिखाओ"]
    ),
    CommandTemplate(
        command="get_low_stock",
        description="View low stock products",
        description_hi="कम स्टॉक वाले प्रोडक्ट्स देखें",
        template="show low stock",
        template_hi="कम स्टॉक दिखाओ",
        examples=[
            "show low stock products",
            "what needs restocking",
            "low inventory",
        ],
        examples_hi=[
            "low stock dikhao",
            "कम स्टॉक वाले products",
            "kya restock karna hai",
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["कम", "स्टॉक", "खत्म"]
    ),
    CommandTemplate(
        command="delete_product",
        description="Delete a product",
        description_hi="प्रोडक्ट डिलीट करें",
        template="delete product {id}",
        template_hi="प्रोडक्ट हटाओ {id}",
        examples=[
            "delete product 5",
            "remove product 12",
        ],
        examples_hi=[
            "product 5 delete karo",
            "प्रोडक्ट 12 हटाओ",
        ],
        category="Products",
        category_hi="प्रोडक्ट्स",
        roles=["admin"],
        keywords_hi=["हटाओ", "डिलीट", "निकालो"]
    ),

    # Order Management
    CommandTemplate(
        command="list_orders",
        description="List all orders",
        description_hi="सभी ऑर्डर्स देखें",
        template="list orders",
        template_hi="ऑर्डर्स दिखाओ",
        examples=[
            "list orders",
            "show all orders",
            "list pending orders",
            "show today's orders",
        ],
        examples_hi=[
            "sab orders dikhao",
            "सभी ऑर्डर्स दिखाओ",
            "pending orders dikhao",
            "aaj ke orders",
        ],
        category="Orders",
        category_hi="ऑर्डर्स",
        roles=["admin"],
        keywords_hi=["ऑर्डर्स", "सभी", "दिखाओ"]
    ),
    CommandTemplate(
        command="get_order",
        description="View order details",
        description_hi="ऑर्डर की जानकारी देखें",
        template="show order {id}",
        template_hi="ऑर्डर दिखाओ {id}",
        examples=[
            "show order 123",
            "order details 456",
        ],
        examples_hi=[
            "order 123 ki details dikhao",
            "ऑर्डर 456 की जानकारी",
        ],
        category="Orders",
        category_hi="ऑर्डर्स",
        roles=["admin"],
        keywords_hi=["ऑर्डर", "जानकारी", "डिटेल्स"]
    ),
    CommandTemplate(
        command="confirm_order",
        description="Confirm a pending order",
        description_hi="पेंडिंग ऑर्डर कन्फर्म करें",
        template="confirm order {id}",
        template_hi="ऑर्डर कन्फर्म करो {id}",
        examples=[
            "confirm order 123",
            "approve order 456",
        ],
        examples_hi=[
            "order 123 confirm karo",
            "ऑर्डर 456 कन्फर्म करो",
        ],
        category="Orders",
        category_hi="ऑर्डर्स",
        roles=["admin"],
        keywords_hi=["कन्फर्म", "अप्रूव", "मंजूर"]
    ),
    CommandTemplate(
        command="ship_order",
        description="Mark order as shipped",
        description_hi="ऑर्डर शिप किया मार्क करें",
        template="ship order {id}",
        template_hi="ऑर्डर शिप करो {id}",
        examples=[
            "ship order 123",
            "mark order 456 as shipped",
            'ship order 789 tracking "TRK123"',
        ],
        examples_hi=[
            "order 123 ship karo",
            "ऑर्डर 456 भेजो",
        ],
        category="Orders",
        category_hi="ऑर्डर्स",
        roles=["admin"],
        keywords_hi=["शिप", "भेजो", "डिस्पैच"]
    ),
    CommandTemplate(
        command="deliver_order",
        description="Mark order as delivered",
        description_hi="ऑर्डर डिलीवर हुआ मार्क करें",
        template="deliver order {id}",
        template_hi="ऑर्डर डिलीवर करो {id}",
        examples=[
            "deliver order 123",
            "mark order 456 as delivered",
            "complete order 789",
        ],
        examples_hi=[
            "order 123 deliver hua",
            "ऑर्डर 456 डिलीवर हो गया",
        ],
        category="Orders",
        category_hi="ऑर्डर्स",
        roles=["admin"],
        keywords_hi=["डिलीवर", "पहुंचा", "कम्प्लीट"]
    ),
    CommandTemplate(
        command="cancel_order",
        description="Cancel an order",
        description_hi="ऑर्डर कैंसल करें",
        template="cancel order {id}",
        template_hi="ऑर्डर कैंसल करो {id}",
        examples=[
            "cancel order 123",
        ],
        examples_hi=[
            "order 123 cancel karo",
            "ऑर्डर 456 कैंसल करो",
        ],
        category="Orders",
        category_hi="ऑर्डर्स",
        roles=["admin"],
        keywords_hi=["कैंसल", "रद्द"]
    ),

    # Customer Management
    CommandTemplate(
        command="list_customers",
        description="List all customers",
        description_hi="सभी ग्राहक देखें",
        template="list customers",
        template_hi="ग्राहक दिखाओ",
        examples=[
            "list customers",
            "show all customers",
        ],
        examples_hi=[
            "sab customers dikhao",
            "सभी ग्राहक दिखाओ",
        ],
        category="Customers",
        category_hi="ग्राहक",
        roles=["admin"],
        keywords_hi=["ग्राहक", "कस्टमर्स"]
    ),
    CommandTemplate(
        command="search_customers",
        description="Search customers",
        description_hi="ग्राहक खोजें",
        template='search customers "{query}"',
        template_hi='ग्राहक खोजो "{query}"',
        examples=[
            'search customers "john"',
            'find customer "jane@test.com"',
        ],
        examples_hi=[
            'customer dhundho "राम"',
            'ग्राहक खोजो "9876543210"',
        ],
        category="Customers",
        category_hi="ग्राहक",
        roles=["admin"],
        keywords_hi=["खोजो", "ढूंढो", "सर्च"]
    ),

    # Billing & Sales
    CommandTemplate(
        command="sell_at_price",
        description="Sell product at bargained price",
        description_hi="मोलभाव वाले दाम पर बेचें",
        template="sell product {id} at {price}",
        template_hi="प्रोडक्ट {id} {price} में बेचो",
        examples=[
            "sell product 5 at 100",
            "sell product 12 at 80 to customer Ram",
            "sold product 8 at 150 quantity 2",
        ],
        examples_hi=[
            "product 5 100 mein becho",
            "प्रोडक्ट 12 को 80 में बेचो customer राम",
            "product 8 becha 150 mein 2 quantity",
        ],
        category="Billing",
        category_hi="बिलिंग",
        roles=["admin"],
        keywords_hi=["बेचो", "बिक्री", "सेल"]
    ),
    CommandTemplate(
        command="generate_bill",
        description="Generate bill for an order",
        description_hi="ऑर्डर का बिल बनाएं",
        template="generate bill for order {id}",
        template_hi="ऑर्डर {id} का बिल बनाओ",
        examples=[
            "generate bill for order 123",
            "print bill for order 456",
            "make admin bill for order 789",
        ],
        examples_hi=[
            "order 123 ka bill banao",
            "ऑर्डर 456 का बिल प्रिंट करो",
        ],
        category="Billing",
        category_hi="बिलिंग",
        roles=["admin"],
        keywords_hi=["बिल", "रसीद", "प्रिंट"]
    ),
    CommandTemplate(
        command="get_daily_profit",
        description="View daily profit report",
        description_hi="आज का प्रॉफिट देखें",
        template="show today's profit",
        template_hi="आज का प्रॉफिट दिखाओ",
        examples=[
            "show today's profit",
            "daily profit report",
            "profit for 2025-01-03",
        ],
        examples_hi=[
            "aaj ka profit dikhao",
            "आज का प्रॉफिट",
            "daily profit batao",
        ],
        category="Billing",
        category_hi="बिलिंग",
        roles=["admin"],
        keywords_hi=["प्रॉफिट", "मुनाफा", "आज"]
    ),
    CommandTemplate(
        command="get_product_profit",
        description="View profit by product",
        description_hi="प्रोडक्ट के हिसाब से प्रॉफिट देखें",
        template="show product profit",
        template_hi="प्रोडक्ट प्रॉफिट दिखाओ",
        examples=[
            "show product profit",
            "profit by product",
            "which products are most profitable",
        ],
        examples_hi=[
            "product wise profit dikhao",
            "किस प्रोडक्ट में ज्यादा प्रॉफिट",
        ],
        category="Billing",
        category_hi="बिलिंग",
        roles=["admin"],
        keywords_hi=["प्रोडक्ट", "प्रॉफिट"]
    ),
    CommandTemplate(
        command="get_profit_summary",
        description="View overall profit summary",
        description_hi="कुल प्रॉफिट सारांश देखें",
        template="show profit summary",
        template_hi="प्रॉफिट सारांश दिखाओ",
        examples=[
            "show profit summary",
            "my profit",
            "today's earnings",
        ],
        examples_hi=[
            "profit summary dikhao",
            "मेरा प्रॉफिट",
            "कुल कमाई",
        ],
        category="Billing",
        category_hi="बिलिंग",
        roles=["admin"],
        keywords_hi=["प्रॉफिट", "मुनाफा", "कमाई", "सारांश"]
    ),
]


# ============== CUSTOMER COMMANDS ==============
# Focus: Browsing, searching, placing orders, managing their orders

CUSTOMER_COMMANDS: List[CommandTemplate] = [
    # Browsing
    CommandTemplate(
        command="list_shop_categories",
        description="Browse shop categories",
        description_hi="दुकान कैटेगरी देखें",
        template="browse categories",
        template_hi="कैटेगरी देखो",
        examples=[
            "browse categories",
            "show shop categories",
            "what can I shop for",
        ],
        examples_hi=[
            "categories dikhao",
            "कैटेगरी दिखाओ",
            "kya kya mil sakta hai",
        ],
        category="Browse",
        category_hi="ब्राउज़",
        roles=["customer"],
        keywords_hi=["कैटेगरी", "दिखाओ", "देखो"]
    ),
    CommandTemplate(
        command="list_shops",
        description="Browse shops",
        description_hi="दुकानें देखें",
        template="browse shops",
        template_hi="दुकानें दिखाओ",
        examples=[
            "browse shops",
            "show shops in Beauty",
            "find shops in Mumbai",
        ],
        examples_hi=[
            "shops dikhao",
            "दुकानें दिखाओ",
            "Mumbai ki dukane dikhao",
        ],
        category="Browse",
        category_hi="ब्राउज़",
        roles=["customer"],
        keywords_hi=["दुकानें", "शॉप्स"]
    ),
    CommandTemplate(
        command="search_products",
        description="Search for products",
        description_hi="प्रोडक्ट खोजें",
        template='search "{query}"',
        template_hi='खोजो "{query}"',
        examples=[
            'search "phone"',
            'find "organic shampoo"',
            'search for "laptop"',
        ],
        examples_hi=[
            'search karo "मोबाइल"',
            'खोजो "शैम्पू"',
            'dhundho "लैपटॉप"',
        ],
        category="Browse",
        category_hi="ब्राउज़",
        roles=["customer"],
        keywords_hi=["खोजो", "ढूंढो", "सर्च"]
    ),

    # Order Management
    CommandTemplate(
        command="place_order",
        description="Place a new order",
        description_hi="नया ऑर्डर करें",
        template="order product {id} quantity {qty}",
        template_hi="प्रोडक्ट {id} ऑर्डर करो {qty} मात्रा",
        examples=[
            "order product 5 quantity 2",
            "buy 3 of product 12",
            "place order for product 8",
        ],
        examples_hi=[
            "product 5 order karo 2 quantity",
            "प्रोडक्ट 12 खरीदो",
            "product 8 kharidna hai",
        ],
        category="My Orders",
        category_hi="मेरे ऑर्डर्स",
        roles=["customer"],
        keywords_hi=["ऑर्डर", "खरीदो", "लेना"]
    ),
    CommandTemplate(
        command="list_my_orders",
        description="View my orders",
        description_hi="मेरे ऑर्डर्स देखें",
        template="show my orders",
        template_hi="मेरे ऑर्डर्स दिखाओ",
        examples=[
            "show my orders",
            "my order history",
            "list my orders",
        ],
        examples_hi=[
            "mere orders dikhao",
            "मेरे ऑर्डर्स दिखाओ",
            "order history dikhao",
        ],
        category="My Orders",
        category_hi="मेरे ऑर्डर्स",
        roles=["customer"],
        keywords_hi=["मेरे", "ऑर्डर्स"]
    ),
    CommandTemplate(
        command="get_order",
        description="Track an order",
        description_hi="ऑर्डर ट्रैक करें",
        template="track order {id}",
        template_hi="ऑर्डर ट्रैक करो {id}",
        examples=[
            "track order 123",
            "where is my order 456",
            "order status 789",
        ],
        examples_hi=[
            "order 123 track karo",
            "मेरा ऑर्डर 456 कहां है",
            "order status batao",
        ],
        category="My Orders",
        category_hi="मेरे ऑर्डर्स",
        roles=["customer"],
        keywords_hi=["ट्रैक", "कहां", "स्टेटस"]
    ),
    CommandTemplate(
        command="update_order",
        description="Update order quantity",
        description_hi="ऑर्डर में बदलाव करें",
        template="update order {id} quantity {qty}",
        template_hi="ऑर्डर {id} अपडेट करो {qty} मात्रा",
        examples=[
            "update order 123 quantity 5",
            "change order 456 to 3 items",
        ],
        examples_hi=[
            "order 123 update karo 5 quantity",
            "ऑर्डर 456 में 3 करो",
        ],
        category="My Orders",
        category_hi="मेरे ऑर्डर्स",
        roles=["customer"],
        keywords_hi=["अपडेट", "बदलो"]
    ),
    CommandTemplate(
        command="cancel_order",
        description="Cancel an order",
        description_hi="ऑर्डर कैंसल करें",
        template="cancel order {id}",
        template_hi="ऑर्डर कैंसल करो {id}",
        examples=[
            "cancel order 123",
            "cancel my order 456",
        ],
        examples_hi=[
            "order 123 cancel karo",
            "मेरा ऑर्डर 456 कैंसल करो",
        ],
        category="My Orders",
        category_hi="मेरे ऑर्डर्स",
        roles=["customer"],
        keywords_hi=["कैंसल", "रद्द"]
    ),
]


# Combine all templates
COMMAND_TEMPLATES: List[CommandTemplate] = (
    SUPER_ADMIN_COMMANDS + SHOP_ADMIN_COMMANDS + CUSTOMER_COMMANDS
)


class CommandSuggestionService:
    """Service for providing command suggestions and autocomplete - Bilingual (English + Hindi)"""

    def __init__(self):
        self.templates = COMMAND_TEMPLATES

    def get_suggestions(
        self,
        query: str,
        role: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get command suggestions based on partial query and user role - supports Hindi"""
        query = query.lower().strip()
        suggestions = []

        # Filter by role
        role_templates = [t for t in self.templates if role in t.roles]

        if not query:
            return self._get_popular_commands(role, limit)

        for template in role_templates:
            score = 0

            # English matching
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

            # Hindi matching
            if query in template.description_hi:
                score += 2
            if query in template.template_hi:
                score += 2
            for example_hi in template.examples_hi:
                if query in example_hi.lower():
                    score += 1
                    break
            if query in template.category_hi:
                score += 1
            # Match Hindi keywords
            if template.keywords_hi:
                for keyword in template.keywords_hi:
                    if query in keyword or keyword in query:
                        score += 2
                        break

            if score > 0:
                suggestions.append({
                    "command": template.command,
                    "description": template.description,
                    "description_hi": template.description_hi,
                    "template": template.template,
                    "template_hi": template.template_hi,
                    "examples": template.examples[:2],
                    "examples_hi": template.examples_hi[:2],
                    "category": template.category,
                    "category_hi": template.category_hi,
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
                "description_hi": template.description_hi,
                "template": template.template,
                "template_hi": template.template_hi,
                "examples": template.examples,
                "examples_hi": template.examples_hi,
                "action_type": template.action_type,
            })

        return grouped

    def get_quick_actions(self, role: str) -> List[Dict[str, Any]]:
        """Get quick action buttons based on role - Bilingual"""
        quick_actions = {
            "super_admin": [
                {"label": "Pending Shops", "label_hi": "पेंडिंग दुकानें", "command": "show pending shops", "icon": "clock"},
                {"label": "Platform Stats", "label_hi": "प्लेटफॉर्म स्टैट्स", "command": "show platform stats", "icon": "chart"},
                {"label": "All Shops", "label_hi": "सभी दुकानें", "command": "list shops", "icon": "store"},
                {"label": "All Users", "label_hi": "सभी यूज़र्स", "command": "list users", "icon": "users"},
                {"label": "Add Shop", "label_hi": "दुकान जोड़ो", "command": "add shop ", "icon": "plus"},
                {"label": "Categories", "label_hi": "कैटेगरी", "command": "list shop categories", "icon": "grid"},
            ],
            "admin": [
                {"label": "Dashboard", "label_hi": "डैशबोर्ड", "command": "show dashboard", "icon": "chart"},
                {"label": "Low Stock", "label_hi": "कम स्टॉक", "command": "show low stock", "icon": "alert"},
                {"label": "Pending Orders", "label_hi": "पेंडिंग ऑर्डर", "command": "list pending orders", "icon": "clock"},
                {"label": "All Products", "label_hi": "सभी प्रोडक्ट्स", "command": "list products", "icon": "box"},
                {"label": "All Orders", "label_hi": "सभी ऑर्डर्स", "command": "list orders", "icon": "list"},
                {"label": "Customers", "label_hi": "ग्राहक", "command": "list customers", "icon": "users"},
                {"label": "Today's Profit", "label_hi": "आज का प्रॉफिट", "command": "show today's profit", "icon": "money"},
                {"label": "Sell Product", "label_hi": "बेचो", "command": "sell product ", "icon": "sale"},
            ],
            "customer": [
                {"label": "Browse", "label_hi": "ब्राउज़ करो", "command": "browse categories", "icon": "grid"},
                {"label": "Search", "label_hi": "खोजो", "command": "search ", "icon": "search"},
                {"label": "My Orders", "label_hi": "मेरे ऑर्डर्स", "command": "show my orders", "icon": "list"},
            ],
        }
        return quick_actions.get(role, [])

    def _get_popular_commands(self, role: str, limit: int) -> List[Dict[str, Any]]:
        """Get popular commands for a role - with Hindi support"""
        popular = {
            "super_admin": [
                "get_pending_shops", "get_platform_stats", "list_shops",
                "verify_shop", "list_users", "list_shop_categories"
            ],
            "admin": [
                "get_shop_dashboard", "list_orders", "get_low_stock",
                "list_products", "confirm_order", "get_profit_summary"
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
                        "description_hi": template.description_hi,
                        "template": template.template,
                        "template_hi": template.template_hi,
                        "examples": template.examples[:2],
                        "examples_hi": template.examples_hi[:2],
                        "category": template.category,
                        "category_hi": template.category_hi,
                        "action_type": template.action_type,
                    })
                    break

        return suggestions

    def get_command_help(self, command: str) -> Optional[Dict[str, Any]]:
        """Get detailed help for a specific command - with Hindi support"""
        for template in self.templates:
            if template.command == command:
                return {
                    "command": template.command,
                    "description": template.description,
                    "description_hi": template.description_hi,
                    "template": template.template,
                    "template_hi": template.template_hi,
                    "examples": template.examples,
                    "examples_hi": template.examples_hi,
                    "category": template.category,
                    "category_hi": template.category_hi,
                    "roles": template.roles,
                    "action_type": template.action_type,
                }
        return None
