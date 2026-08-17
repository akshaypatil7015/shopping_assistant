import sys
from pathlib import Path

import streamlit as st


# ------------------------------------------------------------
# PROJECT PATH
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------
# IMPORT EXISTING SHOPPING ASSISTANT
# ------------------------------------------------------------

from assistant import (
    generate_answer,
    conversation_history,
)


# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------

st.set_page_config(
    page_title="AI Shopping Assistant",
    page_icon="🛍️",
    layout="wide",
)


# ------------------------------------------------------------
# TITLE
# ------------------------------------------------------------

st.title("🛍️ AI Shopping Assistant")

st.write(
    "Find smartphones using hybrid search, RRF, "
    "cross-encoder re-ranking, RAG, and an LLM."
)


# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# DISPLAY PREVIOUS MESSAGES
# ------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------------------------------------------------
# USER INPUT
# ------------------------------------------------------------

user_query = st.chat_input(
    "Example: Suggest me a Samsung smartphone under ₹50,000"
)


# ------------------------------------------------------------
# PROCESS USER QUERY
# ------------------------------------------------------------

if user_query:

    # Show user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate assistant response
    with st.chat_message("assistant"):

        with st.spinner(
            "Searching products and generating recommendation..."
        ):

            try:

                answer = generate_answer(
                    user_query=user_query,
                    top_k=5,
                )

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as e:

                st.error(
                    f"Something went wrong: {str(e)}"
                )


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

with st.sidebar:

    st.header("🛍️ Shopping Assistant")

    st.write(
        """
        This application uses:

        • Vector Search  
        • BM25 Keyword Search  
        • Hybrid Search  
        • RRF Fusion  
        • Cross-Encoder Re-ranking  
        • RAG  
        • LLM
        """
    )

    st.divider()

    st.subheader("Conversation")

    if st.button("Clear conversation"):

        st.session_state.messages = []

        conversation_history.clear()

        st.rerun()