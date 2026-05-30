import streamlit as st

from dotenv import load_dotenv

from utils.loader import load_youtube_transcript
from utils.vectorstore import create_vectorstore

from langchain_mistralai import (
    MistralAIEmbeddings,
    ChatMistralAI
)

from langchain_community.vectorstores import Chroma

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from utils.prompts import QA_SYSTEM_PROMPT

load_dotenv()

# ==========================================
# Page Config
# ==========================================

st.set_page_config(
    page_title="YouTube RAG Bot",
    page_icon="🎥",
    layout="wide"
)

# ==========================================
# Title
# ==========================================

st.title("🎥 YouTube Video Q&A Bot")

st.markdown(
    "Ask questions from any YouTube video transcript."
)

# ==========================================
# Session State
# ==========================================

if "chain" not in st.session_state:
    st.session_state.chain = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# Sidebar
# ==========================================

with st.sidebar:

    st.header("YouTube Video")

    youtube_url = st.text_input(
        "Paste YouTube URL"
    )

    process_button = st.button(
        "Process Video"
    )

# ==========================================
# Process Video
# ==========================================

if process_button:

    if not youtube_url:

        st.error("Please enter a YouTube URL")

    else:

        with st.spinner("Loading transcript..."):

            docs = load_youtube_transcript(
                youtube_url
            )

        if not docs:

            st.error(
                "Transcript not available"
            )

        else:

            with st.spinner(
                "Creating vector database..."
            ):

                vectorstore = create_vectorstore(
                    docs
                )

            # ==========================================
            # Retriever
            # ==========================================

            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 4,
                    "fetch_k": 10,
                    "lambda_mult": 0.5
                }
            )

            # ==========================================
            # LLM
            # ==========================================

            llm = ChatMistralAI(
                model="mistral-small-2506",
                temperature=0
            )

            # ==========================================
            # Prompt
            # ==========================================

            prompt = ChatPromptTemplate.from_template(
                QA_SYSTEM_PROMPT + """

Context:
{context}

Question:
{question}

Answer:
"""
            )

            # ==========================================
            # Output Parser
            # ==========================================

            output_parser = StrOutputParser()

            # ==========================================
            # Formatter
            # ==========================================

            def format_docs(docs):

                return "\n\n".join(
                    doc.page_content
                    for doc in docs
                )

            # ==========================================
            # LCEL Chain
            # ==========================================

            chain = (
                {
                    "context": retriever | format_docs,
                    "question": RunnablePassthrough()
                }
                | prompt
                | llm
                | output_parser
            )

            st.session_state.chain = chain

            st.success(
                "Video processed successfully!"
            )

# ==========================================
# Chat History
# ==========================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# ==========================================
# User Input
# ==========================================

query = st.chat_input(
    "Ask a question about the video"
)

# ==========================================
# Chat Logic
# ==========================================

if query:

    # Save User Message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    with st.chat_message("user"):

        st.markdown(query)

    # Check Chain
    if st.session_state.chain is None:

        with st.chat_message("assistant"):

            st.error(
                "Please process a video first."
            )

    else:

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                response = (
                    st.session_state.chain.invoke(
                        query
                    )
                )

                st.markdown(response)

        # Save AI Response
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )