
import streamlit as st

from crewai_agents import customer_support_crew

from order_lookup import (
    get_escalation_queue,
    update_escalation_status
)


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Nykaa Customer Support",
    page_icon="💄",
    layout="wide"
)


# ==========================================
# 2. APPLICATION HEADER
# ==========================================

st.title("💄 Nykaa Customer Support System")

st.caption(
    "AI-powered customer assistance and escalation management"
)


# ==========================================
# 3. NAVIGATION TABS
# ==========================================

customer_tab, admin_tab = st.tabs([
    "💬 Customer Support",
    "📋 Admin Escalation Dashboard"
])


# ==========================================
# 4. CUSTOMER SUPPORT CHAT
# ==========================================

with customer_tab:

    st.subheader("Customer Support Assistant")

    st.write(
        "Ask questions about your orders, refunds, "
        "returns, cancellations and shipping policies."
    )

    # Initialize conversation history
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

    # Display conversation history
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Customer input
    customer_query = st.chat_input(
        "Type your question here...",
        key="customer_chat"
    )

    if customer_query:

        # Display customer message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": customer_query
            }
        )

        with st.chat_message("user"):
            st.markdown(customer_query)

        # Generate assistant response
        with st.chat_message("assistant"):

            with st.spinner("Processing your request..."):

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
                        "processing your request.\n\n"
                        f"Error: {error}"
                    )

                st.markdown(answer)

        # Save assistant response
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    # Clear conversation
    if st.button(
        "Clear conversation",
        key="clear_chat"
    ):

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


# ==========================================
# 5. ADMIN ESCALATION DASHBOARD
# ==========================================

with admin_tab:

    st.subheader("Human Escalation Management")

    st.write(
        "Monitor and manage customer orders that require "
        "additional human review."
    )

    # Load escalation tickets
    tickets = get_escalation_queue()

    # Dashboard metrics
    total_tickets = len(tickets)

    pending_tickets = sum(
        ticket["review_status"] == "Pending"
        for ticket in tickets
    )

    under_review_tickets = sum(
        ticket["review_status"] == "Under Review"
        for ticket in tickets
    )

    resolved_tickets = sum(
        ticket["review_status"] == "Resolved"
        for ticket in tickets
    )

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Tickets",
        total_tickets
    )

    col2.metric(
        "Pending",
        pending_tickets
    )

    col3.metric(
        "Under Review",
        under_review_tickets
    )

    col4.metric(
        "Resolved",
        resolved_tickets
    )

    st.divider()

    # Display ticket records
    st.subheader("Escalation Tickets")

    if tickets:

        st.dataframe(
            tickets,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # Ticket management
        st.subheader("Update Ticket Status")

        ticket_ids = [
            ticket["ticket_id"]
            for ticket in tickets
        ]

        selected_ticket = st.selectbox(
            "Select an escalation ticket",
            ticket_ids
        )

        selected_record = next(
            (
                ticket for ticket in tickets
                if ticket["ticket_id"] == selected_ticket
            ),
            None
        )

        if selected_record:

            st.write(
                f"**Order ID:** {selected_record['record_id']}"
            )

            st.write(
                f"**Escalation reason:** "
                f"{selected_record['reason']}"
            )

            st.write(
                f"**Current status:** "
                f"{selected_record['review_status']}"
            )

            new_status = st.selectbox(
                "Choose new review status",
                [
                    "Pending",
                    "Under Review",
                    "Resolved"
                ],
                index=[
                    "Pending",
                    "Under Review",
                    "Resolved"
                ].index(selected_record["review_status"]),
                key="new_ticket_status"
            )

            if st.button(
                "Update Ticket",
                type="primary"
            ):

                success = update_escalation_status(
                    selected_ticket,
                    new_status
                )

                if success:

                    st.success(
                        f"Ticket {selected_ticket} updated "
                        f"to {new_status}."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Unable to update the selected ticket."
                    )

    else:

        st.info(
            "No escalation tickets are currently available."
        )


# ==========================================
# 6. SIDEBAR INFORMATION
# ==========================================

with st.sidebar:

    st.header("About this project")

    st.write(
        "An offline AI-powered customer support system "
        "built using CrewAI, Mock LLM, ChromaDB and RAG."
    )

    st.divider()

    st.caption(
        "Nykaa E-commerce Customer Support Capstone"
    )
