
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer


# -----------------------------------------
# 1. PROJECT SETTINGS
# -----------------------------------------

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "chroma_db"

MODEL_NAME = "all-MiniLM-L6-v2"

COLLECTIONS = [
    "nykaa_fixed_chunks",
    "nykaa_sentence_chunks"
]

# Five customer questions for retrieval testing
TEST_QUESTIONS = [
    "What is the refund timeline for COD orders?",
    "What is the return window for footwear?",
    "Can I cancel an order after it has shipped?",
    "What should I do if I receive a damaged product?",
    "Is international shipping available?"
]


# -----------------------------------------
# 2. LOAD DATABASE AND MODEL
# -----------------------------------------

def load_system():

    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    return client, model


# -----------------------------------------
# 3. RETRIEVE RELEVANT POLICY CHUNKS
# -----------------------------------------

def retrieve_documents(client, model, collection_name, question):

    collection = client.get_collection(
        name=collection_name
    )

    question_embedding = model.encode(
        question,
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=3,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    retrieved = []

    for i in range(len(results["ids"][0])):

        distance = results["distances"][0][i]

        # ChromaDB cosine distance is converted
        # into cosine similarity.
        similarity = 1 - distance

        retrieved.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "similarity": similarity
        })

    return retrieved


# -----------------------------------------
# 4. TEST BOTH COLLECTIONS
# -----------------------------------------

def main():

    print("=" * 60)
    print("NYKAA RAG RETRIEVAL TEST")
    print("=" * 60)

    client, model = load_system()

    for question_number, question in enumerate(
        TEST_QUESTIONS, start=1
    ):

        print("\n" + "=" * 60)
        print(f"QUESTION {question_number}: {question}")
        print("=" * 60)

        for collection_name in COLLECTIONS:

            print(f"\nCollection: {collection_name}")
            print("-" * 50)

            results = retrieve_documents(
                client,
                model,
                collection_name,
                question
            )

            for rank, result in enumerate(results, start=1):

                print(f"\nResult {rank}")
                print(
                    "Policy:",
                    result["metadata"]["topic"]
                )
                print(
                    "Parent document ID:",
                    result["metadata"]["parent_doc_id"]
                )
                print(
                    "Similarity:",
                    round(result["similarity"], 4)
                )
                print(
                    "Retrieved text:",
                    result["document"]
                )

    print("\n" + "=" * 60)
    print("RETRIEVAL TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
