import os
import re
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

def parse_chat(file_path):
    chat_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        message_pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(.+?):\s*(.*)$")

        for line in lines:
            match = message_pattern.match(line)
            if match:
                date_str, time_str, sender, message = match.groups()
                # Replace non-breaking space with regular space and normalize AM/PM
                time_str = time_str.replace('\u202f', ' ').strip().upper()
                try:
                    # Try parsing with short year (YY) and full year (YYYY)
                    for date_format in ["%m/%d/%y %I:%M %p", "%m/%d/%Y %I:%M %p"]:
                        try:
                            timestamp = datetime.strptime(f"{date_str} {time_str}", date_format)
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"Time data '{date_str} {time_str}' does not match expected formats")
                    
                    media_type = determine_media_type(message)
                    chat_data.append({
                        "message": message,
                        "sender": sender,
                        "timestamp": timestamp.isoformat(),
                        "media_type": media_type
                    })
                except ValueError as e:
                    logging.error(f"Error parsing line '{line.strip()}': {e}")
                    continue
    except Exception as e:
        logging.error(f"Error parsing chat file: {e}")

    return chat_data

def determine_media_type(message):
    if "<Media omitted>" in message or "attached" in message:
        if any(ext in message.lower() for ext in ['jpg', 'png', 'jpeg']):
            return "image"
        elif any(ext in message.lower() for ext in ['mp4', 'mov']):
            return "video"
        elif any(ext in message.lower() for ext in ['pdf']):
            return "pdf"
        elif any(ext in message.lower() for ext in ['pptx']):
            return "ppt"
        elif any(ext in message.lower() for ext in ['zip']):
            return "zip"
        else:
            return "document"
    return "text"

def get_chroma_client():
    return chromadb.Client(Settings(persist_directory="./chroma_store", anonymized_telemetry=False))

def build_vector_store(collection_name="whatsapp_chat", chat_data=None):
    client = get_chroma_client()
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = client.create_collection(name=collection_name, embedding_function=SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2"))

    if chat_data:
        messages = [item["message"] for item in chat_data]
        ids = [f"msg_{i}" for i in range(len(chat_data))]
        metadatas = [{"sender": item["sender"], "timestamp": item["timestamp"], "media_type": item["media_type"]} for item in chat_data]
        collection.add(documents=messages, ids=ids, metadatas=metadatas)

    return collection