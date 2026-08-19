import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "monitoring.db"


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_monitoring_db():
    """
    Create the monitoring database and requests table.

    Also performs a lightweight migration by adding any
    monitoring columns that are missing from an existing DB.
    """

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_query TEXT NOT NULL,
            search_query TEXT,
            query_type TEXT,
            filters TEXT,
            retrieved_product_ids TEXT,
            num_results INTEGER,
            search_latency REAL,
            llm_latency REAL,
            total_latency REAL,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            llm_cost REAL,
            response TEXT,
            error TEXT
        )
        """
    )

    # --------------------------------------------------------
    # Migration for existing monitoring.db
    # --------------------------------------------------------

    existing_columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(requests)"
        ).fetchall()
    }

    new_columns = {
        "query_type": "TEXT",
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "total_tokens": "INTEGER",
        "llm_cost": "REAL",
    }

    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:

            conn.execute(
                f"""
                ALTER TABLE requests
                ADD COLUMN {column_name} {column_type}
                """
            )

    conn.commit()
    conn.close()


# ============================================================
# LOG REQUEST
# ============================================================

def log_request(
    user_query,
    search_query=None,
    query_type=None,
    filters=None,
    retrieved_product_ids=None,
    num_results=0,
    search_latency=None,
    llm_latency=None,
    total_latency=None,
    model=None,
    input_tokens=None,
    output_tokens=None,
    total_tokens=None,
    llm_cost=None,
    response=None,
    error=None,
):
    """
    Store one assistant request in the monitoring database.
    """

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO requests (
            timestamp,
            user_query,
            search_query,
            query_type,
            filters,
            retrieved_product_ids,
            num_results,
            search_latency,
            llm_latency,
            total_latency,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
            llm_cost,
            response,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            user_query,
            search_query,
            query_type,
            json.dumps(filters) if filters is not None else None,
            json.dumps(retrieved_product_ids)
            if retrieved_product_ids is not None
            else None,
            num_results,
            search_latency,
            llm_latency,
            total_latency,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
            llm_cost,
            response,
            error,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# GET RECENT REQUESTS
# ============================================================

def get_recent_requests(limit=20):
    """
    Return the most recent monitored requests.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT *
        FROM requests
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    init_monitoring_db()

    print(
        f"Monitoring database initialized: {DB_PATH}"
    )