"""
Seed script to populate the database with test data
Run with: ./venv/bin/python seed_data.py
"""
import asyncio
import hashlib
from datetime import datetime, timedelta
import random

from sqlalchemy import text
from app.core.database import async_session, init_db
from app.models import (
    User, UserRole, Shop, ShopCategory, Product, Category, Order, Customer, ActionLog
)


def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


async def clear_data():
    """Clear existing data"""
    async with async_session() as db:
        # Delete in order to respect foreign keys
        await db.execute(text("DELETE FROM action_logs"))
        await db.execute(text("DELETE FROM orders"))
        await db.execute(text("DELETE FROM products"))
        await db.execute(text("DELETE FROM categories"))
        await db.execute(text("DELETE FROM users"))
        await db.execute(text("DELETE FROM shops"))
        await db.execute(text("DELETE FROM shop_categories"))
        await db.execute(text("DELETE FROM customers"))
        await db.commit()
        print("✓ Cleared existing data")


async def seed_shop_categories():
    """Create shop categories (types of shops)"""
    categories = [
        {"name": "Beauty & Cosmetics", "icon": "💄", "description": "Makeup, skincare, and beauty products"},
        {"name": "Grocery", "icon": "🛒", "description": "Fresh produce, pantry staples, and household items"},
        {"name": "Electronics", "icon": "📱", "description": "Phones, laptops, gadgets, and accessories"},
        {"name": "Fashion", "icon": "👗", "description": "Clothing, shoes, and accessories"},
        {"name": "Home & Living", "icon": "🏠", "description": "Furniture, decor, and home essentials"},
        {"name": "Sports & Fitness", "icon": "⚽", "description": "Sports equipment and fitness gear"},
        {"name": "Books & Stationery", "icon": "📚", "description": "Books, office supplies, and art materials"},
        {"name": "Food & Beverages", "icon": "🍕", "description": "Restaurants, cafes, and food delivery"},
    ]

    async with async_session() as db:
        for i, cat in enumerate(categories):
            shop_cat = ShopCategory(
                name=cat["name"],
                icon=cat["icon"],
                description=cat["description"],
                sort_order=i,
                is_active=True
            )
            db.add(shop_cat)
        await db.commit()
        print(f"✓ Created {len(categories)} shop categories")

        # Return IDs for reference
        result = await db.execute(text("SELECT id, name FROM shop_categories"))
        return {row[1]: row[0] for row in result.fetchall()}


async def seed_product_categories():
    """Create product categories"""
    categories = [
        # Beauty
        {"name": "Lipstick", "description": "Lip colors and glosses"},
        {"name": "Foundation", "description": "Base makeup products"},
        {"name": "Skincare", "description": "Moisturizers, serums, and treatments"},
        {"name": "Haircare", "description": "Shampoos, conditioners, and styling"},
        # Electronics
        {"name": "Smartphones", "description": "Mobile phones and accessories"},
        {"name": "Laptops", "description": "Notebooks and computers"},
        {"name": "Audio", "description": "Headphones, speakers, and earbuds"},
        {"name": "Accessories", "description": "Cases, chargers, and cables"},
        # Grocery
        {"name": "Fruits & Vegetables", "description": "Fresh produce"},
        {"name": "Dairy", "description": "Milk, cheese, and eggs"},
        {"name": "Snacks", "description": "Chips, cookies, and treats"},
        {"name": "Beverages", "description": "Drinks and juices"},
        # Fashion
        {"name": "Men's Clothing", "description": "Shirts, pants, and suits"},
        {"name": "Women's Clothing", "description": "Dresses, tops, and bottoms"},
        {"name": "Footwear", "description": "Shoes and sandals"},
    ]

    async with async_session() as db:
        for cat in categories:
            product_cat = Category(
                name=cat["name"],
                description=cat["description"],
                is_active=True
            )
            db.add(product_cat)
        await db.commit()
        print(f"✓ Created {len(categories)} product categories")

        result = await db.execute(text("SELECT id, name FROM categories"))
        return {row[1]: row[0] for row in result.fetchall()}


async def seed_shops(shop_category_ids):
    """Create shops"""
    shops = [
        {
            "name": "Glamour Beauty Store",
            "description": "Premium beauty and cosmetics for the modern woman",
            "category": "Beauty & Cosmetics",
            "city": "Mumbai",
            "owner_name": "Priya Sharma",
            "owner_email": "priya@glamourbeauty.com",
            "rating": 4.7,
        },
        {
            "name": "TechHub Electronics",
            "description": "Latest gadgets and electronics at best prices",
            "category": "Electronics",
            "city": "Bangalore",
            "owner_name": "Rahul Verma",
            "owner_email": "rahul@techhub.com",
            "rating": 4.5,
        },
        {
            "name": "Fresh Mart Grocery",
            "description": "Farm-fresh produce delivered to your doorstep",
            "category": "Grocery",
            "city": "Delhi",
            "owner_name": "Amit Patel",
            "owner_email": "amit@freshmart.com",
            "rating": 4.3,
        },
        {
            "name": "Style Avenue",
            "description": "Trendy fashion for men and women",
            "category": "Fashion",
            "city": "Mumbai",
            "owner_name": "Sneha Reddy",
            "owner_email": "sneha@styleavenue.com",
            "rating": 4.6,
        },
        {
            "name": "Glow Skincare",
            "description": "Organic and natural skincare solutions",
            "category": "Beauty & Cosmetics",
            "city": "Pune",
            "owner_name": "Meera Joshi",
            "owner_email": "meera@glowskin.com",
            "rating": 4.8,
        },
        {
            "name": "Gadget World",
            "description": "Your one-stop shop for all electronics",
            "category": "Electronics",
            "city": "Chennai",
            "owner_name": "Karthik Nair",
            "owner_email": "karthik@gadgetworld.com",
            "rating": 4.4,
        },
    ]

    shop_ids = {}
    async with async_session() as db:
        for shop_data in shops:
            shop = Shop(
                name=shop_data["name"],
                description=shop_data["description"],
                category_id=shop_category_ids.get(shop_data["category"]),
                city=shop_data["city"],
                owner_name=shop_data["owner_name"],
                owner_email=shop_data["owner_email"],
                rating=shop_data["rating"],
                is_active=True,
                is_verified=True,
                total_orders=random.randint(50, 500),
                total_revenue=random.uniform(10000, 100000),
            )
            db.add(shop)
        await db.commit()
        print(f"✓ Created {len(shops)} shops")

        result = await db.execute(text("SELECT id, name FROM shops"))
        return {row[1]: row[0] for row in result.fetchall()}


async def seed_products(shop_ids, category_ids):
    """Create products for each shop"""

    # Beauty products
    beauty_products = [
        {"name": "Ruby Red Lipstick", "brand": "Lakme", "price": 299, "cost": 150, "category": "Lipstick", "sku": "LIP001"},
        {"name": "Matte Finish Foundation", "brand": "Maybelline", "price": 599, "cost": 350, "category": "Foundation", "sku": "FND001"},
        {"name": "Vitamin C Serum", "brand": "The Ordinary", "price": 899, "cost": 450, "category": "Skincare", "sku": "SKN001"},
        {"name": "Hydrating Moisturizer", "brand": "Neutrogena", "price": 449, "cost": 250, "category": "Skincare", "sku": "SKN002"},
        {"name": "Argan Oil Shampoo", "brand": "L'Oreal", "price": 399, "cost": 200, "category": "Haircare", "sku": "HAR001"},
        {"name": "Nude Pink Lipstick", "brand": "MAC", "price": 1299, "cost": 700, "category": "Lipstick", "sku": "LIP002"},
        {"name": "BB Cream SPF 30", "brand": "Garnier", "price": 349, "cost": 180, "category": "Foundation", "sku": "FND002"},
        {"name": "Retinol Night Cream", "brand": "Olay", "price": 799, "cost": 400, "category": "Skincare", "sku": "SKN003"},
    ]

    # Electronics products
    electronics_products = [
        {"name": "iPhone 15 Pro", "brand": "Apple", "price": 134900, "cost": 110000, "category": "Smartphones", "sku": "PHN001"},
        {"name": "Samsung Galaxy S24", "brand": "Samsung", "price": 79999, "cost": 65000, "category": "Smartphones", "sku": "PHN002"},
        {"name": "MacBook Air M3", "brand": "Apple", "price": 114900, "cost": 95000, "category": "Laptops", "sku": "LAP001"},
        {"name": "Dell XPS 15", "brand": "Dell", "price": 154990, "cost": 130000, "category": "Laptops", "sku": "LAP002"},
        {"name": "AirPods Pro 2", "brand": "Apple", "price": 24900, "cost": 18000, "category": "Audio", "sku": "AUD001"},
        {"name": "Sony WH-1000XM5", "brand": "Sony", "price": 29990, "cost": 22000, "category": "Audio", "sku": "AUD002"},
        {"name": "USB-C Hub 7-in-1", "brand": "Anker", "price": 2999, "cost": 1500, "category": "Accessories", "sku": "ACC001"},
        {"name": "65W Fast Charger", "brand": "Samsung", "price": 1999, "cost": 1000, "category": "Accessories", "sku": "ACC002"},
    ]

    # Grocery products
    grocery_products = [
        {"name": "Organic Bananas (1kg)", "brand": "Farm Fresh", "price": 59, "cost": 35, "category": "Fruits & Vegetables", "sku": "FRU001"},
        {"name": "Red Apples (1kg)", "brand": "Himachal", "price": 149, "cost": 90, "category": "Fruits & Vegetables", "sku": "FRU002"},
        {"name": "Full Cream Milk (1L)", "brand": "Amul", "price": 62, "cost": 50, "category": "Dairy", "sku": "DAI001"},
        {"name": "Greek Yogurt (400g)", "brand": "Epigamia", "price": 99, "cost": 60, "category": "Dairy", "sku": "DAI002"},
        {"name": "Potato Chips Party Pack", "brand": "Lay's", "price": 99, "cost": 55, "category": "Snacks", "sku": "SNK001"},
        {"name": "Dark Chocolate Bar", "brand": "Cadbury", "price": 149, "cost": 90, "category": "Snacks", "sku": "SNK002"},
        {"name": "Orange Juice (1L)", "brand": "Tropicana", "price": 120, "cost": 75, "category": "Beverages", "sku": "BEV001"},
        {"name": "Green Tea (25 bags)", "brand": "Lipton", "price": 175, "cost": 100, "category": "Beverages", "sku": "BEV002"},
    ]

    # Fashion products
    fashion_products = [
        {"name": "Slim Fit Cotton Shirt", "brand": "Van Heusen", "price": 1499, "cost": 800, "category": "Men's Clothing", "sku": "MEN001"},
        {"name": "Chino Pants", "brand": "Allen Solly", "price": 1999, "cost": 1100, "category": "Men's Clothing", "sku": "MEN002"},
        {"name": "Floral Summer Dress", "brand": "Zara", "price": 2999, "cost": 1600, "category": "Women's Clothing", "sku": "WOM001"},
        {"name": "High-Waist Jeans", "brand": "Levi's", "price": 2499, "cost": 1400, "category": "Women's Clothing", "sku": "WOM002"},
        {"name": "Running Shoes", "brand": "Nike", "price": 6999, "cost": 4500, "category": "Footwear", "sku": "SHO001"},
        {"name": "Leather Loafers", "brand": "Clarks", "price": 5999, "cost": 3500, "category": "Footwear", "sku": "SHO002"},
    ]

    # Assign products to shops
    shop_products = {
        "Glamour Beauty Store": beauty_products[:5],
        "Glow Skincare": beauty_products[3:],
        "TechHub Electronics": electronics_products[:5],
        "Gadget World": electronics_products[3:],
        "Fresh Mart Grocery": grocery_products,
        "Style Avenue": fashion_products,
    }

    total_products = 0
    async with async_session() as db:
        for shop_name, products in shop_products.items():
            shop_id = shop_ids.get(shop_name)
            if not shop_id:
                continue

            for prod in products:
                product = Product(
                    name=prod["name"],
                    brand=prod["brand"],
                    price=prod["price"],
                    cost_price=prod["cost"],
                    compare_at_price=prod["price"] * 1.2 if random.random() > 0.5 else None,
                    quantity=random.randint(10, 100),
                    min_stock_level=5,
                    shop_id=shop_id,
                    category_id=category_ids.get(prod["category"]),
                    sku=f"{shop_id}-{prod['sku']}",
                    sold_count=random.randint(5, 50),
                    view_count=random.randint(50, 500),
                    is_active=True,
                    is_featured=random.random() > 0.7,
                    unit="piece" if prod["category"] not in ["Fruits & Vegetables", "Dairy"] else "kg",
                )
                db.add(product)
                total_products += 1

        await db.commit()
        print(f"✓ Created {total_products} products across shops")


async def seed_customers():
    """Create test customers"""
    customers = [
        {"name": "Ananya Gupta", "email": "ananya@email.com", "phone": "+91 98765 43210", "address": "123 MG Road, Mumbai"},
        {"name": "Vikram Singh", "email": "vikram@email.com", "phone": "+91 87654 32109", "address": "456 Brigade Road, Bangalore"},
        {"name": "Deepika Menon", "email": "deepika@email.com", "phone": "+91 76543 21098", "address": "789 Park Street, Kolkata"},
        {"name": "Arjun Kapoor", "email": "arjun@email.com", "phone": "+91 65432 10987", "address": "321 Anna Salai, Chennai"},
        {"name": "Kavya Nair", "email": "kavya@email.com", "phone": "+91 54321 09876", "address": "654 FC Road, Pune"},
        {"name": "Rohan Mehta", "email": "rohan@email.com", "phone": "+91 43210 98765", "address": "987 Sector 17, Chandigarh"},
        {"name": "Ishita Sharma", "email": "ishita@email.com", "phone": "+91 32109 87654", "address": "159 Hazratganj, Lucknow"},
        {"name": "Aditya Rao", "email": "aditya@email.com", "phone": "+91 21098 76543", "address": "753 Jubilee Hills, Hyderabad"},
    ]

    async with async_session() as db:
        for cust in customers:
            customer = Customer(
                name=cust["name"],
                email=cust["email"],
                phone=cust["phone"],
                address=cust["address"],
                total_orders=random.randint(1, 20),
                total_spent=random.uniform(500, 50000),
                is_active=True,
            )
            db.add(customer)
        await db.commit()
        print(f"✓ Created {len(customers)} customers")

        result = await db.execute(text("SELECT id, name FROM customers"))
        return {row[1]: row[0] for row in result.fetchall()}


async def seed_users(shop_ids):
    """Create user accounts"""
    password_hash = hash_password("qwert12345")

    users = [
        # Super Admin
        {"name": "Platform Admin", "email": "superadmin@agentsamosa.com", "role": "super_admin", "shop_id": None},
        # Shop Owners (Admins)
        {"name": "Priya Sharma", "email": "admin@agentsamosa.com", "role": "admin", "shop_id": shop_ids.get("Glamour Beauty Store")},
        {"name": "Rahul Verma", "email": "rahul@techhub.com", "role": "admin", "shop_id": shop_ids.get("TechHub Electronics")},
        {"name": "Amit Patel", "email": "amit@freshmart.com", "role": "admin", "shop_id": shop_ids.get("Fresh Mart Grocery")},
        {"name": "Sneha Reddy", "email": "sneha@styleavenue.com", "role": "admin", "shop_id": shop_ids.get("Style Avenue")},
        # Customers
        {"name": "Test Customer", "email": "customer@agentsamosa.com", "role": "customer", "shop_id": None},
        {"name": "Ananya Gupta", "email": "ananya@email.com", "role": "customer", "shop_id": None},
        {"name": "Vikram Singh", "email": "vikram@email.com", "role": "customer", "shop_id": None},
    ]

    async with async_session() as db:
        for u in users:
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=password_hash,
                role=u["role"],
                shop_id=u["shop_id"],
                is_active=True,
                is_verified=True,
            )
            db.add(user)
        await db.commit()
        print(f"✓ Created {len(users)} users")


async def seed_orders(shop_ids, customer_ids):
    """Create sample orders"""
    statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

    async with async_session() as db:
        # Get products
        result = await db.execute(text("SELECT id, name, price, shop_id FROM products"))
        products = result.fetchall()

        customer_list = list(customer_ids.items())
        order_count = 0

        for _ in range(50):  # Create 50 orders
            product = random.choice(products)
            customer = random.choice(customer_list)
            qty = random.randint(1, 5)

            order = Order(
                shop_id=product[3],
                product_id=product[0],
                product_name=product[1],
                unit_price=product[2],
                quantity=qty,
                total_amount=product[2] * qty,
                status=random.choice(statuses),
                customer_id=customer[1],
                customer_name=customer[0],
                customer_email=f"{customer[0].lower().replace(' ', '.')}@email.com",
                created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
            )
            db.add(order)
            order_count += 1

        await db.commit()
        print(f"✓ Created {order_count} orders")


async def main():
    print("\n🌱 Seeding AgentSamosa Database...\n")

    # Initialize tables if they don't exist
    await init_db()
    print("✓ Database tables initialized")

    # Clear existing data
    await clear_data()

    # Seed in order (respecting foreign keys)
    shop_category_ids = await seed_shop_categories()
    product_category_ids = await seed_product_categories()
    shop_ids = await seed_shops(shop_category_ids)
    await seed_products(shop_ids, product_category_ids)
    customer_ids = await seed_customers()
    await seed_users(shop_ids)
    await seed_orders(shop_ids, customer_ids)

    print("\n✅ Database seeded successfully!\n")
    print("Demo accounts (password: qwert12345):")
    print("  • Super Admin: superadmin@agentsamosa.com")
    print("  • Shop Admin:  admin@agentsamosa.com")
    print("  • Customer:    customer@agentsamosa.com")
    print()


if __name__ == "__main__":
    asyncio.run(main())
