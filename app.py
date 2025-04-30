import streamlit as st
from whatsapp_llm_utils import parse_chat, build_vector_store
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_chroma_client():
    return chromadb.Client(Settings(persist_directory="./chroma_store", anonymized_telemetry=False))

def search_messages(query, collection, top_k=5):
    query_embedding = embedding_model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    return results

def render_result(message, metadata):
    media_type = metadata.get("media_type", "text")
    st.markdown(f"**{metadata['sender']}** • {metadata['timestamp']}")

    if media_type == "image":
        st.image("🔗 Image (media omitted in text)", caption=message)
    elif media_type == "pdf":
        st.markdown(f"📄 [PDF] {message}")
    elif media_type == "ppt":
        st.markdown(f"📊 [PPT] {message}")
    elif media_type == "zip":
        st.markdown(f"🗜️ [ZIP] {message}")
    elif media_type == "video":
        st.markdown(f"🎥 [Video] {message}")
    else:
        st.write(message)

    st.markdown("---")

st.title("📱 WhatsApp Chat Search App")

uploaded_file = st.file_uploader("Upload your WhatsApp chat (.txt)", type=["txt"])

if uploaded_file:
    with open("chat.txt", "wb") as f:
        f.write(uploaded_file.read())

    st.success("Chat uploaded successfully!")
    chat_data = parse_chat("chat.txt")

    if not chat_data:
        st.error("No valid messages found in the chat file. Please check the file format.")
    else:
        with st.spinner("Embedding & building vector store..."):
            collection = build_vector_store(chat_data=chat_data)

        st.success("Ready to search!")

        query = st.text_input("Search your chat:")
        top_k = st.slider("Number of results to show", 1, 20, 5)

        if query:
            with st.spinner("Searching..."):
                results = search_messages(query, collection, top_k)
                if results['documents']:
                    for msg, metadata in zip(results['documents'][0], results['metadatas'][0]):
                        render_result(msg, metadata)
                else:
                    st.write("No results found for your query.")