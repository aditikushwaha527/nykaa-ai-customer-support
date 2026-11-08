
import json
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# -----------------------------------------
# 1. PROJECT PATHS AND SETTINGS
# -----------------------------------------

BASE_DIR = Path(__file__).parent

POLICY_FILE = BASE_DIR / "knowledge_base" / "policies.json"
CHROMA_DIR = BASE_DIR / "chroma_db"

MODEL_NAME = "all-MiniLM-L6-v2"

FIXED_CHUNK_SIZE = 500
FIXED_CHUNK_OVERLAP = 100

SENTENCES_PER_CHUNK = 3
SENTENCE_OVERLAP = 1


# -----------------------------------------
# 2. LOAD POLICY DOCUMENTS
# -----------------------------------------

def load_policies():
    if not POLICY_FILE.exists():
        raise FileNotFoundError(
            f"Policy file not found: {POLICY_FILE}"
        )

    with open(POLICY_FILE, "r", encoding="utf-8") as file:
        policies = json.load(file)

    if len(policies) < 12:
        raise ValueError("At least 12 policy documents are required.")

    for policy in policies:
        if not all(key in policy for key in ["id", "topic", "content"]):
            raise ValueError("A policy is missing a required field.")

    print(f"Loaded {len(policies)} policy documents.")

    return policies


# -----------------------------------------
# 3. FIXED-SIZE CHUNKING WITH OVERLAP
# -----------------------------------------

def fixed_size_chunk(text):
    chunks = []

    start = 0

    while start < len(text):
        end = start + FIXED_CHUNK_SIZE

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - FIXED_CHUNK_OVERLAP

    return chunks


# -----------------------------------------
# 4. SENTENCE-BASED CHUNKING
# -----------------------------------------

def sentence_based_chunk(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    chunks = []

    start = 0

    while start < len(sentences):
        end = start + SENTENCES_PER_CHUNK

        chunk = " ".join(sentences[start:end])

        if chunk:
            chunks.append(chunk)

        if end >= len(sentences):
            break

        start = end - SENTENCE_OVERLAP

    return chunks


# -----------------------------------------
# 5. PREPARE CHUNKS AND METADATA
# -----------------------------------------

def prepare_chunks(policies, chunking_method):
    all_chunks = []

    for policy in policies:

        if chunking_method == "fixed":
            chunks = fixed_size_chunk(policy["content"])

        elif chunking_method == "sentence":
            chunks = sentence_based_chunk(policy["content"])

        else:
            raise ValueError("Unknown chunking method.")

        for index, chunk in enumerate(chunks):

            all_chunks.append({
                "id": f'{policy["id"]}_{chunking_method}_{index}',
                "text": chunk,
                "metadata": {
                    "parent_doc_id": policy["id"],
                    "topic": policy["topic"],
                    "chunk_method": chunking_method,
                    "chunk_number": index
                }
            })

    return all_chunks


# -----------------------------------------
# 6. CREATE CHROMADB COLLECTION
# -----------------------------------------

def store_in_chromadb(client, collection_name, chunks, model):

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    # Remove old records before rebuilding this collection.
    existing_records = collection.get()

    if existing_records["ids"]:
        collection.delete(ids=existing_records["ids"])

    if not chunks:
        raise ValueError(f"No chunks generated for {collection_name}.")

    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    print(f"\nGenerating embeddings for {collection_name}...")

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings.tolist()
    )

    print(f"Stored {collection.count()} chunks in {collection_name}.")

    return collection


# -----------------------------------------
# 7. MAIN PROGRAM
# -----------------------------------------

def main():

    print("=" * 50)
    print("NYKAA RAG SYSTEM BUILD")
    print("=" * 50)

    policies = load_policies()

    print("\nLoading local embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    # Generate fixed-size chunks.
    fixed_chunks = prepare_chunks(
        policies,
        "fixed"
    )

    # Generate sentence-based chunks.
    sentence_chunks = prepare_chunks(
        policies,
        "sentence"
    )

    print("\nCHUNKING RESULTS")
    print("-" * 40)
    print("Fixed-size chunks:", len(fixed_chunks))
    print("Sentence-based chunks:", len(sentence_chunks))

    # Store both strategies in separate collections.
    fixed_collection = store_in_chromadb(
        client,
        "nykaa_fixed_chunks",
        fixed_chunks,
        model
    )

    sentence_collection = store_in_chromadb(
        client,
        "nykaa_sentence_chunks",
        sentence_chunks,
        model
    )

    print("\nDATABASE VERIFICATION")
    print("-" * 40)
    print("Fixed collection count:", fixed_collection.count())
    print("Sentence collection count:", sentence_collection.count())

    print("\nRAG BUILD COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
