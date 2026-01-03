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
- create_product: Create a new product (params: name, price, description?, quantity?)
- update_product: Update a product (params: product_id, name?, price?, quantity?, description?)
- delete_product: Delete a product (params: product_id)
- list_products: List all products (params: none)
- get_product: Get a specific product (params: product_id or name)

- create_order: Create a new order (params: product_id, quantity, customer_name, customer_email?)
- update_order: Update an order (params: order_id, status?, quantity?)
- cancel_order: Cancel an order (params: order_id)
- list_orders: List all orders (params: status?)
- get_order: Get a specific order (params: order_id)

Rules:
1. Output ONLY valid JSON, no markdown or explanation
2. For destructive actions (delete, cancel), set requires_confirmation: true
3. If command affects multiple items, set requires_confirmation: true with count
4. If a command requires multiple steps, return an array of actions
5. Use context to resolve references like "that product" or "the last order"

Output format for single action:
{"action": "action_name", "entity": "product|order", "parameters": {...}, "requires_confirmation": false}

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
