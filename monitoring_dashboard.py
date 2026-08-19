import pandas as pd
import streamlit as st

import monitoring_analysis


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Shopping Assistant Monitoring",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("📊 AI Shopping Assistant Monitoring")

st.caption(
    "Monitoring dashboard for RAG, hybrid search, and LLM performance"
)


# ============================================================
# LOAD METRICS
# ============================================================

request_stats = monitoring_analysis.get_request_stats()
latency_stats = monitoring_analysis.get_latency_stats()
token_stats = monitoring_analysis.get_token_stats()
cost_stats = monitoring_analysis.get_cost_stats()
query_type_stats = monitoring_analysis.get_query_type_stats()
feedback_stats = monitoring_analysis.get_feedback_stats()

recent_requests = monitoring_analysis.get_recent_requests(20)
slowest_requests = monitoring_analysis.get_slowest_requests(10)
expensive_requests = monitoring_analysis.get_most_expensive_requests(10)



# ============================================================
# TOP-LEVEL METRICS
# ============================================================

st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Requests",
        request_stats["total_requests"],
    )

with col2:
    st.metric(
        "Error Rate",
        f"{request_stats['error_rate']:.2f}%",
    )

with col3:
    st.metric(
        "Average Total Latency",
        f"{latency_stats['avg_total_latency']:.2f}s",
    )

with col4:
    st.metric(
        "Total LLM Cost",
        f"${cost_stats['total_cost']:.6f}",
    )


# ============================================================
# USER FEEDBACK
# ============================================================

st.subheader("User Feedback")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Feedback",
        feedback_stats["total_feedback"],
    )

with col2:
    st.metric(
        "👍 Positive",
        feedback_stats["positive_feedback"],
    )

with col3:
    st.metric(
        "👎 Negative",
        feedback_stats["negative_feedback"],
    )

with col4:
    st.metric(
        "Positive Rate",
        f"{feedback_stats['positive_rate']:.2f}%",
    )


# ============================================================
# FEEDBACK CHART
# ============================================================

feedback_data = pd.DataFrame(
    {
        "Feedback": [
            "Positive",
            "Negative",
        ],
        "Count": [
            feedback_stats["positive_feedback"],
            feedback_stats["negative_feedback"],
        ],
    }
)

if feedback_stats["total_feedback"] > 0:

    st.bar_chart(
        feedback_data.set_index("Feedback")
    )

else:

    st.info("No user feedback available yet.")


# ============================================================
# SECONDARY METRICS
# ============================================================

st.subheader("LLM Usage")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Input Tokens",
        f"{int(token_stats['total_input_tokens']):,}",
    )

with col2:
    st.metric(
        "Total Output Tokens",
        f"{int(token_stats['total_output_tokens']):,}",
    )

with col3:
    st.metric(
        "Total Tokens",
        f"{int(token_stats['total_tokens']):,}",
    )

with col4:
    st.metric(
        "Average Cost / Request",
        f"${cost_stats['avg_cost']:.6f}",
    )


# ============================================================
# LATENCY SECTION
# ============================================================

st.subheader("Latency")

latency_data = pd.DataFrame(
    {
        "Latency Type": [
            "Search",
            "LLM",
            "Total",
        ],
        "Average (seconds)": [
            latency_stats["avg_search_latency"],
            latency_stats["avg_llm_latency"],
            latency_stats["avg_total_latency"],
        ],
    }
)

st.bar_chart(
    latency_data.set_index("Latency Type")
)


# ============================================================
# TOKEN USAGE
# ============================================================

st.subheader("Token Usage")

token_data = pd.DataFrame(
    {
        "Token Type": [
            "Input",
            "Output",
            "Total",
        ],
        "Tokens": [
            token_stats["total_input_tokens"],
            token_stats["total_output_tokens"],
            token_stats["total_tokens"],
        ],
    }
)

st.bar_chart(
    token_data.set_index("Token Type")
)


# ============================================================
# QUERY TYPES
# ============================================================

st.subheader("Requests by Query Type")

if query_type_stats:

    query_type_data = pd.DataFrame(query_type_stats)

    st.bar_chart(
        query_type_data.set_index("query_type")
    )

else:

    st.info("No query type data available yet.")


# ============================================================
# SLOWEST REQUESTS
# ============================================================

st.subheader("Slowest Requests")

if slowest_requests:

    slow_df = pd.DataFrame(slowest_requests)

    slow_df = slow_df[
        [
            "id",
            "timestamp",
            "user_query",
            "search_latency",
            "llm_latency",
            "total_latency",
        ]
    ]

    st.dataframe(
        slow_df,
        use_container_width=True,
    )

else:

    st.info("No request data available.")


# ============================================================
# MOST EXPENSIVE REQUESTS
# ============================================================

st.subheader("Most Expensive Requests")

if expensive_requests:

    expensive_df = pd.DataFrame(expensive_requests)

    expensive_df = expensive_df[
        [
            "id",
            "timestamp",
            "user_query",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "llm_cost",
        ]
    ]

    st.dataframe(
        expensive_df,
        use_container_width=True,
    )

else:

    st.info("No cost data available.")


# ============================================================
# RECENT REQUESTS
# ============================================================

st.subheader("Recent Requests")

if recent_requests:

    recent_df = pd.DataFrame(recent_requests)

    st.dataframe(
        recent_df,
        use_container_width=True,
    )

else:

    st.info("No monitoring data available.")