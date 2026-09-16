import os
import psycopg

source_url = os.environ["SOURCE_DATABASE_URL"]
target_url = os.environ["TARGET_DATABASE_URL"]

tables = {
    "users": [
        "user_id",
        "name",
        "password_hash",
        "password_salt",
        "wins",
        "losses",
        "rating",
        "rank",
        "created_at",
        "updated_at",
    ],
    "sessions": [
        "session_id",
        "user_id",
        "token_hash",
        "created_at",
        "expires_at",
    ],
    "matches": [
        "match_id",
        "winner_user_id",
        "loser_user_id",
        "winner_rating_before",
        "winner_rating_after",
        "loser_rating_before",
        "loser_rating_after",
        "created_at",
    ],
}

with psycopg.connect(source_url) as source_conn, psycopg.connect(target_url) as target_conn:
    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    # Neon側が空であることを確認
    for table in tables:
        target_cur.execute(
            f"SELECT COUNT(*) FROM {table}"
        )
        count = target_cur.fetchone()[0]

        if count != 0:
            raise RuntimeError(
                f"Neonの {table} が空ではありません: {count}件"
            )

    # Render → Neon
    for table, columns in tables.items():
        column_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        source_cur.execute(
            f"SELECT {column_list} FROM {table}"
        )
        rows = source_cur.fetchall()

        if rows:
            target_cur.executemany(
                f"""
                INSERT INTO {table} ({column_list})
                VALUES ({placeholders})
                """,
                rows,
            )

        print(f"{table}: {len(rows)}件コピー")

    target_conn.commit()

print("Render → Neon migration completed.")
