# KommandAI Command Guide

This guide explains all the AI-powered commands available in KommandAI, organized by user role.

---

## Table of Contents

1. [Overview](#overview)
2. [Super Admin Commands](#super-admin-commands)
3. [Shop Admin Commands](#shop-admin-commands)
4. [Customer Commands](#customer-commands)
5. [Quick Actions](#quick-actions)
6. [Tips for Better Commands](#tips-for-better-commands)

---

## Overview

KommandAI features an AI-powered natural language command system. Simply type what you want to do in plain English, and the system will understand and execute your request.

### How It Works

1. **Type your command** in the command input box
2. **Use quick action buttons** for common tasks
3. **Get suggestions** as you type (autocomplete)
4. **Press Enter** or click "Go" to execute

### Command Input Features

- **Autocomplete**: Start typing and see matching commands
- **Quick Actions**: One-click buttons for common tasks
- **Keyboard Navigation**: Use arrow keys to navigate suggestions
- **Natural Language**: Commands don't need exact syntax

---

## Super Admin Commands

As a Super Admin, you manage the entire platform including shops, users, and categories.

### Shop Management

| Task | Example Commands |
|------|------------------|
| **Register a new shop** | `add shop "Tech Hub" owner "John Doe" email john@test.com city "Mumbai"` |
| | `register shop "Beauty Palace" owner "Jane Smith"` |
| | `create shop "Fresh Mart" in category 3` |
| **Verify a pending shop** | `verify shop 5` |
| | `approve shop "Tech Hub"` |
| | `verify pending shop 8` |
| **Suspend a shop** | `suspend shop 5` |
| | `suspend shop "Bad Store"` |
| **Activate a suspended shop** | `activate shop 5` |
| | `reactivate shop 12` |
| **View pending shops** | `show pending shops` |
| | `list shops waiting for approval` |
| | `pending verifications` |
| **List all shops** | `list shops` |
| | `show all shops` |
| | `list shops in Mumbai` |
| | `show verified shops` |
| **View shop details** | `show shop 5` |
| | `get shop "Tech Hub" stats` |
| | `view shop 12 details` |

> **Note**: When you use "add shop" or "create shop", the system will **pre-fill the registration form** with your provided details. You can then review, complete any missing fields, and submit.

### Platform Statistics

| Task | Example Commands |
|------|------------------|
| **View platform stats** | `show platform stats` |
| | `platform overview` |
| | `show dashboard` |

### User Management

| Task | Example Commands |
|------|------------------|
| **List all users** | `list users` |
| | `show all users` |
| | `list admin users` |
| | `show customers` |
| **View user details** | `show user 5` |
| | `get user "john@test.com"` |

### Category Management

| Task | Example Commands |
|------|------------------|
| **List shop categories** | `list shop categories` |
| | `show business types` |
| **Create a category** | `create category "Electronics"` |
| | `add shop category "Pharmacy" description "Medical stores"` |

---

## Shop Admin Commands

As a Shop Admin, you manage your shop's products, orders, and customers.

### Dashboard

| Task | Example Commands |
|------|------------------|
| **View your dashboard** | `show dashboard` |
| | `my shop stats` |
| | `shop overview` |

### Product Management

| Task | Example Commands |
|------|------------------|
| **Create a product** | `create product "iPhone 15" price 999.99 quantity 50` |
| | `add product "Shampoo" at 29.99 with 100 in stock` |
| | `new product "Blue T-Shirt" price 19.99 quantity 200` |
| **Update a product** | `update product 5 price 89.99` |
| | `update product 12 quantity 100` |
| | `change product 8 name "Premium Widget"` |
| **Restock a product** | `restock product 5 add 100` |
| | `add 50 units to product 12` |
| | `increase stock of product 8 by 200` |
| **Change product price** | `set price of product 5 to 49.99` |
| | `change price of product 12 to 29.99` |
| **List all products** | `list products` |
| | `show all products` |
| | `list products in category 3` |
| **View low stock items** | `show low stock products` |
| | `what needs restocking` |
| | `low inventory` |
| **Delete a product** | `delete product 5` |
| | `remove product 12` |

### Order Management

| Task | Example Commands |
|------|------------------|
| **List all orders** | `list orders` |
| | `show all orders` |
| | `list pending orders` |
| | `show today's orders` |
| **View order details** | `show order 123` |
| | `order details 456` |
| **Confirm an order** | `confirm order 123` |
| | `approve order 456` |
| **Ship an order** | `ship order 123` |
| | `mark order 456 as shipped` |
| | `ship order 789 tracking "TRK123456"` |
| **Mark as delivered** | `deliver order 123` |
| | `mark order 456 as delivered` |
| | `complete order 789` |
| **Cancel an order** | `cancel order 123` |

### Customer Management

| Task | Example Commands |
|------|------------------|
| **List customers** | `list customers` |
| | `show all customers` |
| **Search customers** | `search customers "john"` |
| | `find customer "jane@test.com"` |

---

## Customer Commands

As a Customer, you can browse products, place orders, and manage your orders.

### Browsing & Search

| Task | Example Commands |
|------|------------------|
| **Browse categories** | `browse categories` |
| | `show shop categories` |
| | `what can I shop for` |
| **Browse shops** | `browse shops` |
| | `show shops in Beauty` |
| | `find shops in Mumbai` |
| **Search products** | `search "phone"` |
| | `find "organic shampoo"` |
| | `search for "laptop"` |

### Order Management

| Task | Example Commands |
|------|------------------|
| **Place an order** | `order product 5 quantity 2` |
| | `buy 3 of product 12` |
| | `place order for product 8` |
| **View my orders** | `show my orders` |
| | `my order history` |
| | `list my orders` |
| **Track an order** | `track order 123` |
| | `where is my order 456` |
| | `order status 789` |
| **Update order quantity** | `update order 123 quantity 5` |
| | `change order 456 to 3 items` |
| **Cancel an order** | `cancel order 123` |
| | `cancel my order 456` |

---

## Quick Actions

Each role has quick action buttons for common tasks. Click them to instantly execute or start typing a command.

### Super Admin Quick Actions

| Button | Action |
|--------|--------|
| **Pending Shops** | View shops awaiting verification |
| **Platform Stats** | View platform-wide statistics |
| **All Shops** | List all registered shops |
| **All Users** | List all platform users |
| **Add Shop** | Start registering a new shop |
| **Categories** | View shop categories |

### Shop Admin Quick Actions

| Button | Action |
|--------|--------|
| **Dashboard** | View your shop's dashboard |
| **Low Stock** | View products running low |
| **Pending Orders** | View orders awaiting confirmation |
| **All Products** | List all your products |
| **All Orders** | View all orders |
| **Customers** | List your customers |

### Customer Quick Actions

| Button | Action |
|--------|--------|
| **Browse** | Browse shop categories |
| **Search** | Search for products |
| **My Orders** | View your order history |

---

## Tips for Better Commands

### Be Specific
Instead of: `update product`
Try: `update product 5 price 49.99`

### Use Natural Language
You don't need exact syntax. These all work:
- `verify shop 5`
- `approve shop 5`
- `approve shop number 5`

### Include Relevant Details
For shop registration:
```
add shop "Tech Hub" owner "John Doe" email john@test.com city "Mumbai"
```

For product creation:
```
create product "Widget Pro" price 99.99 quantity 100 brand "Acme"
```

### Use Autocomplete
- Start typing to see suggestions
- Press **Arrow Down/Up** to navigate
- Press **Enter** to select a suggestion
- Press **Escape** to close suggestions

### Destructive Actions Need Confirmation
Commands like `delete`, `cancel`, and `suspend` will ask for confirmation before executing.

---

## API Endpoints

For developers, these endpoints power the command system:

| Endpoint | Description |
|----------|-------------|
| `POST /api/command` | Execute a natural language command |
| `GET /api/command/suggestions?query=&role=` | Get command suggestions |
| `GET /api/command/quick-actions?role=` | Get quick action buttons |
| `GET /api/command/all?role=` | Get all commands by category |
| `GET /api/command/help/{command}` | Get help for a specific command |

---

## Need Help?

- Type partial commands to see suggestions
- Click quick action buttons for common tasks
- Check the Activity Log for command results
- Contact support for additional assistance

---

*Last updated: January 2026*
