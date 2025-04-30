import streamlit as st
from whatsapp_llm_utils_2 import parse_chat, build_vector_store
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os
import zipfile
import shutil
import re

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_chroma_client():
    return chromadb.Client(Settings(persist_directory="./chroma_store", anonymized_telemetry=False))

def search_messages(query, collection, top_k=5):
    query_embedding = embedding_model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    return results

# def render_result(message, metadata):
#     media_type = metadata.get("media_type", "text")
#     media_path = metadata.get("media_path", "")
    
#     st.markdown(f"**{metadata['sender']}** • {metadata['timestamp']}")
    
#     if media_path and os.path.exists(media_path):
#         try:
#             if media_type == "image":
#                 st.image(media_path, caption=message)
#             elif media_type == "video":
#                 st.video(media_path)
#             elif media_type == "ppt":
#                 st.markdown(f"📊 [PowerPoint] {message}")
#                 st.markdown(f"`{os.path.basename(media_path)}`")
#             elif media_type == "audio":
#                 st.audio(media_path)
#                 st.markdown(f"🎤 {message}")
#             elif media_type == "pdf":
#                 st.markdown(f"📄 [PDF] {message}")
#             elif media_type == "zip":
#                 st.markdown(f"🗜️ [ZIP] {message}")
#             else:
#                 st.markdown(f"📎 {message}")
#         except Exception as e:
#             st.error(f"Error displaying media: {str(e)}")
#             st.markdown(f"📎 [Media] {message}")
#     else:
#         if media_type == "ppt":
#             st.markdown(f"📊 [PPT] {message}")
#         elif media_type == "audio":
#             st.markdown(f"🎤 [Voice Message] {message}")
#         elif media_type == "media":
#             st.markdown(f"📎 [Media] {message}")
#         else:
#             st.write(message)
    
#     st.markdown("---")
def render_result(message, metadata):
    media_type = metadata.get("media_type", "text")
    media_path = metadata.get("media_path", "")
    
    st.markdown(f"**{metadata['sender']}** • {metadata['timestamp']}")
    
    if media_path and os.path.exists(media_path):
        try:
            if media_type == "image":
                st.image(media_path, caption=message, use_column_width=True)
            elif media_type == "video":
                st.video(open(media_path, 'rb').read())
            elif media_type == "audio":
                st.audio(open(media_path, 'rb').read())
            elif media_type == "ppt":
                st.markdown(f"📊 [PowerPoint] {message}")
                with open(media_path, "rb") as file:
                    st.download_button(
                        label="Download PPT",
                        data=file,
                        file_name=os.path.basename(media_path),
                        mime="application/vnd.ms-powerpoint"
                    )
            else:
                st.markdown(f"📎 [Media File] {os.path.basename(media_path)}")
                with open(media_path, "rb") as file:
                    st.download_button(
                        label="Download File",
                        data=file,
                        file_name=os.path.basename(media_path)
                    )
        except Exception as e:
            st.error(f"Error displaying media: {str(e)}")
            st.markdown(f"📎 [Media] {message}")
    else:
        if media_type == "media":
            st.markdown(f"📎 [Media] {message}")
            st.warning("Media file not found. Possible reasons:")
            st.write("1. Media wasn't included in the export")
            st.write("2. File was renamed or moved")
            st.write("3. Export didn't preserve media links")
        else:
            st.write(message)
    
    st.markdown("---")

st.title("📱 WhatsApp Chat Search App")

uploaded_zip = st.file_uploader("Upload your WhatsApp chat export (.zip)", type=["zip"])

if uploaded_zip:
    temp_dir = "temp_chat_extract"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    zip_path = os.path.join(temp_dir, "chat.zip")
    with open(zip_path, "wb") as f:
        f.write(uploaded_zip.read())

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    chat_file_path = None
    media_folder = None
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".txt"):
                potential_chat_file = os.path.join(root, file)
                try:
                    with open(potential_chat_file, 'r', encoding='utf-8') as f:
                        first_lines = [f.readline() for _ in range(5)]
                    st.text_area("First lines of chat file:", value="\n".join(first_lines), height=150)
                    chat_file_path = potential_chat_file
                    media_folder = os.path.dirname(chat_file_path)
                    break
                except Exception as e:
                    st.warning(f"Could not read {file}: {e}")

        if "Media" in dirs:
            media_folder = os.path.join(root, "Media")

    if not chat_file_path:
        st.error("No valid chat file found in the ZIP.")
    else:
        chat_data = parse_chat(chat_file_path, media_folder)
        
        if not chat_data:
            st.error("""
            No messages parsed. Possible issues:
            1. Unsupported chat format
            2. Corrupted export file
            3. Encoding issues
            """)
        else:
            with st.spinner("Processing chat data..."):
                collection = build_vector_store(chat_data=chat_data)
                st.success(f"Processed {len(chat_data)} messages!")

            query = st.text_input("Search your chat:")
            top_k = st.slider("Number of results", 1, 20, 5)

            if query:
                with st.spinner("Searching..."):
                    results = search_messages(query, collection, top_k)
                    if results['documents']:
                        for msg, metadata in zip(results['documents'][0], results['metadatas'][0]):
                            render_result(msg, metadata)
                    else:
                        st.info("No results found")

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)