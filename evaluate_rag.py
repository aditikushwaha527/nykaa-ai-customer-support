
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer


# ==================================================
# 1. PROJECT SETTINGS
# ==================================================

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "chroma_db"

MODEL_NAME = "all-MiniLM-L6-v2"

COLLECTIONS = [
    "nykaa_fixed_chunks",
    "nykaa_sentence_chunks"
]

TOP_K = 3


# ==================================================
# 2. EVALUATION QUESTIONS AND RELEVANT DOCUMENTS
# ==================================================

# Each question has a known correct policy document.
# These are our manually defined evaluation labels.

EVALUATION_QUESTIONS = [
    {
        "question": "What is the refund timeline for COD orders?",
        "relevant_ids": {"POL002"}
    },
    {
        "question": "What is the return window for footwear?",
        "relevant_ids": {"POL001"}
    },
    {
        "question": "Can I cancel an order after it has shipped?",
        "relevant_ids": {"POL006"}
    },
    {
        "question": "What should I do if I receive a damaged product?",
        "relevant_ids": {"POL010"}
    },
    {
        "question": "Is international shipping available?",
        "relevant_ids": {"POL011"}
    }
]


# Used only for similarity-threshold calibration.
IN_SCOPE_QUESTIONS = [
    "How many business days does a COD refund take?",
    "Can I exchange footwear if the size is incorrect?",
    "What is the warranty period for electronics?",
    "How do I report a damaged item?",
    "Can customers cancel an order before it is shipped?"
]

OUT_OF_SCOPE_QUESTIONS = [
    "What is the capital city of Japan?",
    "How can I repair a bicycle engine?"
]


# ==================================================
# 3. LOAD THE MODEL AND DATABASE
# ==================================================

def load_system():

    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    return client, model


# ==================================================
# 4. RETRIEVE DOCUMENTS
# ==================================================

def retrieve(client, model, collection_name, question):

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
        n_results=TOP_K,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    retrieved = []

    for i in range(len(results["ids"][0])):

        similarity = 1 - results["distances"][0][i]

        retrieved.append({
            "parent_doc_id": results["metadatas"][0][i][
                "parent_doc_id"
            ],
            "topic": results["metadatas"][0][i]["topic"],
            "similarity": similarity,
            "text": results["documents"][0][i]
        })

    return retrieved


# ==================================================
# 5. DOCUMENT-LEVEL PRECISION AND RECALL
# ==================================================

def evaluate_collection(client, model, collection_name):

    total_precision = 0
    total_recall = 0

    print("\n" + "=" * 65)
    print("EVALUATING:", collection_name)
    print("=" * 65)

    for item in EVALUATION_QUESTIONS:

        question = item["question"]
        relevant_ids = item["relevant_ids"]

        results = retrieve(
            client,
            model,
            collection_name,
            question
        )

        # Deduplicate chunks using their parent document IDs.
        retrieved_ids = list(dict.fromkeys(
            result["parent_doc_id"]
            for result in results
        ))

        retrieved_set = set(retrieved_ids)

        relevant_retrieved = (
            retrieved_set & relevant_ids
        )

        hits = len(relevant_retrieved)

        precision = (
            hits / len(retrieved_set)
            if retrieved_set else 0
        )

        recall = (
            hits / len(relevant_ids)
            if relevant_ids else 0
        )

        total_precision += precision
        total_recall += recall

        print("\nQuestion:", question)
        print("Relevant document IDs:", sorted(relevant_ids))
        print("Retrieved unique document IDs:", retrieved_ids)
        print("Relevant documents retrieved:", hits)

        print(
            f"Precision: {hits}/{len(retrieved_set)} "
            f"= {precision:.4f}"
        )

        print(
            f"Recall: {hits}/{len(relevant_ids)} "
            f"= {recall:.4f}"
        )

    count = len(EVALUATION_QUESTIONS)

    average_precision = total_precision / count
    average_recall = total_recall / count

    print("\nAVERAGE RESULTS")
    print("Average precision:", round(average_precision, 4))
    print("Average recall:", round(average_recall, 4))

    return {
        "precision": average_precision,
        "recall": average_recall
    }


# ==================================================
# 6. SIMILARITY THRESHOLD CALIBRATION
# ==================================================

def calibrate_threshold(client, model, collection_name):

    print("\n" + "=" * 65)
    print("THRESHOLD CALIBRATION:", collection_name)
    print("=" * 65)

    in_scope_scores = []
    out_scope_scores = []

    # Test in-scope questions.
    for question in IN_SCOPE_QUESTIONS:

        results = retrieve(
            client,
            model,
            collection_name,
            question
        )

        top_score = results[0]["similarity"]

        in_scope_scores.append(top_score)

        print("\nIN-SCOPE:", question)
        print("Top-1 similarity:", round(top_score, 4))

    # Test out-of-scope questions.
    for question in OUT_OF_SCOPE_QUESTIONS:

        results = retrieve(
            client,
            model,
            collection_name,
            question
        )

        top_score = results[0]["similarity"]

        out_scope_scores.append(top_score)

        print("\nOUT-OF-SCOPE:", question)
        print("Top-1 similarity:", round(top_score, 4))

    # Compare the observed score ranges.
    minimum_in_scope = min(in_scope_scores)
    maximum_out_scope = max(out_scope_scores)

    print("\nSCORE SUMMARY")
    print("Minimum in-scope score:", round(minimum_in_scope, 4))
    print("Maximum out-of-scope score:", round(maximum_out_scope, 4))

    if maximum_out_scope < minimum_in_scope:

        threshold = (
            maximum_out_scope + minimum_in_scope
        ) / 2

        print("\nA SEPARATING THRESHOLD WAS FOUND.")
        print("Proposed threshold:", round(threshold, 4))

    else:

        print("\nWARNING: SCORE RANGES OVERLAP.")
        print(
            "No defensible separating threshold was found "
            "from these samples."
        )
        print(
            "Collect more representative test questions "
            "before choosing a threshold."
        )


# ==================================================
# 7. MAIN PROGRAM
# ==================================================

def main():

    print("=" * 65)
    print("NYKAA RAG EVALUATION")
    print("=" * 65)

    client, model = load_system()

    # Compare both chunking methods.
    evaluation_results = {}

    for collection_name in COLLECTIONS:

        evaluation_results[collection_name] = (
            evaluate_collection(
                client,
                model,
                collection_name
            )
        )

    # Compare average precision and recall.
    print("\n" + "=" * 65)
    print("FINAL CHUNKING COMPARISON")
    print("=" * 65)

    for collection_name, scores in evaluation_results.items():

        print("\n", collection_name)
        print("Precision:", round(scores["precision"], 4))
        print("Recall:", round(scores["recall"], 4))

    # Calibrate threshold for both collections separately.
    for collection_name in COLLECTIONS:

        calibrate_threshold(
            client,
            model,
            collection_name
        )

    print("\n" + "=" * 65)
    print("RAG EVALUATION COMPLETED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
