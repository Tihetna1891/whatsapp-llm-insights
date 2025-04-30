import streamlit as st
import os
import tempfile
from whatsapp_llm_utils_3 import parse_chat, VectorStore

# App configuration
st.set_page_config(page_title="WhatsApp Chat Search", layout="wide")
st.title("🔍 WhatsApp Chat Search with FAISS")

# Initialize vector store in session state
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = VectorStore()

# File upload section
with st.sidebar:
    st.header("Upload Chat")
    uploaded_file = st.file_uploader(
        "Choose WhatsApp export (.txt)", 
        type="txt",
        help="Export your chat without media for best results"
    )

# Processing and search UI
if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    # Parse chat
    with st.spinner("Parsing chat messages..."):
        chat_data = parse_chat(tmp_path)
    
    if chat_data:
        st.success(f"✅ Parsed {len(chat_data)} messages")
        
        # Build index
        with st.spinner("Building search index (this may take a minute)..."):
            st.session_state.vector_store.build_index(chat_data)
            st.success("Search ready!")
        
        # Search interface
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("Search your chat", placeholder="Type your query...")
        with col2:
            top_k = st.selectbox("Results to show", [3, 5, 10, 20], index=1)
        
        if query:
            with st.spinner("Searching..."):
                results = st.session_state.vector_store.search(query, top_k)
            
            if results['documents']:
                st.subheader(f"Top {len(results['documents'][0])} results")
                for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    with st.expander(f"Result {i+1} - {meta['sender']} ({meta['timestamp']})"):
                        if meta['media_type'] == "media":
                            st.markdown("📎 Media file")
                        st.write(doc)
                        st.caption(f"Similarity score: {1 - results['distances'][0][i]:.2f}")
            else:
                st.warning("No results found")
    
    # Clean up
    os.unlink(tmp_path)
else:
    st.info("👈 Upload a WhatsApp chat export to begin")
    st.markdown("""
    ### How to export your chat:
    1. Open WhatsApp conversation
    2. Tap ⋮ > More > Export chat
    3. Choose **Without media**
    4. Upload the resulting .txt file here
    """)

# Add some styling
st.markdown("""
<style>
    .st-emotion-cache-1y4p8pa {
        padding: 2rem;
    }
    .st-emotion-cache-1y4p8pa {
        max-width: 1200px;
    }
</style>
""", unsafe_allow_html=True)