import sqlite3
import monitoring


conn = sqlite3.connect(monitoring.DB_PATH)

rows = conn.execute(
    """
    SELECT feedback, COUNT(*)
    FROM requests
    WHERE feedback IS NOT NULL
    GROUP BY feedback
    """
).fetchall()

print("Feedback statistics:")
print(rows)

conn.close()