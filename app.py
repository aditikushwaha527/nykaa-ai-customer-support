
import streamlit as st
from crewai_agents import customer_support_crew


# PAGE CONFIGURATION
st.set_page_config(
    page_title="Nykaa Customer Support",
    page_icon="💄",
    layout="centered"
)


# PAGE DESIGN
st.title("💄 Nykaa Customer Support")
st.caption("Your AI-powered shopping assistant")

st.markdown(
    """
    Welcome to Nykaa Customer Support!

    I can help you with:
    - 📦 Order tracking
    - 💰 Refund policies
    - 🔄 Returns and exchanges
    - ❌ Order cancellations
    - 🚚 Shipping policies
    """
)

st.divider()


# INITIALIZE CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! Welcome to Nykaa Customer Support. "
                "How can I help you today?"
            )
        }
    ]


# DISPLAY PREVIOUS MESSAGES
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# CUSTOMER INPUT
customer_query = st.chat_input(
    "Type your question here..."
)


# PROCESS CUSTOMER QUERY
if customer_query:

    # DISPLAY CUSTOMER MESSAGE
    st.session_state.messages.append(
        {
            "role": "user",
            "content": customer_query
        }
    )

    with st.chat_message("user"):
        st.markdown(customer_query)

    # GET AI RESPONSE
    with st.chat_message("assistant"):

        with st.spinner("Nykaa assistant is thinking..."):

            try:
                response = customer_support_crew.kickoff(
                    inputs={
                        "customer_query": customer_query
                    }
                )

                answer = str(response)

            except Exception as error:
                answer = (
                    "Sorry, something went wrong while "
                    "processing your request. Please try again.\n\n"
                    f"Error: {error}"
                )

        st.markdown(answer)

    # SAVE RESPONSE
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


# SIDEBAR
with st.sidebar:
    st.header("About this project")
    st.write(
        "An offline AI-powered customer support system "
        "built using CrewAI, Mock LLM, ChromaDB and RAG."
    )

    st.divider()

    if st.button("Clear conversation"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! Welcome to Nykaa Customer Support. "
                    "How can I help you today?"
                )
            }
        ]
        st.rerun()
