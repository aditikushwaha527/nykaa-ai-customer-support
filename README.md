# Nykaa AI-Powered Customer Support System

## Project Overview

The Nykaa AI-Powered Customer Support System is an intelligent customer-support application designed to assist customers with order-related queries and company policies.

The system combines CrewAI, an offline Mock LLM, Retrieval-Augmented Generation (RAG), ChromaDB and Streamlit to provide automated customer assistance.

It supports order tracking, policy information retrieval and escalation of orders that require human review.

## Objectives

- Automate basic customer-support queries.
- Retrieve customer order information from a structured dataset.
- Provide policy-based answers using a knowledge base.
- Identify orders that require further human review.
- Provide a simple chat-based customer interface.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.11.9 | Main programming language |
| CrewAI | Agent orchestration |
| Mock LLM | Offline query routing and response generation |
| ChromaDB | Vector database |
| Sentence Transformers | Text embeddings |
| RAG | Policy retrieval |
| Streamlit | Customer-support interface |
| CSV | Order dataset and escalation queue |
| JSON | Policy knowledge base |

## Implemented Features

### 1. Customer Order Lookup

- Uses a fictional dataset containing 50 Nykaa orders.
- Retrieves order ID, product category, order status and order value.
- Identifies delayed shipments.
- Calculates an escalation score for each order.

### 2. Policy-Based Question Answering

- Uses a knowledge base containing 12 policy documents.
- Implements fixed-size and sentence-based text chunking.
- Generates text embeddings using Sentence Transformers.
- Stores policy chunks in ChromaDB.
- Retrieves relevant policy information using semantic similarity and keyword-based reranking.
- Provides answers using an offline deterministic Mock LLM.

### 3. CrewAI Integration

- Implements a Nykaa Customer Support Agent.
- Connects the customer-support task to the Mock LLM.
- Routes order-related queries to the order lookup function.
- Routes policy-related queries to the RAG retrieval system.

### 4. Escalation Management

- Calculates an escalation score using shipment delay and order age.
- Uses the 80th percentile of dataset scores as the escalation threshold.
- Creates escalation tickets for qualifying orders.
- Stores tickets in `data/escalation_queue.csv`.
- Prevents duplicate tickets for the same order.
- Maintains a Pending review status.

### 5. Streamlit Interface

- Provides a chat-based customer-support interface.
- Displays customer and assistant messages.
- Supports order-tracking and policy-related questions.
- Maintains conversation history during the session.

## Project Structure

```text
Agentic AI capstone project/
│
├── app.py
├── crewai_agents.py
├── mock_llm.py
├── order_lookup.py
├── rag_engine.py
├── build-rag.py
├── dataset.py
├── test_retrieval.py
├── evaluate_rag.py
│
├── data/
│   ├── nykaa_orders.csv
│   └── escalation_queue.csv
│
├── knowledge_base/
│   └── policies.json
│
├── chroma_db/             # Generated vector database
│
├── requirements.txt
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.11 or compatible version
- Visual Studio Code
- Git
- GitHub account

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_PROJECT_FOLDER
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Build the RAG knowledge base

```bash
python build-rag.py
```

This generates the ChromaDB collections from the policy documents.

### 5. Run the application

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal.

## Example Customer Queries

**Order Tracking**

```text
Check the status of my order NYK0001
```

**Policy Retrieval**

```text
What is the refund timeline for Cash on Delivery orders?
```

**Escalation Testing**

```text
Check the status of my order NYK0007
```

## Escalation Scoring Logic

The current escalation score uses two factors:

- Shipment delay: 60%
- Order age: 40%

The system compares the calculated score against the 80th percentile threshold derived from the dataset.

Orders meeting or exceeding the threshold are added to the human-review queue.

## Current Project Status

The following components have been implemented and tested:

- Python project environment
- Fictional Nykaa order dataset
- Policy knowledge base
- ChromaDB vector storage
- RAG-based policy retrieval
- Offline Mock LLM
- Basic CrewAI customer-support agent
- Order lookup
- Escalation scoring and CSV ticket creation
- Streamlit customer-support interface

## Future Improvements

- Expand the CrewAI architecture into specialized agents.
- Integrate additional agent-review workflows.
- Develop a FastAPI backend.
- Add an administrative escalation dashboard.
- Improve customer conversation handling.
- Expand evaluation, testing and governance features.

## Note

This project uses fictional customer orders and an offline Mock LLM. It does not connect to Nykaa's actual customer database or production systems.

The application is an academic capstone implementation and demonstrates an approach to AI-assisted e-commerce customer support.

## Author

Developed as an Agentic AI capstone project in the E-commerce domain, focusing on Nykaa customer support.
