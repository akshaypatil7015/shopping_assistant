import streamlit as st

from assistant import generate_answer

from monitoring import (
    log_request,
    save_feedback,
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

if "current_request_id" not in st.session_state:
    st.session_state.current_request_id = None

if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False


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

    # --------------------------------------------------------
    # Reset feedback state for new response
    # --------------------------------------------------------

    st.session_state.current_request_id = None
    st.session_state.feedback_given = False

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # --------------------------------------------------------
    # Generate assistant response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching products and generating recommendation..."
        ):

            try:

                # --------------------------------------------
                # Generate answer
                # --------------------------------------------

                answer = generate_answer(
                    user_query=user_query,
                    top_k=5,
                )

                # --------------------------------------------
                # Display answer
                # --------------------------------------------

                st.markdown(answer)

                # --------------------------------------------
                # Save assistant message
                # --------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

                # --------------------------------------------
                # Log request
                # --------------------------------------------

                request_id = log_request(
                    user_query=user_query,
                    response=answer,
                )

                # --------------------------------------------
                # Store request ID
                # --------------------------------------------

                st.session_state.current_request_id = request_id

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
# USER FEEDBACK
# ------------------------------------------------------------

if (
    st.session_state.current_request_id is not None
    and not st.session_state.feedback_given
):

    st.divider()

    st.write("### Was this recommendation helpful?")

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # POSITIVE FEEDBACK
    # --------------------------------------------------------

    with col1:

        if st.button(
            "👍 Helpful",
            use_container_width=True,
            key=f"positive_feedback_"
                f"{st.session_state.current_request_id}",
        ):

            try:

                save_feedback(
                    request_id=st.session_state.current_request_id,
                    feedback="positive",
                )

                st.session_state.feedback_given = True

                st.success("Thanks for your feedback! 👍")

            except Exception as e:

                st.error(
                    f"Unable to save feedback: {e}"
                )

    # --------------------------------------------------------
    # NEGATIVE FEEDBACK
    # --------------------------------------------------------

    with col2:

        if st.button(
            "👎 Not helpful",
            use_container_width=True,
            key=f"negative_feedback_"
                f"{st.session_state.current_request_id}",
        ):

            try:

                save_feedback(
                    request_id=st.session_state.current_request_id,
                    feedback="negative",
                )

                st.session_state.feedback_given = True

                st.success("Thanks for your feedback! 👎")

            except Exception as e:

                st.error(
                    f"Unable to save feedback: {e}"
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
        - User Feedback
        """
    )

    st.divider()

    st.subheader("Conversation")

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.session_state.current_request_id = None

        st.session_state.feedback_given = False

        conversation_history.clear()

        st.rerun()