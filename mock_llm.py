
import re

from crewai.llms.base_llm import BaseLLM


class MockLLM(BaseLLM):

    def __init__(self, model: str = "nykaa-mock-llm"):
        super().__init__(model=model)
        self.call_count = 0
        self.tool_call_count = 0

    def _get_prompt_text(self, messages):

        if isinstance(messages, str):
            return messages

        parts = []

        for message in messages:
            if isinstance(message, dict):
                content = message.get("content", "")
            else:
                content = getattr(message, "content", str(message))

            parts.append(str(content))

        return "\n".join(parts)

    def _extract_customer_query(self, prompt):

        match = re.search(
            r"Respond to this customer message:\s*(.*?)"
            r"\.\s*Use the available customer order",
            prompt,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return match.group(1).strip()

        return prompt.strip()

    def _extract_record_id(self, text):

        match = re.search(
            r"\bNYK\d{4,}\b",
            text,
            re.IGNORECASE
        )

        return match.group(0).upper() if match else None

    def _select_route(self, customer_query):

        text = customer_query.lower()

        if self._extract_record_id(customer_query):
            return "check_order_status"

        policy_keywords = [
            "refund",
            "return",
            "cancellation",
            "cancel",
            "shipping policy",
            "delivery policy",
            "damaged product",
            "replacement",
            "exchange",
            "cash on delivery",
            "cod",
            "refund timeline"
        ]

        if any(word in text for word in policy_keywords):
            return "search_nykaa_policies"

        order_keywords = [
            "order status",
            "check my order",
            "track my order",
            "where is my order",
            "track order",
            "delivery status"
        ]

        if any(word in text for word in order_keywords):
            return "check_order_status"

        return None

    def _format_order_response(self, result):

        if not result.get("found"):
            return (
                "I'm sorry, I couldn't find an order with that ID. "
                "Please check the order ID and try again."
            )

        order_id = result.get("record_id", "your order")
        status = result.get("status", "Unavailable")
        category = result.get("category", "your product")
        amount = result.get("order_value_inr", 0)

        amount_formatted = (
            f"₹{amount:,.2f}".rstrip("0").rstrip(".")
        )

        response = (
            f"Your order **{order_id}** is currently **{status}**.\n\n"
            f"- Product category: {category}\n"
            f"- Order value: {amount_formatted}\n"
        )

        if result.get("requires_escalation"):

            ticket = result.get("escalation_ticket") or {}

            ticket_id = ticket.get(
                "ticket_id",
                f"ESC-{order_id}"
            )

            response += (
                "\n**Your order requires further review.**\n\n"
                "Our support team has been notified for human review.\n\n"
                f"Your support reference number is **{ticket_id}**.\n\n"
                "Please keep this reference number for future "
                "communication with our support team."
            )

        elif result.get("delayed_shipment"):

            response += (
                "\nYour shipment appears to be delayed. "
                "We apologize for the inconvenience."
            )

        elif status.lower() == "delivered":

            response += (
                "\nYour order has been delivered successfully."
            )

        else:

            response += (
                "\nThank you for shopping with Nykaa!"
            )

        return response

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ) -> str:

        self.call_count += 1

        prompt = self._get_prompt_text(messages)
        customer_query = self._extract_customer_query(prompt)

        route = self._select_route(customer_query)

        # ORDER LOOKUP
        if route == "check_order_status":

            from order_lookup import check_order_status

            record_id = self._extract_record_id(customer_query)

            if not record_id:
                return (
                    "Please provide your Nykaa order ID, "
                    "for example NYK0001, so I can check your order."
                )

            self.tool_call_count += 1

            result = check_order_status(record_id)

            return self._format_order_response(result)

        # POLICY SEARCH USING RAG
        if route == "search_nykaa_policies":

            from rag_engine import (
                load_rag_system,
                retrieve_context,
                mock_llm_generate,
            )

            collection, model = load_rag_system()

            retrieved_chunks = retrieve_context(
                collection,
                model,
                customer_query
            )

            self.tool_call_count += 1

            answer = mock_llm_generate(
                customer_query,
                retrieved_chunks
            )

            return str(answer)

        if response_model is not None:
            return str(response_model.model_json_schema())

        return (
            "Hello! Welcome to Nykaa Customer Support. "
            "I can help you with order tracking, refunds, "
            "returns, cancellations and shipping policies. "
            "Please tell me how I can help you."
        )
