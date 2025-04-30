import os
import re
import logging
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

def determine_media_type(message):
    if not message or message.strip() == "":
        return "text"
    if "<Media omitted>" in message or "attached" in message.lower():
        if any(ext in message.lower() for ext in ['jpg', 'png', 'jpeg']):
            return "image"
        elif any(ext in message.lower() for ext in ['mp4', 'mov']):
            return "video"
        elif any(ext in message.lower() for ext in ['pdf']):
            return "pdf"
        elif any(ext in message.lower() for ext in ['ppt', 'pptx']):
            return "ppt"
        elif any(ext in message.lower() for ext in ['opus']):
            return "audio"
        elif any(ext in message.lower() for ext in ['zip']):
            return "zip"
        else:
            return "media"
    return "text"

# def parse_chat(file_path, media_folder=None):
#     chat_data = []
#     media_files = []
    
#     # Find all media files in the directory
#     media_dir = media_folder if media_folder and os.path.exists(media_folder) else os.path.dirname(file_path)
    
#     # Look for media files in both main directory and 'Media' subfolder
#     search_dirs = [media_dir]
#     media_subdir = os.path.join(media_dir, "Media")
#     if os.path.exists(media_subdir):
#         search_dirs.append(media_subdir)
    
#     # Collect all media files
#     for search_dir in search_dirs:
#         for filename in os.listdir(search_dir):
#             # Match WhatsApp media file patterns including OPUS and PPT
#             match = re.match(
#                 r"^(IMG|VID|PTT|AUDIO)[-_](\d{8})[-_]WA(\d{4})\.(jpg|png|jpeg|mp4|mov|opus|ppt|pptx)$", 
#                 filename, 
#                 re.IGNORECASE
#             )
#             if match:
#                 media_type = match.group(1).upper()
#                 date_str = match.group(2)
#                 try:
#                     media_date = datetime.strptime(date_str, "%Y%m%d").date()
#                     file_type = "image" if media_type == "IMG" else \
#                               "video" if media_type == "VID" else \
#                               "ppt" if media_type == "PTT" else \
#                               "audio" if media_type == "AUDIO" else "media"
                    
#                     media_files.append({
#                         "path": os.path.join(search_dir, filename),
#                         "type": file_type,
#                         "date": media_date,
#                         "used": False
#                     })
#                 except ValueError:
#                     continue

#     # Sort media files by date
#     media_files.sort(key=lambda x: x["date"])

#     # Parse chat messages with multiple possible formats
#     date_formats = [
#         (r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(.+?):\s*(.*)$"),
#         (r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}:\d{2}\s*[APMapm]{2})\]\s*(.+?):\s*(.*)$"),
#         (r"^(\d{1,2}\.\d{1,2}\.\d{2,4}),?\s+(\d{1,2}:\d{2})\s*-\s*(.+?):\s*(.*)$"),
#         (r"^(\d{1,2}-\d{1,2}-\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(.+?):\s*(.*)$")
#     ]
    
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             lines = file.readlines()

#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue

#             matched = False
#             for pattern in date_formats:
#                 match = re.match(pattern, line)
#                 if match:
#                     date_str, time_str, sender, message = match.groups()
#                     time_str = time_str.replace('\u202f', ' ').strip().upper()
                    
#                     # Parse timestamp with multiple formats
#                     timestamp = None
#                     for date_format in [
#                         "%m/%d/%y %I:%M %p", "%m/%d/%Y %I:%M %p",
#                         "%d.%m.%y %H:%M", "%d-%m-%y %I:%M %p"
#                     ]:
#                         try:
#                             timestamp = datetime.strptime(f"{date_str} {time_str}", date_format)
#                             break
#                         except ValueError:
#                             continue
                    
#                     if not timestamp:
#                         continue
                    
#                     media_type = determine_media_type(message) or "text"
#                     media_path = ""
                    
#                     if media_type == "media" and media_files:
#                         message_date = timestamp.date()
#                         for media in media_files:
#                             if not media["used"] and media["date"] == message_date:
#                                 media_path = media["path"]
#                                 media_type = media["type"]
#                                 media["used"] = True
#                                 break

#                     chat_data.append({
#                         "message": message,
#                         "sender": sender,
#                         "timestamp": timestamp.isoformat(),
#                         "media_type": media_type,
#                         "media_path": media_path
#                     })
#                     matched = True
#                     break
            
#             if not matched and chat_data:
#                 chat_data[-1]["message"] += "\n" + line

#     except Exception as e:
#         logging.error(f"Error parsing chat file: {e}")
    
#     return chat_data if chat_data else None
def parse_chat(file_path, media_folder=None):
    chat_data = []
    media_files = []
    
    # Search for media in both main folder and 'Media' subfolder
    search_dirs = []
    if media_folder and os.path.exists(media_folder):
        search_dirs.append(media_folder)
    
    main_dir = os.path.dirname(file_path)
    search_dirs.append(main_dir)
    
    media_subdir = os.path.join(main_dir, "Media")
    if os.path.exists(media_subdir):
        search_dirs.append(media_subdir)

    # Collect all media files with their creation dates
    for search_dir in search_dirs:
        for filename in os.listdir(search_dir):
            filepath = os.path.join(search_dir, filename)
            if os.path.isfile(filepath):
                # Get both WhatsApp-style names and creation dates
                created_date = datetime.fromtimestamp(os.path.getctime(filepath)).date()
                
                # Match WhatsApp media patterns (old and new formats)
                match = re.match(r"^(IMG|VID|PTT|AUDIO)[-_](\d{8})[-_]WA(\d{0,4})", filename, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(2)
                        file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    except:
                        file_date = created_date
                else:
                    file_date = created_date
                
                # Determine file type
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png']:
                    file_type = "image"
                elif ext in ['.mp4', '.mov']:
                    file_type = "video"
                elif ext in ['.opus']:
                    file_type = "audio"
                elif ext in ['.ppt', '.pptx']:
                    file_type = "ppt"
                else:
                    file_type = "media"
                
                media_files.append({
                    "path": filepath,
                    "type": file_type,
                    "date": file_date,
                    "created": created_date,
                    "used": False
                })

    # Sort media files by date
    media_files.sort(key=lambda x: x["date"])

    # Parse chat messages
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        message_pattern = re.compile(
            r"^(\[?)(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})(\]?)[,\s]+(\d{1,2}:\d{2}(?::\d{2})?)\s*([APMapm]{2})?\s*[\]\-\s]+\s*(.+?):\s*(.*)$"
        )

        current_date = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to match message pattern
            match = message_pattern.match(line)
            if match:
                # Parse message components
                date_str = match.group(2)
                time_str = match.group(4)
                ampm = match.group(5)
                sender = match.group(6)
                message = match.group(7)

                # Standardize time format
                if ampm:
                    time_str = f"{time_str} {ampm.upper()}"
                
                # Parse timestamp with multiple possible formats
                timestamp = None
                for date_format in [
                    "%m/%d/%y %I:%M %p", "%m/%d/%Y %I:%M %p",
                    "%d/%m/%y %I:%M %p", "%d/%m/%Y %I:%M %p",
                    "%m-%d-%y %I:%M %p", "%d-%m-%y %I:%M %p",
                    "%m.%d.%y %H:%M", "%d.%m.%y %H:%M"
                ]:
                    try:
                        timestamp = datetime.strptime(f"{date_str} {time_str}", date_format)
                        break
                    except ValueError:
                        continue
                
                if not timestamp:
                    continue

                media_type = determine_media_type(message) or "text"
                media_path = ""
                
                # Match media files to messages
                if media_type == "media" and media_files:
                    message_date = timestamp.date()
                    
                    # Find closest matching media file
                    best_match = None
                    min_diff = float('inf')
                    
                    for media in media_files:
                        if not media["used"]:
                            date_diff = abs((media["date"] - message_date).days)
                            if date_diff < min_diff:
                                min_diff = date_diff
                                best_match = media
                    
                    if best_match and min_diff <= 1:  # Allow 1 day difference
                        media_path = best_match["path"]
                        media_type = best_match["type"]
                        best_match["used"] = True

                chat_data.append({
                    "message": message,
                    "sender": sender,
                    "timestamp": timestamp.isoformat(),
                    "media_type": media_type,
                    "media_path": media_path
                })
            elif chat_data:
                # Handle multi-line messages
                chat_data[-1]["message"] += "\n" + line

    except Exception as e:
        logging.error(f"Error parsing chat file: {e}")
    
    return chat_data if chat_data else None

def get_chroma_client():
    return chromadb.Client(Settings(persist_directory="./chroma_store", anonymized_telemetry=False))

def build_vector_store(collection_name="whatsapp_chat", chat_data=None):
    client = get_chroma_client()
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        embedding_function=SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    )

    if chat_data:
        messages = [item["message"] for item in chat_data]
        ids = [f"msg_{i}" for i in range(len(chat_data))]
        metadatas = []
        
        for item in chat_data:
            metadata = {
                "sender": str(item.get("sender", "")),
                "timestamp": str(item.get("timestamp", "")),
                "media_type": str(item.get("media_type", "text")),
                "media_path": str(item.get("media_path", ""))
            }
            metadatas.append(metadata)
        
        collection.add(documents=messages, ids=ids, metadatas=metadatas)

    return collection