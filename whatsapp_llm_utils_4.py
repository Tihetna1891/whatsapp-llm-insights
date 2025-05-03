# import os
# import re
# import logging
# import numpy as np
# from datetime import datetime
# from sentence_transformers import SentenceTransformer

# try:
#     import faiss
#     FAISS_AVAILABLE = True
# except ImportError:
#     FAISS_AVAILABLE = False
#     logging.warning("FAISS not available, falling back to numpy similarity")

# class VectorStore:
#     def __init__(self):
#         self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
#         self.embeddings = None
#         self.metadata = []
    
#     def build_index(self, chat_data):
#         messages = [item["message"] for item in chat_data]
#         self.embeddings = self.embedder.encode(messages, show_progress_bar=False)
#         self.metadata = chat_data
#         self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
    
#     def search(self, query, top_k=5):
#         query_embedding = self.embedder.encode([query], show_progress_bar=False)
#         query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
#         if FAISS_AVAILABLE:
#             dimension = self.embeddings.shape[1]
#             index = faiss.IndexFlatIP(dimension)
#             index.add(self.embeddings)
#             distances, indices = index.search(query_embedding, top_k)
#         else:
#             similarities = np.dot(self.embeddings, query_embedding.T).flatten()
#             indices = np.argpartition(similarities, -top_k)[-top_k:]
#             indices = indices[np.argsort(-similarities[indices])]
#             distances = similarities[indices]
#             indices = indices.reshape(1, -1)
#             distances = distances.reshape(1, -1)
        
#         return {
#             'documents': [[self.metadata[idx]["message"] for idx in indices[0]]],
#             'metadatas': [[self.metadata[idx] for idx in indices[0]]],
#             'distances': distances.tolist()
#         }

# def parse_chat(file_path, media_folder=None):
#     chat_data = []
#     media_files = []
    
#     # Scan for media files if folder exists
#     if media_folder and os.path.exists(media_folder):
#         for root, _, files in os.walk(media_folder):
#             for filename in files:
#                 filepath = os.path.join(root, filename)
#                 try:
#                     created_date = datetime.fromtimestamp(os.path.getctime(filepath)).date()
#                     file_type = get_file_type_simple(filename)
                    
#                     media_files.append({
#                         "path": filepath,
#                         "type": file_type,
#                         "date": created_date,
#                         "used": False
#                     })
#                 except:
#                     continue
    
#     # Parse chat file
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             for line in file:
#                 line = line.strip()
#                 if not line:
#                     continue
                
#                 # Match WhatsApp message patterns
#                 match = re.match(
#                     r"^(\[?)(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})(\]?)[,\s]+(\d{1,2}:\d{2}(?::\d{2})?)\s*([APMapm]{2})?\s*[\]\-\s]+\s*(.+?):\s*(.*)$",
#                     line
#                 )
#                 if match:
#                     date_str = match.group(2)
#                     time_str = match.group(4)
#                     ampm = match.group(5)
#                     sender = match.group(6)
#                     message = match.group(7)
                    
#                     # Parse timestamp
#                     timestamp = None
#                     for date_format in [
#                         "%m/%d/%y %I:%M %p", "%d/%m/%y %I:%M %p",
#                         "%m-%d-%y %I:%M %p", "%d-%m-%y %I:%M %p"
#                     ]:
#                         try:
#                             timestamp = datetime.strptime(f"{date_str} {time_str}{' ' + ampm if ampm else ''}", date_format)
#                             break
#                         except:
#                             continue
                    
#                     if not timestamp:
#                         continue
                    
#                     # Determine media type and match files
#                     media_type = "text"
#                     media_path = ""
                    
#                     if "<Media omitted>" in message or "attached" in message.lower():
#                         media_type = "media"
#                         message_date = timestamp.date()
                        
#                         # Find best matching media file
#                         best_match = None
#                         min_diff = float('inf')
                        
#                         for media in media_files:
#                             if not media["used"]:
#                                 date_diff = abs((media["date"] - message_date).days)
#                                 if date_diff < min_diff:
#                                     min_diff = date_diff
#                                     best_match = media
                        
#                         if best_match and min_diff <= 1:
#                             media_path = best_match["path"]
#                             media_type = best_match["type"]
#                             best_match["used"] = True
                    
#                     chat_data.append({
#                         "message": message,
#                         "sender": sender,
#                         "timestamp": timestamp.isoformat(),
#                         "media_type": media_type,
#                         "media_path": media_path
#                     })
#     except Exception as e:
#         logging.error(f"Error parsing chat: {str(e)}")
    
#     return chat_data

# def get_file_type_simple(filename):
#     """Simple file type detection based on extension"""
#     ext = os.path.splitext(filename)[1].lower()
#     if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
#         return "image"
#     elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
#         return "video"
#     elif ext in ['.pdf']:
#         return "pdf"
#     elif ext in ['.ppt', '.pptx']:
#         return "ppt"
#     elif ext in ['.opus', '.mp3', '.wav', '.m4a']:
#         return "audio"
#     elif ext in ['.zip', '.rar']:
#         return "archive"
#     else:
#         return "document"
import os
import re
import logging
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = None
        self.metadata = []
    
    def build_index(self, chat_data):
        messages = [item["message"] for item in chat_data]
        self.embeddings = self.embedder.encode(messages, show_progress_bar=False)
        self.metadata = chat_data
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
    
    def search(self, query, top_k=5):
        query_embedding = self.embedder.encode([query], show_progress_bar=False)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        indices = np.argpartition(similarities, -top_k)[-top_k:]
        indices = indices[np.argsort(-similarities[indices])]
        return {
            'documents': [[self.metadata[idx]["message"] for idx in indices]],
            'metadatas': [[self.metadata[idx] for idx in indices]],
            'distances': similarities[indices].tolist()
        }

def parse_whatsapp_timestamp(date_str, time_str):
    """Parse WhatsApp timestamps with multiple format support"""
    # Normalize time string (handle special space characters)
    time_str = time_str.replace('\u202f', ' ').replace('\xa0', ' ').strip()
    
    # Try multiple date formats
    date_formats = [
        "%d/%m/%Y %I:%M %p",  # 14/03/2025 6:49 pm
        "%d/%m/%y %I:%M %p",   # 14/03/25 6:49 pm
        "%m/%d/%Y %I:%M %p",   # 03/14/2025 6:49 pm (US format)
        "%d-%m-%Y %I:%M %p",   # 14-03-2025 6:49 pm
        "%d.%m.%Y %I:%M %p",   # 14.03.2025 6:49 pm
        "%Y-%m-%d %I:%M %p",   # 2025-03-14 6:49 pm
        "%d/%m/%Y %H:%M",      # 14/03/2025 18:49 (24-hour format)
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(f"{date_str} {time_str}", fmt)
        except ValueError:
            continue
    
    logger.warning(f"Couldn't parse timestamp: {date_str} {time_str}")
    return None

def parse_chat(file_path, media_folder=None):
    """Robust WhatsApp chat parser that handles all common formats"""
    chat_data = []
    media_files = []
    
    # Collect media files
    if media_folder and os.path.exists(media_folder):
        for root, _, files in os.walk(media_folder):
            for file in files:
                if not file.lower().endswith('.txt'):
                    try:
                        filepath = os.path.join(root, file)
                        created_date = datetime.fromtimestamp(os.path.getctime(filepath)).date()
                        media_files.append({
                            "path": filepath,
                            "date": created_date,
                            "used": False
                        })
                    except Exception as e:
                        logger.warning(f"Couldn't process media file {filepath}: {e}")

    # WhatsApp message patterns (supports all common formats)
    patterns = [
        # Format: 14/03/2025, 6:49 pm - John: Message
        r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[apmAPM]{2})\s*-\s*(.+?):\s*(.*)$",
        # Format: [14/03/2025, 6:49:00 pm] John: Message
        r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}:\d{2}\s*[apmAPM]{2})\]\s*(.+?):\s*(.*)$",
        # Format: 14-03-2025 6:49 pm - John: Message
        r"^(\d{1,2}-\d{1,2}-\d{2,4})\s+(\d{1,2}:\d{2}\s*[apmAPM]{2})\s*-\s*(.+?):\s*(.*)$",
        # Format: 14.03.2025, 6:49 pm - John: Message
        r"^(\d{1,2}\.\d{1,2}\.\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[apmAPM]{2})\s*-\s*(.+?):\s*(.*)$",
        # Format with special space characters
        r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[apmAPM]{2}\u202f)\s*-\s*(.+?):\s*(.*)$",
    ]

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            line_buffer = []
            
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                matched = False
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        date_str = match.group(1)
                        time_str = match.group(2)
                        sender = match.group(3)
                        message = match.group(4)
                        
                        # Parse timestamp
                        timestamp = parse_whatsapp_timestamp(date_str, time_str)
                        if not timestamp:
                            continue
                        
                        # Handle multi-line messages
                        if line_buffer:
                            prev_msg = chat_data[-1]
                            prev_msg["message"] += "\n" + "\n".join(line_buffer)
                            line_buffer = []
                        
                        # Media detection
                        media_type = "text"
                        media_path = ""
                        if "<Media omitted>" in message or "attached" in message.lower():
                            media_type = "media"
                            message_date = timestamp.date()
                            
                            # Find closest media file
                            for media in media_files:
                                if not media["used"] and abs((media["date"] - message_date).days) <= 1:
                                    media_path = media["path"]
                                    media["used"] = True
                                    break
                        
                        chat_data.append({
                            "message": message,
                            "sender": sender,
                            "timestamp": timestamp.isoformat(),
                            "media_type": media_type,
                            "media_path": media_path
                        })
                        matched = True
                        break
                
                if not matched:
                    # System messages (like "X created group")
                    if " created group " in line or " joined using " in line:
                        timestamp_match = re.match(r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[apmAPM]{2})\s*-\s*(.*)$", line)
                        if timestamp_match:
                            date_str = timestamp_match.group(1)
                            time_str = timestamp_match.group(2)
                            message = timestamp_match.group(3)
                            
                            timestamp = parse_whatsapp_timestamp(date_str, time_str)
                            if timestamp:
                                chat_data.append({
                                    "message": message,
                                    "sender": "System",
                                    "timestamp": timestamp.isoformat(),
                                    "media_type": "text",
                                    "media_path": ""
                                })
                                matched = True
                    
                    if not matched:
                        line_buffer.append(line)
            
            # Handle any remaining buffered lines
            if line_buffer and chat_data:
                chat_data[-1]["message"] += "\n" + "\n".join(line_buffer)
    
    except UnicodeDecodeError:
        try:
            # Try UTF-16 encoding if UTF-8 fails
            with open(file_path, 'r', encoding='utf-16') as file:
                return parse_chat_from_file(file, media_files)
        except Exception as e:
            logger.error(f"Failed to read file with UTF-16: {str(e)}")
    except Exception as e:
        logger.error(f"Error parsing chat file: {str(e)}")
    
    return chat_data

def parse_chat_from_file(file, media_files):
    """Helper function to parse chat from already opened file"""
    chat_data = []
    line_buffer = []
    patterns = [
        r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[apmAPM]{2})\s*-\s*(.+?):\s*(.*)$",
        # Add other patterns as needed
    ]

    for line in file:
        line = line.strip()
        if not line:
            continue
        
        matched = False
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                sender = match.group(3)
                message = match.group(4)
                
                timestamp = parse_whatsapp_timestamp(date_str, time_str)
                if not timestamp:
                    continue
                
                if line_buffer:
                    chat_data[-1]["message"] += "\n" + "\n".join(line_buffer)
                    line_buffer = []
                
                chat_data.append({
                    "message": message,
                    "sender": sender,
                    "timestamp": timestamp.isoformat(),
                    "media_type": "text",
                    "media_path": ""
                })
                matched = True
                break
        
        if not matched:
            line_buffer.append(line)
    
    if line_buffer and chat_data:
        chat_data[-1]["message"] += "\n" + "\n".join(line_buffer)
    
    return chat_data