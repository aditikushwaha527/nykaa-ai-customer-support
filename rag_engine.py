
import chromadb
from pathlib import Path
import re
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. PROJECT SETTINGS
# ==========================================

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "chroma_db"

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "nykaa_sentence_chunks"

SIMILARITY_THRESHOLD = 0.2727
TOP_K = 3


# ==========================================
# 2. LOAD RAG SYSTEM
# ==========================================

def load_rag_system():

    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    return collection, model


# ==========================================
# 3. RETRIEVE AND RERANK RELEVANT CONTEXT
# ==========================================

def retrieve_context(collection, model, question):

    question_embedding = model.encode(
        question,
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=collection.count(),
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    stop_words = {
        "what", "is", "the", "a", "an", "in",
        "on", "for", "to", "of", "and", "or",
        "can", "i", "do", "how", "does", "my",
        "it", "if", "has", "have", "are", "be"
    }

    question_words = set(
        re.findall(r"\b[a-z]+\b", question.lower())
    ) - stop_words

    candidates = {}

    for i in range(len(results["ids"][0])):

        similarity = 1 - results["distances"][0][i]

        document = results["documents"][0][i]
        metadata = results["metadatas"][0][i]

        searchable_text = (
            metadata["topic"] + " " + document
        )

        document_words = set(
            re.findall(r"\b[a-z]+\b", searchable_text.lower())
        )

        keyword_matches = question_words & document_words

        lexical_score = (
            len(keyword_matches) / len(question_words)
            if question_words else 0
        )

        rerank_score = (
            0.70 * similarity +
            0.30 * lexical_score
        )

        candidate = {
            "text": document,
            "topic": metadata["topic"],
            "parent_doc_id": metadata["parent_doc_id"],
            "similarity": similarity,
            "lexical_score": lexical_score,
            "rerank_score": rerank_score
        }

        parent_id = metadata["parent_doc_id"]

        if (
            parent_id not in candidates
            or rerank_score > candidates[parent_id]["rerank_score"]
        ):
            candidates[parent_id] = candidate

    ranked_candidates = sorted(
        candidates.values(),
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return ranked_candidates[:TOP_K]


# ==========================================
# 4. MOCK LLM RESPONSE GENERATOR
# ==========================================

def mock_llm_generate(question, retrieved_chunks):

    if not retrieved_chunks:
        return (
            "I'm sorry, I couldn't find relevant information "
            "to answer your question. Could you please clarify?"
        )

    best_match = retrieved_chunks[0]

    if best_match["similarity"] < SIMILARITY_THRESHOLD:

        return (
            "I'm sorry, I couldn't find sufficient information "
            "to answer your question. Please contact our "
            "customer support team for further assistance."
        )

    # Retrieve the actual policy information.
    answer = best_match["text"].strip()

    # Remove unwanted project-related wording.
    answer = re.sub(
        r"\bFor this capstone,\s*",
        "",
        answer,
        flags=re.IGNORECASE
    )

    # Return the policy directly without an introduction.
    return answer


# ==========================================
# 5. ASK CUSTOMER QUESTIONS
# ==========================================

def ask_question(collection, model, question):

    print("\n" + "=" * 60)
    print("CUSTOMER QUESTION:", question)
    print("=" * 60)

    retrieved_chunks = retrieve_context(
        collection,
        model,
        question
    )

    print("\nALL RETRIEVED CANDIDATES:")

    for rank, chunk in enumerate(retrieved_chunks, start=1):

        print(
            f"Rank {rank} | "
            f"Policy: {chunk['topic']} | "
            f"ID: {chunk['parent_doc_id']} | "
            f"Similarity: {chunk['similarity']:.4f} | "
            f"Rerank: {chunk['rerank_score']:.4f}"
        )

    if not retrieved_chunks:

        print("\nAnswer:")
        print("No relevant policy information was retrieved.")
        return

    best_match = retrieved_chunks[0]

    print(
        "\nTop similarity score:",
        round(best_match["similarity"], 4)
    )

    print("Selected policy:", best_match["topic"])
    print("Policy ID:", best_match["parent_doc_id"])

    answer = mock_llm_generate(
        question,
        retrieved_chunks
    )

    print("\nMOCK LLM RESPONSE:")
    print("-" * 60)
    print(answer)


# ==========================================
# 6. TEST QUESTIONS
# ==========================================

def main():

    collection, model = load_rag_system()

    test_questions = [

        # In-scope questions
        "What is the refund timeline for COD orders?",
        "What is the return window for footwear?",
        "Can I cancel an order after it has shipped?",
        "What should I do if I receive a damaged product?",
        "Is international shipping available?",

        # Out-of-scope questions
        "What is the capital city of Japan?",
        "How can I repair a bicycle engine?"
    ]

    print("\nNYKAA GROUNDED RESPONSE TEST")

    for question in test_questions:

        ask_question(
            collection,
            model,
            question
        )

    print("\n" + "=" * 60)
    print("GROUNDED RESPONSE TEST COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
