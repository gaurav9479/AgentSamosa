"""
Seed script to populate the database with comprehensive test data
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
        {"name": "Pharmacy", "icon": "💊", "description": "Medicines, health supplements, and wellness"},
        {"name": "Jewelry", "icon": "💎", "description": "Gold, silver, and fashion jewelry"},
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
        {"name": "Perfumes", "description": "Fragrances and deodorants"},
        # Electronics
        {"name": "Smartphones", "description": "Mobile phones and accessories"},
        {"name": "Laptops", "description": "Notebooks and computers"},
        {"name": "Audio", "description": "Headphones, speakers, and earbuds"},
        {"name": "Accessories", "description": "Cases, chargers, and cables"},
        {"name": "Wearables", "description": "Smartwatches and fitness bands"},
        # Grocery
        {"name": "Fruits & Vegetables", "description": "Fresh produce"},
        {"name": "Dairy", "description": "Milk, cheese, and eggs"},
        {"name": "Snacks", "description": "Chips, cookies, and treats"},
        {"name": "Beverages", "description": "Drinks and juices"},
        {"name": "Staples", "description": "Rice, flour, and pulses"},
        # Fashion
        {"name": "Men's Clothing", "description": "Shirts, pants, and suits"},
        {"name": "Women's Clothing", "description": "Dresses, tops, and bottoms"},
        {"name": "Footwear", "description": "Shoes and sandals"},
        {"name": "Bags", "description": "Handbags and backpacks"},
        # Sports
        {"name": "Gym Equipment", "description": "Weights and machines"},
        {"name": "Sports Gear", "description": "Cricket, football, badminton"},
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
            "owner_phone": "+91 98765 11111",
            "address": "Shop 12, Phoenix Mall, Lower Parel",
            "pincode": "400013",
            "rating": 4.7,
        },
        {
            "name": "TechHub Electronics",
            "description": "Latest gadgets and electronics at best prices",
            "category": "Electronics",
            "city": "Bangalore",
            "owner_name": "Rahul Verma",
            "owner_email": "rahul@techhub.com",
            "owner_phone": "+91 98765 22222",
            "address": "45, Brigade Road",
            "pincode": "560001",
            "rating": 4.5,
        },
        {
            "name": "Fresh Mart Grocery",
            "description": "Farm-fresh produce delivered to your doorstep",
            "category": "Grocery",
            "city": "Delhi",
            "owner_name": "Amit Patel",
            "owner_email": "amit@freshmart.com",
            "owner_phone": "+91 98765 33333",
            "address": "A-12, Connaught Place",
            "pincode": "110001",
            "rating": 4.3,
        },
        {
            "name": "Style Avenue",
            "description": "Trendy fashion for men and women",
            "category": "Fashion",
            "city": "Mumbai",
            "owner_name": "Sneha Reddy",
            "owner_email": "sneha@styleavenue.com",
            "owner_phone": "+91 98765 44444",
            "address": "Plot 78, Linking Road, Bandra",
            "pincode": "400050",
            "rating": 4.6,
        },
        {
            "name": "Glow Skincare",
            "description": "Organic and natural skincare solutions",
            "category": "Beauty & Cosmetics",
            "city": "Pune",
            "owner_name": "Meera Joshi",
            "owner_email": "meera@glowskin.com",
            "owner_phone": "+91 98765 55555",
            "address": "Shop 5, FC Road",
            "pincode": "411004",
            "rating": 4.8,
        },
        {
            "name": "Gadget World",
            "description": "Your one-stop shop for all electronics",
            "category": "Electronics",
            "city": "Chennai",
            "owner_name": "Karthik Nair",
            "owner_email": "karthik@gadgetworld.com",
            "owner_phone": "+91 98765 66666",
            "address": "123, T Nagar",
            "pincode": "600017",
            "rating": 4.4,
        },
        {
            "name": "FitZone Sports",
            "description": "Premium sports and fitness equipment",
            "category": "Sports & Fitness",
            "city": "Hyderabad",
            "owner_name": "Rajesh Kumar",
            "owner_email": "rajesh@fitzone.com",
            "owner_phone": "+91 98765 77777",
            "address": "Plot 34, Jubilee Hills",
            "pincode": "500033",
            "rating": 4.5,
        },
        {
            "name": "BookWorm Store",
            "description": "Books, stationery, and educational supplies",
            "category": "Books & Stationery",
            "city": "Kolkata",
            "owner_name": "Sanjay Das",
            "owner_email": "sanjay@bookworm.com",
            "owner_phone": "+91 98765 88888",
            "address": "College Street",
            "pincode": "700073",
            "rating": 4.6,
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
                owner_phone=shop_data.get("owner_phone"),
                address=shop_data.get("address"),
                pincode=shop_data.get("pincode"),
                rating=shop_data["rating"],
                is_active=True,
                is_verified=True,
                total_orders=random.randint(100, 800),
                total_revenue=random.uniform(50000, 500000),
            )
            db.add(shop)
        await db.commit()
        print(f"✓ Created {len(shops)} shops")

        result = await db.execute(text("SELECT id, name FROM shops"))
        return {row[1]: row[0] for row in result.fetchall()}


async def seed_products(shop_ids, category_ids):
    """Create products for each shop with cost_price and min_price"""

    # Beauty products - cost, price, min_price for bargaining
    beauty_products = [
        {"name": "Ruby Red Lipstick", "brand": "Lakme", "cost": 150, "price": 299, "min": 220, "category": "Lipstick"},
        {"name": "Matte Finish Foundation", "brand": "Maybelline", "cost": 350, "price": 599, "min": 450, "category": "Foundation"},
        {"name": "Vitamin C Serum", "brand": "The Ordinary", "cost": 450, "price": 899, "min": 700, "category": "Skincare"},
        {"name": "Hydrating Moisturizer", "brand": "Neutrogena", "cost": 250, "price": 449, "min": 350, "category": "Skincare"},
        {"name": "Argan Oil Shampoo", "brand": "L'Oreal", "cost": 200, "price": 399, "min": 300, "category": "Haircare"},
        {"name": "Nude Pink Lipstick", "brand": "MAC", "cost": 700, "price": 1299, "min": 999, "category": "Lipstick"},
        {"name": "BB Cream SPF 30", "brand": "Garnier", "cost": 180, "price": 349, "min": 280, "category": "Foundation"},
        {"name": "Retinol Night Cream", "brand": "Olay", "cost": 400, "price": 799, "min": 600, "category": "Skincare"},
        {"name": "Hair Serum Silk", "brand": "Schwarzkopf", "cost": 280, "price": 549, "min": 420, "category": "Haircare"},
        {"name": "Perfume Eau de Toilette", "brand": "Davidoff", "cost": 1200, "price": 2499, "min": 1800, "category": "Perfumes"},
        {"name": "Compact Powder", "brand": "Lakme", "cost": 180, "price": 350, "min": 280, "category": "Foundation"},
        {"name": "Mascara Volume", "brand": "Maybelline", "cost": 220, "price": 449, "min": 350, "category": "Lipstick"},
    ]

    # Electronics products
    electronics_products = [
        {"name": "iPhone 15 Pro", "brand": "Apple", "cost": 110000, "price": 134900, "min": 125000, "category": "Smartphones"},
        {"name": "Samsung Galaxy S24", "brand": "Samsung", "cost": 65000, "price": 79999, "min": 72000, "category": "Smartphones"},
        {"name": "OnePlus 12", "brand": "OnePlus", "cost": 52000, "price": 64999, "min": 58000, "category": "Smartphones"},
        {"name": "MacBook Air M3", "brand": "Apple", "cost": 95000, "price": 114900, "min": 105000, "category": "Laptops"},
        {"name": "Dell XPS 15", "brand": "Dell", "cost": 130000, "price": 154990, "min": 140000, "category": "Laptops"},
        {"name": "HP Pavilion 14", "brand": "HP", "cost": 45000, "price": 59990, "min": 52000, "category": "Laptops"},
        {"name": "AirPods Pro 2", "brand": "Apple", "cost": 18000, "price": 24900, "min": 21000, "category": "Audio"},
        {"name": "Sony WH-1000XM5", "brand": "Sony", "cost": 22000, "price": 29990, "min": 26000, "category": "Audio"},
        {"name": "JBL Flip 6", "brand": "JBL", "cost": 8000, "price": 12999, "min": 10500, "category": "Audio"},
        {"name": "USB-C Hub 7-in-1", "brand": "Anker", "cost": 1500, "price": 2999, "min": 2200, "category": "Accessories"},
        {"name": "65W Fast Charger", "brand": "Samsung", "cost": 1000, "price": 1999, "min": 1500, "category": "Accessories"},
        {"name": "Apple Watch Series 9", "brand": "Apple", "cost": 35000, "price": 44900, "min": 40000, "category": "Wearables"},
        {"name": "Samsung Galaxy Watch 6", "brand": "Samsung", "cost": 22000, "price": 29999, "min": 26000, "category": "Wearables"},
    ]

    # Grocery products
    grocery_products = [
        {"name": "Organic Bananas (1kg)", "brand": "Farm Fresh", "cost": 35, "price": 59, "min": 45, "category": "Fruits & Vegetables"},
        {"name": "Red Apples (1kg)", "brand": "Himachal", "cost": 90, "price": 149, "min": 120, "category": "Fruits & Vegetables"},
        {"name": "Tomatoes (1kg)", "brand": "Local", "cost": 25, "price": 45, "min": 35, "category": "Fruits & Vegetables"},
        {"name": "Onions (1kg)", "brand": "Local", "cost": 20, "price": 40, "min": 30, "category": "Fruits & Vegetables"},
        {"name": "Full Cream Milk (1L)", "brand": "Amul", "cost": 50, "price": 62, "min": 58, "category": "Dairy"},
        {"name": "Greek Yogurt (400g)", "brand": "Epigamia", "cost": 60, "price": 99, "min": 80, "category": "Dairy"},
        {"name": "Paneer (200g)", "brand": "Amul", "cost": 70, "price": 99, "min": 85, "category": "Dairy"},
        {"name": "Butter (100g)", "brand": "Amul", "cost": 40, "price": 56, "min": 50, "category": "Dairy"},
        {"name": "Potato Chips Party Pack", "brand": "Lay's", "cost": 55, "price": 99, "min": 75, "category": "Snacks"},
        {"name": "Dark Chocolate Bar", "brand": "Cadbury", "cost": 90, "price": 149, "min": 120, "category": "Snacks"},
        {"name": "Mixed Nuts (250g)", "brand": "Happilo", "cost": 180, "price": 299, "min": 240, "category": "Snacks"},
        {"name": "Orange Juice (1L)", "brand": "Tropicana", "cost": 75, "price": 120, "min": 100, "category": "Beverages"},
        {"name": "Green Tea (25 bags)", "brand": "Lipton", "cost": 100, "price": 175, "min": 140, "category": "Beverages"},
        {"name": "Basmati Rice (5kg)", "brand": "India Gate", "cost": 400, "price": 599, "min": 500, "category": "Staples"},
        {"name": "Toor Dal (1kg)", "brand": "Tata", "cost": 120, "price": 169, "min": 145, "category": "Staples"},
    ]

    # Fashion products
    fashion_products = [
        {"name": "Slim Fit Cotton Shirt", "brand": "Van Heusen", "cost": 800, "price": 1499, "min": 1100, "category": "Men's Clothing"},
        {"name": "Chino Pants", "brand": "Allen Solly", "cost": 1100, "price": 1999, "min": 1500, "category": "Men's Clothing"},
        {"name": "Formal Blazer", "brand": "Raymond", "cost": 3500, "price": 5999, "min": 4800, "category": "Men's Clothing"},
        {"name": "Polo T-Shirt", "brand": "US Polo", "cost": 600, "price": 1099, "min": 850, "category": "Men's Clothing"},
        {"name": "Floral Summer Dress", "brand": "Zara", "cost": 1600, "price": 2999, "min": 2300, "category": "Women's Clothing"},
        {"name": "High-Waist Jeans", "brand": "Levi's", "cost": 1400, "price": 2499, "min": 1900, "category": "Women's Clothing"},
        {"name": "Cotton Kurti", "brand": "W", "cost": 500, "price": 899, "min": 700, "category": "Women's Clothing"},
        {"name": "Maxi Skirt", "brand": "Only", "cost": 800, "price": 1499, "min": 1100, "category": "Women's Clothing"},
        {"name": "Running Shoes", "brand": "Nike", "cost": 4500, "price": 6999, "min": 5800, "category": "Footwear"},
        {"name": "Leather Loafers", "brand": "Clarks", "cost": 3500, "price": 5999, "min": 4800, "category": "Footwear"},
        {"name": "Sneakers Classic", "brand": "Adidas", "cost": 3000, "price": 4999, "min": 4000, "category": "Footwear"},
        {"name": "Laptop Backpack", "brand": "Wildcraft", "cost": 800, "price": 1499, "min": 1100, "category": "Bags"},
        {"name": "Women's Handbag", "brand": "Lavie", "cost": 1200, "price": 2199, "min": 1700, "category": "Bags"},
    ]

    # Sports products
    sports_products = [
        {"name": "Yoga Mat Premium", "brand": "Decathlon", "cost": 400, "price": 799, "min": 600, "category": "Gym Equipment"},
        {"name": "Dumbbell Set 10kg", "brand": "Kore", "cost": 1200, "price": 1999, "min": 1600, "category": "Gym Equipment"},
        {"name": "Resistance Bands Set", "brand": "Boldfit", "cost": 300, "price": 599, "min": 450, "category": "Gym Equipment"},
        {"name": "Cricket Bat English Willow", "brand": "SG", "cost": 3000, "price": 4999, "min": 4000, "category": "Sports Gear"},
        {"name": "Football Official Size", "brand": "Nivia", "cost": 500, "price": 899, "min": 700, "category": "Sports Gear"},
        {"name": "Badminton Racket", "brand": "Yonex", "cost": 1500, "price": 2499, "min": 2000, "category": "Sports Gear"},
        {"name": "Tennis Balls (3 pack)", "brand": "Wilson", "cost": 200, "price": 399, "min": 300, "category": "Sports Gear"},
        {"name": "Gym Gloves", "brand": "Nivia", "cost": 200, "price": 399, "min": 300, "category": "Gym Equipment"},
    ]

    # Assign products to shops
    shop_products = {
        "Glamour Beauty Store": beauty_products[:8],
        "Glow Skincare": beauty_products[4:],
        "TechHub Electronics": electronics_products[:8],
        "Gadget World": electronics_products[5:],
        "Fresh Mart Grocery": grocery_products,
        "Style Avenue": fashion_products,
        "FitZone Sports": sports_products,
    }

    total_products = 0
    async with async_session() as db:
        for shop_name, products in shop_products.items():
            shop_id = shop_ids.get(shop_name)
            if not shop_id:
                continue

            for i, prod in enumerate(products):
                product = Product(
                    name=prod["name"],
                    brand=prod["brand"],
                    price=prod["price"],
                    cost_price=prod["cost"],
                    min_price=prod.get("min"),
                    compare_at_price=prod["price"] * 1.2 if random.random() > 0.5 else None,
                    quantity=random.randint(20, 150),
                    min_stock_level=10,
                    shop_id=shop_id,
                    category_id=category_ids.get(prod["category"]),
                    sku=f"{shop_id}-{prod['category'][:3].upper()}{i+1:03d}",
                    sold_count=random.randint(10, 100),
                    view_count=random.randint(100, 1000),
                    is_active=True,
                    is_featured=random.random() > 0.7,
                    unit="piece" if prod["category"] not in ["Fruits & Vegetables", "Dairy", "Staples"] else "kg",
                )
                db.add(product)
                total_products += 1

        await db.commit()
        print(f"✓ Created {total_products} products across shops")

        # Return product info for orders
        result = await db.execute(text("SELECT id, name, price, cost_price, shop_id FROM products"))
        return [(row[0], row[1], row[2], row[3], row[4]) for row in result.fetchall()]


async def seed_customers():
    """Create test customers"""
    customers = [
        {"name": "Ananya Gupta", "email": "ananya@email.com", "phone": "+91 98765 43210", "address": "123 MG Road, Mumbai 400001"},
        {"name": "Vikram Singh", "email": "vikram@email.com", "phone": "+91 87654 32109", "address": "456 Brigade Road, Bangalore 560001"},
        {"name": "Deepika Menon", "email": "deepika@email.com", "phone": "+91 76543 21098", "address": "789 Park Street, Kolkata 700016"},
        {"name": "Arjun Kapoor", "email": "arjun@email.com", "phone": "+91 65432 10987", "address": "321 Anna Salai, Chennai 600002"},
        {"name": "Kavya Nair", "email": "kavya@email.com", "phone": "+91 54321 09876", "address": "654 FC Road, Pune 411004"},
        {"name": "Rohan Mehta", "email": "rohan@email.com", "phone": "+91 43210 98765", "address": "987 Sector 17, Chandigarh 160017"},
        {"name": "Ishita Sharma", "email": "ishita@email.com", "phone": "+91 32109 87654", "address": "159 Hazratganj, Lucknow 226001"},
        {"name": "Aditya Rao", "email": "aditya@email.com", "phone": "+91 21098 76543", "address": "753 Jubilee Hills, Hyderabad 500033"},
        {"name": "Priya Menon", "email": "priyam@email.com", "phone": "+91 91234 56789", "address": "45 Marine Drive, Mumbai 400002"},
        {"name": "Karan Malhotra", "email": "karan@email.com", "phone": "+91 81234 56789", "address": "78 Indiranagar, Bangalore 560038"},
        {"name": "Neha Verma", "email": "neha@email.com", "phone": "+91 71234 56789", "address": "23 Salt Lake, Kolkata 700091"},
        {"name": "Siddharth Iyer", "email": "sid@email.com", "phone": "+91 61234 56789", "address": "56 Mylapore, Chennai 600004"},
    ]

    async with async_session() as db:
        for cust in customers:
            customer = Customer(
                name=cust["name"],
                email=cust["email"],
                phone=cust["phone"],
                address=cust["address"],
                total_orders=random.randint(5, 50),
                total_spent=random.uniform(2000, 100000),
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
        {"name": "Platform Admin", "email": "superadmin@kommandai.com", "role": "super_admin", "shop_id": None},
        # Shop Owners (Admins)
        {"name": "Priya Sharma", "email": "admin@kommandai.com", "role": "admin", "shop_id": shop_ids.get("Glamour Beauty Store")},
        {"name": "Rahul Verma", "email": "rahul@techhub.com", "role": "admin", "shop_id": shop_ids.get("TechHub Electronics")},
        {"name": "Amit Patel", "email": "amit@freshmart.com", "role": "admin", "shop_id": shop_ids.get("Fresh Mart Grocery")},
        {"name": "Sneha Reddy", "email": "sneha@styleavenue.com", "role": "admin", "shop_id": shop_ids.get("Style Avenue")},
        {"name": "Meera Joshi", "email": "meera@glowskin.com", "role": "admin", "shop_id": shop_ids.get("Glow Skincare")},
        {"name": "Karthik Nair", "email": "karthik@gadgetworld.com", "role": "admin", "shop_id": shop_ids.get("Gadget World")},
        {"name": "Rajesh Kumar", "email": "rajesh@fitzone.com", "role": "admin", "shop_id": shop_ids.get("FitZone Sports")},
        # Customers
        {"name": "Test Customer", "email": "customer@kommandai.com", "role": "customer", "shop_id": None},
        {"name": "Ananya Gupta", "email": "ananya@email.com", "role": "customer", "shop_id": None},
        {"name": "Vikram Singh", "email": "vikram@email.com", "role": "customer", "shop_id": None},
        {"name": "Deepika Menon", "email": "deepika@email.com", "role": "customer", "shop_id": None},
        {"name": "Arjun Kapoor", "email": "arjun@email.com", "role": "customer", "shop_id": None},
        {"name": "Kavya Nair", "email": "kavya@email.com", "role": "customer", "shop_id": None},
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


async def seed_orders(products_data, customer_ids):
    """Create sample orders with profit tracking"""
    statuses = ["pending", "confirmed", "shipped", "delivered"]

    async with async_session() as db:
        customer_list = list(customer_ids.items())
        order_count = 0

        for _ in range(150):  # Create 150 orders
            product = random.choice(products_data)
            product_id, product_name, price, cost_price, shop_id = product
            customer = random.choice(customer_list)
            qty = random.randint(1, 5)

            # Simulate bargaining - sometimes sell at discount
            bargain_discount = random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2])  # 60% at MRP, 40% bargained
            final_price = price * (1 - bargain_discount)

            # Calculate profit fields
            cost = cost_price or (price * 0.6)  # Assume 40% margin if no cost
            total_amount = final_price * qty
            total_cost = cost * qty
            profit = total_amount - total_cost
            discount_given = (price - final_price) * qty

            order = Order(
                shop_id=shop_id,
                product_id=product_id,
                product_name=product_name,
                quantity=qty,
                cost_price=cost,
                listed_price=price,
                final_price=final_price,
                unit_price=final_price,
                total_amount=total_amount,
                total_cost=total_cost,
                profit=profit,
                discount_given=discount_given,
                status=random.choice(statuses),
                customer_id=customer[1],
                customer_name=customer[0],
                customer_email=f"{customer[0].lower().replace(' ', '.')}@email.com",
                customer_phone=f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
                created_at=datetime.now() - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23)),
            )
            db.add(order)
            order_count += 1

        await db.commit()
        print(f"✓ Created {order_count} orders with profit tracking")


async def main():
    print("\n🌱 Seeding KommandAI Database with Comprehensive Data...\n")

    # Initialize tables if they don't exist
    await init_db()
    print("✓ Database tables initialized")

    # Clear existing data
    await clear_data()

    # Seed in order (respecting foreign keys)
    shop_category_ids = await seed_shop_categories()
    product_category_ids = await seed_product_categories()
    shop_ids = await seed_shops(shop_category_ids)
    products_data = await seed_products(shop_ids, product_category_ids)
    customer_ids = await seed_customers()
    await seed_users(shop_ids)
    await seed_orders(products_data, customer_ids)

    print("\n" + "="*60)
    print("✅ Database seeded successfully!")
    print("="*60)
    print("\n📊 Data Summary:")
    print(f"   • 10 Shop Categories")
    print(f"   • 21 Product Categories")
    print(f"   • 8 Shops (all verified)")
    print(f"   • 70+ Products with cost & min prices")
    print(f"   • 12 Customers")
    print(f"   • 14 Users (1 Super Admin, 7 Shop Admins, 6 Customers)")
    print(f"   • 150 Orders with profit tracking")
    print()
    print("🔐 Demo Accounts (password: qwert12345):")
    print("   ┌─────────────┬──────────────────────────────┐")
    print("   │ Role        │ Email                        │")
    print("   ├─────────────┼──────────────────────────────┤")
    print("   │ Super Admin │ superadmin@kommandai.com     │")
    print("   │ Shop Admin  │ admin@kommandai.com          │")
    print("   │ Customer    │ customer@kommandai.com       │")
    print("   └─────────────┴──────────────────────────────┘")
    print()


if __name__ == "__main__":
    asyncio.run(main())
