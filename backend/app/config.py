import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma:2b")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/embeddings/faiss_index")
