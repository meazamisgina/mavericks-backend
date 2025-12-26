import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
import os

# This creates a 'vector_db' folder in your project to store the fingerprints
client = chromadb.PersistentClient(path="./vector_db")

# We use a standard embedding function that understands images
# This might download a small model the first time you run it
embedding_function = OpenCLIPEmbeddingFunction()

collection = client.get_or_create_collection(
    name="product_images",
    embedding_function=embedding_function
)

def add_product_to_vector_db(product_id, image_path, metadata):
    """Stores the image fingerprint in ChromaDB"""
    collection.add(
        ids=[str(product_id)],
        uris=[image_path],
        metadatas=[metadata]
    )

def search_similar_products(image_path, n_results=5):
    """Finds the most similar images in the database"""
    results = collection.query(
        query_uris=[image_path],
        n_results=n_results
    )
    return results