from sentence_transformers import SentenceTransformer
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
embeddings = SentenceTransformer("all-MiniLM-L6-v2")

def embed(title, description, tools):
    text = f"Title: {title}\nDescription: {description}"
    return embeddings.encode(text, normalize_embeddings=True).tolist()

def embed_query(query):
    return embeddings.encode(query, normalize_embeddings=True).tolist()