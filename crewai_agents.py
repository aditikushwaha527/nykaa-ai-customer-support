
from crewai import Agent, Crew, Task, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from order_lookup import check_order_status
from rag_engine import (
    load_rag_system,
    retrieve_context,
    mock_llm_generate
)
from mock_llm import MockLLM


# ==================================================
# 1. ORDER LOOKUP TOOL INPUT
# ==================================================

class OrderLookupInput(BaseModel):
    record_id: str = Field(
        description="Customer's Nykaa order ID, for example NYK0001."
    )


# ==================================================
# 2. ORDER LOOKUP TOOL
# ==================================================

class OrderLookupTool(BaseTool):

    name: str = "check_order_status"

    description: str = (
        "Checks a customer's Nykaa order status. "
        "Returns order details, shipment delay information "
        "and escalation information."
    )

    args_schema: type[BaseModel] = OrderLookupInput

    def _run(self, record_id: str) -> str:
        result = check_order_status(record_id)
        return str(result)


# ==================================================
# 3. POLICY SEARCH TOOL INPUT
# ==================================================

class PolicySearchInput(BaseModel):
    question: str = Field(
        description="Customer's question about Nykaa policies."
    )


# ==================================================
# 4. POLICY SEARCH TOOL
# ==================================================

class PolicySearchTool(BaseTool):

    name: str = "search_nykaa_policies"

    description: str = (
        "Searches the Nykaa customer support knowledge base "
        "for refunds, returns, cancellations, shipping, "
        "damaged products, replacements and exchanges."
    )

    args_schema: type[BaseModel] = PolicySearchInput

    def _run(self, question: str) -> str:

        collection, model = load_rag_system()

        retrieved_chunks = retrieve_context(
            collection,
            model,
            question
        )

        answer = mock_llm_generate(
            question,
            retrieved_chunks
        )

        return str(answer)


# ==================================================
# 5. INITIALIZE MOCK LLM
# ==================================================

mock_llm = MockLLM()


# ==================================================
# 6. INITIALIZE TOOLS
# ==================================================

order_tool = OrderLookupTool()
policy_tool = PolicySearchTool()


# ==================================================
# 7. UNIFIED CUSTOMER SUPPORT AGENT
# ==================================================

customer_support_agent = Agent(

    role="Nykaa Customer Support Agent",

    goal=(
        "Resolve customer queries about orders, refunds, "
        "returns, cancellations, replacements and shipping."
    ),

    backstory=(
        "You are a customer support agent for Nykaa. "
        "You provide accurate order information and "
        "grounded policy answers. Never invent customer "
        "order details or company policies."
    ),

    llm=mock_llm,

    tools=[
        order_tool,
        policy_tool
    ],

    allow_delegation=False,

    verbose=True,

    max_iter=2
)


# ==================================================
# 8. CUSTOMER SUPPORT TASK
# ==================================================

customer_support_task = Task(

    description=(
        "Respond to this customer message: {customer_query}. "
        "Use the available customer order or policy information "
        "to provide a clear, accurate and helpful response. "
        "Do not invent information."
    ),

    expected_output=(
        "A clear customer support response based on the "
        "customer's order information or Nykaa support policies."
    ),

    agent=customer_support_agent
)


# ==================================================
# 9. CREATE CUSTOMER SUPPORT CREW
# ==================================================

customer_support_crew = Crew(

    agents=[
        customer_support_agent
    ],

    tasks=[
        customer_support_task
    ],

    process=Process.sequential,

    verbose=True
)


# ==================================================
# 10. PROJECT TEST
# ==================================================

if __name__ == "__main__":

    test_query = "What is the refund timeline for Cash on Delivery orders?"

    print("\nStarting Nykaa Customer Support...")
    print("Customer query:", test_query)

    result = customer_support_crew.kickoff(
        inputs={
            "customer_query": test_query
        }
    )

    print("\n========================================")
    print("CUSTOMER SUPPORT RESPONSE")
    print("========================================")

    print(result)

    print("\n========================================")
    print("MOCK LLM USAGE")
    print("========================================")

    print("LLM calls:", mock_llm.call_count)
    print("Routed function calls:", mock_llm.tool_call_count)
