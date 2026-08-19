import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "monitoring.db"


def get_connection():
    """Create a connection to the monitoring database."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# BASIC REQUEST METRICS
# ============================================================

def get_request_stats():
    """
    Return basic request statistics.
    """

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_requests,

            SUM(
                CASE
                    WHEN error IS NULL OR error = ''
                    THEN 1
                    ELSE 0
                END
            ) AS successful_requests,

            SUM(
                CASE
                    WHEN error IS NOT NULL AND error != ''
                    THEN 1
                    ELSE 0
                END
            ) AS failed_requests

        FROM requests
        """
    ).fetchone()

    conn.close()

    total_requests = row["total_requests"] or 0
    successful_requests = row["successful_requests"] or 0
    failed_requests = row["failed_requests"] or 0

    if total_requests > 0:
        error_rate = (
            failed_requests / total_requests
        ) * 100
    else:
        error_rate = 0.0

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "error_rate": error_rate,
    }


# ============================================================
# LATENCY METRICS
# ============================================================

def get_latency_stats():
    """
    Return average latency metrics.
    """

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            AVG(search_latency) AS avg_search_latency,
            AVG(llm_latency) AS avg_llm_latency,
            AVG(total_latency) AS avg_total_latency,

            MAX(search_latency) AS max_search_latency,
            MAX(llm_latency) AS max_llm_latency,
            MAX(total_latency) AS max_total_latency

        FROM requests
        WHERE error IS NULL
           OR error = ''
        """
    ).fetchone()

    conn.close()

    return {
        "avg_search_latency": row["avg_search_latency"] or 0,
        "avg_llm_latency": row["avg_llm_latency"] or 0,
        "avg_total_latency": row["avg_total_latency"] or 0,

        "max_search_latency": row["max_search_latency"] or 0,
        "max_llm_latency": row["max_llm_latency"] or 0,
        "max_total_latency": row["max_total_latency"] or 0,
    }


# ============================================================
# TOKEN METRICS
# ============================================================

def get_token_stats():
    """
    Return token usage statistics.
    """

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            SUM(input_tokens) AS total_input_tokens,
            SUM(output_tokens) AS total_output_tokens,
            SUM(total_tokens) AS total_tokens,

            AVG(input_tokens) AS avg_input_tokens,
            AVG(output_tokens) AS avg_output_tokens,
            AVG(total_tokens) AS avg_total_tokens

        FROM requests
        """
    ).fetchone()

    conn.close()

    return {
        "total_input_tokens": row["total_input_tokens"] or 0,
        "total_output_tokens": row["total_output_tokens"] or 0,
        "total_tokens": row["total_tokens"] or 0,

        "avg_input_tokens": row["avg_input_tokens"] or 0,
        "avg_output_tokens": row["avg_output_tokens"] or 0,
        "avg_total_tokens": row["avg_total_tokens"] or 0,
    }


# ============================================================
# COST METRICS
# ============================================================

def get_cost_stats():
    """
    Return LLM cost statistics.
    """

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            SUM(llm_cost) AS total_cost,
            AVG(llm_cost) AS avg_cost,
            MAX(llm_cost) AS max_cost

        FROM requests
        """
    ).fetchone()

    conn.close()

    return {
        "total_cost": row["total_cost"] or 0,
        "avg_cost": row["avg_cost"] or 0,
        "max_cost": row["max_cost"] or 0,
    }


# ============================================================
# QUERY TYPE METRICS
# ============================================================

def get_query_type_stats():
    """
    Return request counts grouped by query type.
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            COALESCE(query_type, 'unknown') AS query_type,
            COUNT(*) AS count

        FROM requests

        GROUP BY query_type

        ORDER BY count DESC
        """
    ).fetchall()

    conn.close()

    return [
        {
            "query_type": row["query_type"],
            "count": row["count"],
        }
        for row in rows
    ]


# ============================================================
# USER FEEDBACK METRICS
# ============================================================

def get_feedback_stats():
    """
    Return user feedback statistics.
    """

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            COUNT(feedback) AS total_feedback,

            SUM(
                CASE
                    WHEN feedback = 'positive'
                    THEN 1
                    ELSE 0
                END
            ) AS positive_feedback,

            SUM(
                CASE
                    WHEN feedback = 'negative'
                    THEN 1
                    ELSE 0
                END
            ) AS negative_feedback

        FROM requests
        """
    ).fetchone()

    conn.close()

    total_feedback = row["total_feedback"] or 0
    positive_feedback = row["positive_feedback"] or 0
    negative_feedback = row["negative_feedback"] or 0

    if total_feedback > 0:
        positive_rate = (
            positive_feedback / total_feedback
        ) * 100
    else:
        positive_rate = 0.0

    return {
        "total_feedback": total_feedback,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "positive_rate": positive_rate,
    }

# ============================================================
# RECENT REQUESTS
# ============================================================

def get_recent_requests(limit=20):
    """
    Return recent monitoring records.
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            id,
            timestamp,
            user_query,
            query_type,
            num_results,
            search_latency,
            llm_latency,
            total_latency,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
            llm_cost,
            error

        FROM requests

        ORDER BY id DESC

        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# SLOWEST REQUESTS
# ============================================================

def get_slowest_requests(limit=10):
    """
    Return requests with the highest total latency.
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            id,
            timestamp,
            user_query,
            total_latency,
            search_latency,
            llm_latency,
            llm_cost

        FROM requests

        ORDER BY total_latency DESC

        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# MOST EXPENSIVE REQUESTS
# ============================================================

def get_most_expensive_requests(limit=10):
    """
    Return requests with the highest LLM cost.
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            id,
            timestamp,
            user_query,
            input_tokens,
            output_tokens,
            total_tokens,
            llm_cost

        FROM requests

        ORDER BY llm_cost DESC

        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("MONITORING ANALYSIS")
    print("=" * 60)

    print("\nREQUEST STATISTICS")
    print("-" * 60)

    print(get_request_stats())

    print("\nLATENCY STATISTICS")
    print("-" * 60)

    print(get_latency_stats())

    print("\nTOKEN STATISTICS")
    print("-" * 60)

    print(get_token_stats())

    print("\nCOST STATISTICS")
    print("-" * 60)

    print(get_cost_stats())

    print("\nQUERY TYPES")
    print("-" * 60)

    print(get_query_type_stats())

    print("\nRECENT REQUESTS")
    print("-" * 60)

    for request in get_recent_requests(5):
        print(request)