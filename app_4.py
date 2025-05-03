# import streamlit as st
# import os
# import zipfile
# import tempfile
# import shutil
# from whatsapp_llm_utils_4 import parse_chat, VectorStore

# # App configuration
# st.set_page_config(page_title="WhatsApp Archive Search", layout="wide")
# st.title("📁 WhatsApp Chat Explorer")

# # Initialize session state
# if 'vector_store' not in st.session_state:
#     st.session_state.vector_store = VectorStore()
#     st.session_state.chat_processed = False

# # File upload section
# with st.sidebar:
#     st.header("1. Upload Archive")
#     uploaded_zip = st.file_uploader(
#         "Choose WhatsApp .zip export", 
#         type=["zip"],
#         help="Export your chat WITH MEDIA from WhatsApp mobile app"
#     )
    
#     if uploaded_zip:
#         st.info("💡 Processing may take a few minutes for large chats")

# # Main processing logic
# if uploaded_zip and not st.session_state.chat_processed:
#     with st.spinner("Extracting and processing your chat archive..."):
#         # Create temp directory
#         temp_dir = tempfile.mkdtemp()
        
#         try:
#             # Save and extract ZIP
#             zip_path = os.path.join(temp_dir, "whatsapp_export.zip")
#             with open(zip_path, "wb") as f:
#                 f.write(uploaded_zip.getvalue())
            
#             with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#                 zip_ref.extractall(temp_dir)
            
#             # Find chat file and media folder
#             chat_file = None
#             media_folder = None
            
#             for root, dirs, files in os.walk(temp_dir):
#                 # Look for chat file
#                 for file in files:
#                     if file.lower().endswith('.txt'):
#                         # Verify it's a WhatsApp chat file
#                         with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
#                             first_line = f.readline()
#                             if any(pattern in first_line for pattern in [' - ', '] ']):  # Common WhatsApp patterns
#                                 chat_file = os.path.join(root, file)
#                                 media_folder = root  # Default media location
#                                 break
                
#                 # Look for media folder
#                 if 'Media' in dirs:
#                     media_folder = os.path.join(root, 'Media')
            
#             if not chat_file:
#                 st.error("Could not find a valid WhatsApp chat file in the archive")
#             else:
#                 # Parse chat with media
#                 chat_data = parse_chat(chat_file, media_folder)
                
#                 if not chat_data:
#                     st.error("No messages could be parsed from the chat file")
#                 else:
#                     # Build search index
#                     st.session_state.vector_store.build_index(chat_data)
#                     st.session_state.chat_processed = True
#                     st.session_state.media_folder = media_folder
#                     st.success(f"✅ Processed {len(chat_data)} messages with media attachments")
                    
#                     # Show sample of parsed data
#                     with st.expander("Show first 5 messages"):
#                         for msg in chat_data[:5]:
#                             st.write(f"**{msg['sender']}** ({msg['timestamp']}):")
#                             if msg['media_type'] != 'text' and msg['media_path']:
#                                 st.caption(f"Media: {os.path.basename(msg['media_path'])}")
#                             st.write(msg['message'])
#                             st.divider()
        
#         except Exception as e:
#             st.error(f"Error processing archive: {str(e)}")
#         finally:
#             # Clean up temp files (keeping media references)
#             try:
#                 shutil.rmtree(temp_dir)
#             except:
#                 pass

# # Search interface (only show if processing complete)
# if st.session_state.chat_processed:
#     st.header("2. Search Your Archive")
    
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         query = st.text_input(
#             "Enter your search query", 
#             placeholder="E.g. 'photos from vacation'"
#         )
#     with col2:
#         top_k = st.selectbox("Results to show", [3, 5, 10], index=1)
    
#     if query:
#         with st.spinner(f"Searching through your messages..."):
#             results = st.session_state.vector_store.search(query, top_k)
        
#         if results['documents']:
#             st.subheader(f"Top {len(results['documents'][0])} Results")
            
#             for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
#                 with st.container():
#                     # Header with sender and timestamp
#                     st.write(f"**{meta['sender']}** • `{meta['timestamp']}`")
                    
#                     # Media display
#                     if meta['media_type'] != 'text' and meta['media_path']:
#                         if os.path.exists(meta['media_path']):
#                             try:
#                                 if meta['media_type'] == 'image':
#                                     st.image(
#                                         meta['media_path'],
#                                         caption=doc,
#                                         use_column_width=True
#                                     )
#                                 elif meta['media_type'] == 'video':
#                                     st.video(meta['media_path'])
#                                 elif meta['media_type'] == 'audio':
#                                     st.audio(meta['media_path'])
#                                 else:
#                                     with open(meta['media_path'], "rb") as f:
#                                         st.download_button(
#                                             label=f"Download {meta['media_type'].upper()} file",
#                                             data=f,
#                                             file_name=os.path.basename(meta['media_path'])
#                                         )
#                             except Exception as e:
#                                 st.error(f"Couldn't display media: {str(e)}")
#                                 st.write(doc)
#                         else:
#                             st.warning("Media file not found in archive")
#                             st.write(doc)
#                     else:
#                         # Regular text message
#                         st.write(doc)
                    
#                     # Relevance indicator
#                     relevance = (1 - results['distances'][0][i]) * 100
#                     st.progress(
#                         int(relevance),
#                         text=f"Match: {relevance:.0f}%"
#                     )
                    
#                     st.divider()
#         else:
#             st.info("No matching messages found")

# # Initial instructions
# else:
#     st.markdown("""
#     ## How to use this explorer:
    
#     1. **Export your WhatsApp chat** from your phone:
#        - Open the conversation
#        - Tap ⋮ → More → Export chat
#        - Select **INCLUDE MEDIA**
#        - Share/Save the .zip file
    
#     2. **Upload the .zip file** using the panel on the left
    
#     3. **Search your messages** once processing completes
    
#     ⚠️ **Note:** 
#     - First-time processing may take several minutes
#     - Very large chats (>10,000 messages) may require more time
#     - Media files are extracted temporarily during processing
#     """)

# # Add some custom styling
# st.markdown("""
# <style>
#     /* Improve spacing and readability */
#     .st-emotion-cache-1y4p8pa {
#         padding: 2rem;
#     }
    
#     /* Style the progress bars */
#     .st-emotion-cache-1m7p7oq {
#         background-color: #4CAF50;
#     }
    
#     /* Better container borders */
#     .st-emotion-cache-1hynsf2 {
#         border: 1px solid #e0e0e0;
#         border-radius: 8px;
#         padding: 1rem;
#         margin-bottom: 1rem;
#     }
    
#     /* Download button styling */
#     .stDownloadButton button {
#         width: 100%;
#         margin-top: 0.5rem;
#     }
# </style>
# """, unsafe_allow_html=True)
import streamlit as st
import os
import zipfile
import tempfile
import shutil
from whatsapp_llm_utils_4 import parse_chat, VectorStore

# Configure page
st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="📱",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f9f9f9;
        margin-bottom: 1rem;
        border-left: 4px solid #4CAF50;
    }
    .system-message {
        border-left: 4px solid #2196F3;
    }
    .media-message {
        border-left: 4px solid #FF9800;
    }
    .timestamp {
        color: #757575;
        font-size: 0.9rem;
    }
    .sender {
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📱 WhatsApp Chat Explorer")
    st.caption("Search through your WhatsApp exports with media attachments")

    # Initialize session state
    if 'vs' not in st.session_state:
        st.session_state.vs = VectorStore()
        st.session_state.chat_data = None
        st.session_state.temp_dir = None

    # File upload
    uploaded_file = st.file_uploader(
        "Upload WhatsApp Export (ZIP or TXT)",
        type=["zip", "txt"],
        help="Export your chat WITH MEDIA from WhatsApp mobile app"
    )

    # Processing
    if uploaded_file and st.session_state.chat_data is None:
        with st.spinner("Processing your WhatsApp export..."):
            try:
                # Create temp directory
                temp_dir = tempfile.mkdtemp()
                st.session_state.temp_dir = temp_dir
                
                # Save uploaded file
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Handle ZIP or TXT
                if uploaded_file.name.lower().endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    os.remove(file_path)  # Remove the zip after extraction
                
                # Find chat file
                chat_file = None
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith('.txt'):
                            potential_chat = os.path.join(root, file)
                            try:
                                with open(potential_chat, 'r', encoding='utf-8') as f:
                                    first_line = f.readline()
                                    if any(p in first_line for p in [' - ', '] ']):
                                        chat_file = potential_chat
                                        break
                            except UnicodeDecodeError:
                                try:
                                    with open(potential_chat, 'r', encoding='utf-16') as f:
                                        first_line = f.readline()
                                        if any(p in first_line for p in [' - ', '] ']):
                                            chat_file = potential_chat
                                            break
                                except:
                                    continue
                
                if not chat_file:
                    st.error("No valid WhatsApp chat file found in the export")
                else:
                    # Parse chat with all found media files
                    st.session_state.chat_data = parse_chat(chat_file, temp_dir)
                    
                    if not st.session_state.chat_data:
                        st.error("""
                        No messages could be parsed. Possible reasons:
                        - Unsupported chat format
                        - Corrupted export file
                        - Encoding issues
                        """)
                        # Show file preview for debugging
                        with st.expander("Show file preview"):
                            try:
                                with open(chat_file, 'r', encoding='utf-8') as f:
                                    st.text(f.read(1000))
                            except:
                                try:
                                    with open(chat_file, 'r', encoding='utf-16') as f:
                                        st.text(f.read(1000))
                                except Exception as e:
                                    st.error(f"Couldn't read file: {str(e)}")
                    else:
                        st.session_state.vs.build_index(st.session_state.chat_data)
                        st.success(f"✅ Successfully processed {len(st.session_state.chat_data)} messages")
                        
                        # Show statistics
                        with st.expander("📊 Chat Statistics"):
                            senders = list(set(msg['sender'] for msg in st.session_state.chat_data))
                            st.write(f"**Participants:** {', '.join(senders)}")
                            st.write(f"**Time range:** {st.session_state.chat_data[0]['timestamp']} to {st.session_state.chat_data[-1]['timestamp']}")
                            media_count = sum(1 for msg in st.session_state.chat_data if msg['media_type'] != 'text')
                            st.write(f"**Media files:** {media_count}")
            
            except Exception as e:
                st.error(f"Error processing archive: {str(e)}")
                if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
                    shutil.rmtree(st.session_state.temp_dir)

    # Search interface
    if st.session_state.chat_data:
        st.header("🔍 Search Messages")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input(
                "Search your chat",
                placeholder="Type your search query..."
            )
        with col2:
            top_k = st.selectbox("Results to show", [3, 5, 10], index=1)
        
        if query:
            with st.spinner("Searching..."):
                results = st.session_state.vs.search(query, top_k)
            
            if results['documents']:
                st.subheader(f"Top {len(results['documents'][0])} Results")
                
                for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    # Determine message type for styling
                    message_class = "chat-message"
                    if meta['sender'] == "System":
                        message_class += " system-message"
                    elif meta['media_type'] != 'text':
                        message_class += " media-message"
                    
                    # Display message
                    st.markdown(f"""
                    <div class="{message_class}">
                        <div class="sender">{meta['sender']}</div>
                        <div class="timestamp">{meta['timestamp']}</div>
                        <p>{doc}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display media if available
                    if meta['media_type'] != 'text' and meta['media_path']:
                        if os.path.exists(meta['media_path']):
                            try:
                                if meta['media_type'] == 'image':
                                    st.image(meta['media_path'], use_column_width=True)
                                elif meta['media_type'] == 'video':
                                    st.video(meta['media_path'])
                                elif meta['media_type'] == 'audio':
                                    st.audio(meta['media_path'])
                                else:
                                    with open(meta['media_path'], "rb") as f:
                                        st.download_button(
                                            label=f"Download {meta['media_type']} file",
                                            data=f,
                                            file_name=os.path.basename(meta['media_path']))
                            except Exception as e:
                                st.error(f"Couldn't display media: {str(e)}")
                        else:
                            st.warning("Associated media file not found in archive")
                    
                    # Relevance indicator
                    relevance = (1 - results['distances'][0][i]) * 100
                    st.progress(
                        int(relevance),
                        text=f"Relevance: {relevance:.0f}%"
                    )
            else:
                st.info("No matching messages found")

    # Initial instructions
    else:
        st.markdown("""
        ## How to use this explorer:
        
        1. **Export your chat** from WhatsApp mobile:
           - Open conversation → ⋮ → More → Export chat
           - Select **Include media**
           - Share/Save the .zip file
        
        2. **Upload the export file** above
        
        3. **Search** through your messages
        
        ### Supported formats:
        - All common WhatsApp date formats (DD/MM/YYYY, MM/DD/YYYY, etc.)
        - Both 12-hour and 24-hour time formats
        - System messages (group creation, joins, etc.)
        - Media attachments (images, videos, audio, documents)
        """)

    # Clean up
    if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)

if __name__ == "__main__":
    main()