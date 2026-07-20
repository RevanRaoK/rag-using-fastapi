import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RAG Document Q&A", layout='wide')
st.title("📚 RAG Document Assistant")

# Sidebar
st.sidebar.header("Document Upload")
uploaded_file = st.sidebar.file_uploader("Upload a TXT or PDF", type=['pdf', 'txt'])

if uploaded_file is not None:
    if st.sidebar.button("Process Document"):
        with st.spinner("Uploading & processing document..."):
            # Prepare file payload for FastAPI
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{API_URL}/uploadfile/", files=files)
            
            if response.status_code == 200:
                data = response.json()
                st.session_state["file_id"] = data["file_id"]
                st.session_state["filename"] = data["filename"]
                st.sidebar.success(f"Uploaded! Document ID: {data['file_id']}")
            else:
                st.sidebar.error(f"Error: {response.json().get('detail')}")

# Main Chat Interface
# Display current selected document
if "file_id" in st.session_state:
    st.info(f"Active Document: **{st.session_state['filename']}** (ID: {st.session_state['file_id']})")
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Question Input
    if question := st.chat_input("Ask a question about your document..."):
        # Display user question
        st.chat_message("user").markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})

        # Send request to FastAPI /ask/ endpoint
        with st.chat_message("assistant"):
            with st.spinner("Searching document & generating answer..."):
                payload = {
                    "document_id": st.session_state["file_id"],
                    "question": question
                }
                res = requests.post(f"{API_URL}/ask/", json=payload)
                
                if res.status_code == 200:
                    answer = res.json().get("response", "No response received.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"Failed to get response: {res.text}"
                    st.error(error_msg)
else:
    st.warning("Please upload and process a document in the sidebar to start asking questions.")
