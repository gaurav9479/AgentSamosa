# AgentSamosa

Agentic AI Command & Control System - A backend that takes natural language commands, parses intent using Google Gemini, and executes real database operations with real-time updates.

## Architecture

```
User Command → Gemini (Intent Parser) → Action Executor → Database → WebSocket Broadcast
```

## Features

- **Intent Recognition**: Natural language to structured actions via Gemini
- **Database Mutations**: Full CRUD for Products and Orders
- **Context Awareness**: Session memory for contextual commands
- **Real-time Updates**: WebSocket broadcasts for live UI updates
- **Safety Rails**: Confirmation required for destructive operations
- **Multi-step Execution**: Complex commands broken into action plans

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **LLM**: Google Gemini 1.5 Flash
- **Real-time**: WebSockets

## Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
# - DATABASE_URL=postgresql://user:pass@localhost:5432/agentsamosa
# - GEMINI_API_KEY=your_api_key
```

### 3. Setup PostgreSQL

```bash
# Create database
createdb agentsamosa

# Or using psql
psql -c "CREATE DATABASE agentsamosa;"
```

### 4. Run the Server

```bash
python run.py
# Or: uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000
API Docs: http://localhost:8000/docs

## API Endpoints

### Agent Command (Main)

```bash
POST /api/command
{
  "text": "Create a product called iPhone with price 999",
  "context": {}
}
```

### Example Commands

```
"Create a product called MacBook Pro with price 2499"
"Update product 1 price to 1999"
"Delete product 5"
"Show all products"
"Create an order for product 1, quantity 2 for John Doe"
"Cancel order 3"
"Cancel that order and refund"  # Multi-step
```

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/products | List products |
| POST | /api/products | Create product |
| PUT | /api/products/{id} | Update product |
| DELETE | /api/products/{id} | Delete product |
| GET | /api/orders | List orders |
| POST | /api/orders | Create order |
| POST | /api/orders/{id}/cancel | Cancel order |

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // { type: "action_result", action: "create_product", success: true, data: {...} }
  // { type: "data_update", entity: "product", operation: "created", data: {...} }
};
```

## Safety Features

Destructive operations require confirmation:

```json
// Response when trying to delete
{
  "success": false,
  "action": "delete_product",
  "requires_confirmation": true,
  "confirmation_id": "uuid-here",
  "message": "Are you sure you want to delete_product?"
}

// Confirm with:
POST /api/command/confirm/{confirmation_id}
```

## Project Structure

```
AgentSamosa/
├── app/
│   ├── api/
│   │   └── routes.py       # All API endpoints
│   ├── core/
│   │   ├── config.py       # Settings
│   │   ├── database.py     # DB connection
│   │   └── websocket.py    # WebSocket manager
│   ├── models/
│   │   ├── product.py      # Product model
│   │   ├── order.py        # Order model
│   │   └── action_log.py   # Audit log
│   ├── schemas/
│   │   ├── product.py      # Product DTOs
│   │   ├── order.py        # Order DTOs
│   │   └── command.py      # Command/Intent DTOs
│   ├── services/
│   │   ├── intent_parser.py    # Gemini integration
│   │   ├── action_executor.py  # Action routing
│   │   ├── product_service.py  # Product CRUD
│   │   └── order_service.py    # Order CRUD
│   └── main.py             # FastAPI app
├── tests/
├── requirements.txt
├── run.py
└── README.md
```

## Get Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Add to .env file
