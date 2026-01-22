# backend/tools/policy.py - RAG for company policies using OpenAI embeddings + FAISS
import os
import logging
import numpy as np
import faiss
import requests
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment")
    raise RuntimeError("OPENAI_API_KEY is required for policy lookup")

client = OpenAI(api_key=OPENAI_API_KEY)

# Fetch FAQ document
try:
    logger.info("Fetching FAQ document from remote source...")
    response = requests.get(
        "https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md",
        timeout=10
    )
    response.raise_for_status()
    faq_text = response.text
    logger.info("✓ FAQ document loaded successfully")
except Exception as e:
    logger.error(f"Failed to fetch FAQ: {e}")
    faq_text = "# Swiss Airlines FAQ\n\n## Cancellation Policy\nCancellations allowed up to 24 hours before departure."

# Split into documents
docs = [
    {"page_content": txt.strip()}
    for txt in re.split(r"(?=\n##)", faq_text)
    if txt.strip()
]
logger.info(f"Parsed {len(docs)} FAQ sections")


class VectorStoreRetriever:
    """Simple vector store using FAISS for policy document retrieval."""
    
    def __init__(self, docs, vectors, oai_client):
        self._docs = docs
        self._arr = vectors
        self._client = oai_client
        self.dimension = vectors.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(vectors)
        logger.info(f"✓ FAISS index created with {len(docs)} documents")

    @classmethod
    def from_docs(cls, docs, oai_client):
        """Create retriever from documents by generating embeddings."""
        try:
            logger.info("Generating embeddings for FAQ documents...")
            embeddings = oai_client.embeddings.create(
                model="text-embedding-3-small",
                input=[doc["page_content"] for doc in docs]
            )
            vectors = np.array([emb.embedding for emb in embeddings.data])
            logger.info(f"✓ Generated {len(vectors)} embeddings")
            return cls(docs, vectors, oai_client)
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            raise

    def query(self, query, k=5):
        """
        Query the vector store for relevant documents.
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of relevant documents with similarity scores
        """
        try:
            embed = self._client.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            query_emb = np.array([embed.data[0].embedding])
            _, indices = self.index.search(query_emb, k)
            scores = np.dot(query_emb, self._arr.T)[0]
            
            results = [
                {
                    "page_content": self._docs[i]["page_content"],
                    "similarity": float(scores[i])
                }
                for i in indices[0]
            ]
            logger.info(f"Retrieved {len(results)} relevant policy documents")
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []


# Initialize retriever at module load
try:
    retriever = VectorStoreRetriever.from_docs(docs, client)
    logger.info("✓ Policy retriever ready")
except Exception as e:
    logger.error(f"Failed to initialize policy retriever: {e}")
    retriever = None


def lookup_policy(query):
    """
    Lookup company policies via semantic search.
    
    Args:
        query: User's policy question
    
    Returns:
        Relevant policy text or error message
    """
    if not retriever:
        logger.error("Policy retriever not available")
        return "Policy lookup is currently unavailable. Please try again later."
    
    try:
        logger.info(f"Looking up policy for: {query[:100]}")
        retrieved_docs = retriever.query(query, k=2)
        
        if not retrieved_docs:
            return "No relevant policy information found. Please contact customer service."
        
        # Combine top results
        policy_text = "\n\n---\n\n".join([doc["page_content"] for doc in retrieved_docs])
        logger.info("✓ Policy lookup successful")
        return policy_text
    except Exception as e:
        logger.error(f"Policy lookup error: {e}")
        return f"Error retrieving policy: {str(e)}"