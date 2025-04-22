# WhatsApp Chat to Notebook LLM - Colab-Ready Interactive App
# Install requirements in Colab:
# !pip install pandas sentence-transformers chromadb opencv-python pytesseract langchain pillow transformers gradio
import os 
import re 
import pandas as pd 
import pytesseract 
import cv2 
from PIL import Image 
from datetime import datetime 
from sentence_transformers import SentenceTransformer
import chromadb 
from chromadb.utils import embedding_functions 
from transformers import pipeline 
import gradio as gr
# 1. Parse WhatsApp Chat Export
def parse_whatsapp_chat(chat_path): 
    with open(chat_path, encoding="utf-8") as f: 
        lines = f.readlines()
    chat_data = [] 
    for line in lines: 
        match = re.match(r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - ([^:]+): (.+)$", line) 
        if match: 
            date_str, time_str, sender, message = match.groups() 
            try: 
                timestamp = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%y %H:%M") 
            except: 
                continue 
            chat_data.append({"timestamp": timestamp, "sender": sender, "message": message}) 
    return pd.DataFrame(chat_data) 
# 2. Extract Text from Images
def extract_text_from_images(media_folder): 
    media_texts = [] 
    for fname in os.listdir(media_folder): 
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')): 
            path = os.path.join(media_folder, fname) 
            img = cv2.imread(path) 
            text = pytesseract.image_to_string(img) 
            media_texts.append({"timestamp": None, "sender": "MediaOCR", "message": text.strip()}) 
    return pd.DataFrame(media_texts)
# 3. Embed Messages
def embed_messages(df): 
    model = SentenceTransformer('all-MiniLM-L6-v2') 
    df['embedding'] = df['message'].apply(lambda x: model.encode(x)) 
    return df
# 4. Store in ChromaDB
def store_in_chromadb(df): 
    chroma_client = chromadb.Client() 
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2") 
    collection = chroma_client.create_collection(name="whatsapp_chat", embedding_function=embed_fn)
    for i, row in df.iterrows(): 
        collection.add( 
            ids=[str(i)], 
            documents=[row['message']], 
            metadatas=[{"sender": row['sender'], "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None}] ) 
    return collection 
# 5. Semantic Search
def search_messages(collection, query, k=5): 
    results = collection.query(query_texts=[query], n_results=k) 
    return results
# 6. Summary
def summarize_texts(texts): 
    summarizer = pipeline("summarization") 
    joined_text = " ".join(texts) 
    summary = summarizer(joined_text[:1000], max_length=130, min_length=30, do_sample=False) 
    return summary[0]['summary_text']
# 7. Gradio Interface
chat_df = None 
collection = None
def initialize_pipeline(chat_file, media_folder_path): 
    global chat_df, collection 
    with open("uploaded_chat.txt", "w", encoding="utf-8") as f:
        f.write(chat_file.read().decode("utf-8"))
    df_chat = parse_whatsapp_chat("uploaded_chat.txt") 
    df_media = extract_text_from_images(media_folder_path) 
    df_all = pd.concat([df_chat, df_media], ignore_index=True) 
    df_all = embed_messages(df_all) 
    collection = store_in_chromadb(df_all) 
    chat_df = df_all 
    return "Data processed and ready for querying." 
def query_and_summarize(prompt): 
    if collection is None: 
        return "Please initialize first."
    results = search_messages(collection, prompt) 
    docs = results['documents'][0] 
    summary = summarize_texts(docs) 
    return f"\nTop Results:\n" + "\n\n".join(docs) + f"\n\nSummary:\n{summary}"
iface = gr.Interface( 
    fn=query_and_summarize, 
    inputs="text", 
    outputs="text", 
    title="WhatsApp Semantic Search + Summary" 
    )
uploader = gr.Interface( 
    fn=initialize_pipeline, 
    inputs=[gr.File(label="Upload WhatsApp Chat (.txt)"), gr.Textbox(label="Path to Media Folder")],
    outputs="text", 
    title="Initialize WhatsApp Chat Parser" 
    )
app = gr.TabbedInterface([uploader, iface], ["Upload Chat & Media", "Query & Summarize"])
if __name__ == "main": 
    app.launch(server_name = "0.0.0.0",server_port=7860, share= True )
    print("hi")