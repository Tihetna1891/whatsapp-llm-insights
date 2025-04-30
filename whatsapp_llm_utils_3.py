import os
import re
import logging
import numpy as np
import faiss
from datetime import datetime
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.metadata = []
    
    def build_index(self, chat_data):
        """Create a FAISS index from chat messages"""
        messages = [item["message"] for item in chat_data]
        embeddings = self.embedder.encode(messages, show_progress_bar=False)
        
        # Normalize embeddings for better cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create and populate FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.index.add(embeddings)
        
        # Store metadata with original indices
        self.metadata = chat_data
    
    def search(self, query, top_k=5):
        """Search the index with a text query"""
        query_embedding = self.embedder.encode([query], show_progress_bar=False)
        faiss.normalize_L2(query_embedding)
        
        # Perform the search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results in ChromaDB-like format for compatibility
        return {
            'documents': [[self.metadata[idx]["message"] for idx in indices[0]]],
            'metadatas': [[self.metadata[idx] for idx in indices[0]]],
            'distances': distances.tolist()
        }

def parse_chat(file_path, media_folder=None):
    """Parse WhatsApp chat file with basic media support"""
    chat_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                # Match WhatsApp message pattern
                match = re.match(
                    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(.+?):\s*(.*)$", 
                    line
                )
                if match:
                    date_str, time_str, sender, message = match.groups()
                    
                    # Determine media type
                    media_type = "text"
                    media_path = ""
                    if "<Media omitted>" in message:
                        media_type = "media"
                    
                    chat_data.append({
                        "message": message,
                        "sender": sender,
                        "timestamp": f"{date_str} {time_str}",
                        "media_type": media_type,
                        "media_path": media_path
                    })
    except Exception as e:
        logging.error(f"Error parsing chat: {str(e)}")
    
    return chat_data