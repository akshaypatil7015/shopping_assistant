import streamlit as st

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
    "re-ranking, RAG, and an LLM."
)


# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# DISPLAY CHAT HISTORY
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
# PROCESS QUERY
# ------------------------------------------------------------

if user_query:

    # Display user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate response
    with st.chat_message("assistant"):

        with st.spinner("Searching products and generating recommendation..."):

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

                error_message = f"Error: {e}"

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

with st.sidebar:

    st.header("About")

    st.write(
        """
        This AI Shopping Assistant uses:

        - Vector Search
        - BM25 Keyword Search
        - Hybrid Search
        - RRF Fusion
        - Cross-Encoder Re-ranking
        - RAG
        - LLM
        """
    )

    st.divider()

    st.subheader("Conversation")

    if st.button("Clear conversation"):

        st.session_state.messages = []

        conversation_history.clear()

        st.rerun()