from pathlib import Path

import os
import hashlib
import hmac
import secrets
import sqlite3
import uuid

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

from datetime import datetime, timedelta, timezone


# =============================================
# DATABASE
# =============================================

BASE_DIR = Path(
    __file__
).resolve().parent

DB_PATH = (
    BASE_DIR
    /
    "veil53.db"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
).strip()

DATABASE_BACKEND = (
    "postgresql"
    if DATABASE_URL
    else "sqlite"
)

if psycopg is not None:
    DB_INTEGRITY_ERRORS = (
        sqlite3.IntegrityError,
        psycopg.IntegrityError
    )
else:
    DB_INTEGRITY_ERRORS = (
        sqlite3.IntegrityError,
    )


# =============================================
# SETTINGS
# =============================================

PLAYER_NAME_MAX_LENGTH = 12

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

INITIAL_RATING = 1000

SESSION_EXPIRE_DAYS = 30

ELO_K_FACTOR = 32


# =============================================
# CONNECTION
# =============================================

class DatabaseConnection:

    def __init__(
        self,
        connection,
        backend
    ):

        self._connection = connection
        self.backend = backend


    def _prepare_sql(
        self,
        sql
    ):

        if self.backend == "postgresql":

            return sql.replace(
                "?",
                "%s"
            )

        return sql


    def execute(
        self,
        sql,
        params=()
    ):

        return self._connection.execute(
            self._prepare_sql(
                sql
            ),
            params
        )


    def commit(self):

        self._connection.commit()


    def rollback(self):

        self._connection.rollback()


    def close(self):

        self._connection.close()


    def __enter__(self):

        return self


    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        try:

            if exc_type is None:

                self.commit()

            else:

                self.rollback()

        finally:

            self.close()

        return False


def get_connection():

    if DATABASE_URL:

        if psycopg is None:

            raise RuntimeError(
                "PostgreSQLを使用するには "
                "psycopg[binary] が必要です"
            )

        conn = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )

        return DatabaseConnection(
            conn,
            "postgresql"
        )


    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = (
        sqlite3.Row
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return DatabaseConnection(
        conn,
        "sqlite"
    )


def begin_ranked_transaction(
    conn,
    winner_user_id,
    loser_user_id
):

    if conn.backend == "sqlite":

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        return


    # PostgreSQLでは対象ユーザー行を一定順序でロックする。
    # 同時に複数のランク戦結果が記録されても、
    # レーティング更新の競合やデッドロックが起きにくくなる。
    first_user_id, second_user_id = sorted(
        (
            winner_user_id,
            loser_user_id
        )
    )

    conn.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id IN (?, ?)
        ORDER BY user_id
        FOR UPDATE
        """,
        (
            first_user_id,
            second_user_id
        )
    ).fetchall()


# =============================================
# TIME
# =============================================

def utc_now():

    return datetime.now(
        timezone.utc
    )


def utc_now_iso():

    return utc_now().isoformat()


# =============================================
# INIT
# =============================================

def init_db():

    with get_connection() as conn:

        # =====================================
        # USERS
        # =====================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,

                name TEXT
                    NOT NULL
                    UNIQUE,

                password_hash TEXT
                    NOT NULL,

                password_salt TEXT
                    NOT NULL,

                wins INTEGER
                    NOT NULL
                    DEFAULT 0
                    CHECK (wins >= 0),

                losses INTEGER
                    NOT NULL
                    DEFAULT 0
                    CHECK (losses >= 0),

                rating INTEGER
                    NOT NULL
                    DEFAULT 1000
                    CHECK (rating >= 0),

                rank TEXT
                    NOT NULL
                    DEFAULT 'BRONZE',

                created_at TEXT
                    NOT NULL,

                updated_at TEXT
                    NOT NULL
            )
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_rating
            ON users(rating DESC)
            """
        )


        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_name_lower_unique
            ON users(LOWER(name))
            """
        )


        # =====================================
        # SESSIONS
        # =====================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,

                user_id TEXT
                    NOT NULL,

                token_hash TEXT
                    NOT NULL
                    UNIQUE,

                created_at TEXT
                    NOT NULL,

                expires_at TEXT
                    NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_sessions_user_id
            ON sessions(user_id)
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_sessions_token_hash
            ON sessions(token_hash)
            """
        )


        # =====================================
        # RANKED MATCHES
        # =====================================

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,

                winner_user_id TEXT
                    NOT NULL,

                loser_user_id TEXT
                    NOT NULL,

                winner_rating_before INTEGER
                    NOT NULL,

                winner_rating_after INTEGER
                    NOT NULL,

                loser_rating_before INTEGER
                    NOT NULL,

                loser_rating_after INTEGER
                    NOT NULL,

                created_at TEXT
                    NOT NULL,

                FOREIGN KEY (winner_user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (loser_user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                CHECK (
                    winner_user_id
                    !=
                    loser_user_id
                )
            )
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_matches_created_at
            ON matches(created_at)
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_matches_winner_user_id
            ON matches(winner_user_id)
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_matches_loser_user_id
            ON matches(loser_user_id)
            """
        )


# =============================================
# NAME
# =============================================

def normalize_player_name(
    name
):

    if name is None:

        return ""

    return str(
        name
    ).strip()


def validate_player_name(
    name
):

    name = normalize_player_name(
        name
    )


    if not name:

        raise ValueError(
            "プレイヤー名を入力してください"
        )


    if (
        len(name)
        >
        PLAYER_NAME_MAX_LENGTH
    ):

        raise ValueError(
            "プレイヤー名は"
            f"{PLAYER_NAME_MAX_LENGTH}"
            "文字以内で入力してください"
        )


    return name


# =============================================
# PASSWORD
# =============================================

def validate_password(
    password
):

    if not isinstance(
        password,
        str
    ):

        raise ValueError(
            "パスワードが正しくありません"
        )


    if (
        len(password)
        <
        PASSWORD_MIN_LENGTH
    ):

        raise ValueError(
            "パスワードは"
            f"{PASSWORD_MIN_LENGTH}"
            "文字以上で入力してください"
        )


    if (
        len(password)
        >
        PASSWORD_MAX_LENGTH
    ):

        raise ValueError(
            "パスワードは"
            f"{PASSWORD_MAX_LENGTH}"
            "文字以内で入力してください"
        )


    return password


def hash_password(
    password,
    salt=None
):

    password = validate_password(
        password
    )


    if salt is None:

        salt_bytes = (
            secrets.token_bytes(
                16
            )
        )

    else:

        salt_bytes = (
            bytes.fromhex(
                salt
            )
        )


    password_hash = hashlib.scrypt(
        password.encode(
            "utf-8"
        ),
        salt=salt_bytes,
        n=2 ** 14,
        r=8,
        p=1,
        dklen=64
    )


    return (
        password_hash.hex(),
        salt_bytes.hex()
    )


def verify_password(
    password,
    stored_hash,
    stored_salt
):

    try:

        calculated_hash, _ = (
            hash_password(
                password,
                stored_salt
            )
        )

    except (
        ValueError,
        TypeError
    ):

        return False


    return hmac.compare_digest(
        calculated_hash,
        stored_hash
    )


# =============================================
# RANK
# =============================================

def calculate_rank(
    rating
):

    if rating < 900:

        return "IRON"


    elif rating < 1100:

        return "BRONZE"


    elif rating < 1300:

        return "SILVER"


    elif rating < 1500:

        return "GOLD"


    elif rating < 1700:

        return "PLATINUM"


    else:

        return "DIAMOND"


# =============================================
# USER DICT
# =============================================

def user_to_dict(
    row
):

    if row is None:

        return None


    wins = int(
        row["wins"]
    )

    losses = int(
        row["losses"]
    )

    matches = (
        wins
        +
        losses
    )


    if matches > 0:

        win_rate = (
            wins
            /
            matches
            *
            100
        )

    else:

        win_rate = 0.0


    return {
        "user_id":
            row["user_id"],

        "name":
            row["name"],

        "wins":
            wins,

        "losses":
            losses,

        "matches":
            matches,

        "win_rate":
            round(
                win_rate,
                1
            ),

        "rating":
            int(
                row["rating"]
            ),

        "rank":
            row["rank"],

        "created_at":
            row["created_at"],

        "updated_at":
            row["updated_at"]
    }


# =============================================
# CREATE USER
# =============================================

def create_user(
    name,
    password
):

    name = validate_player_name(
        name
    )

    password = validate_password(
        password
    )


    password_hash, password_salt = (
        hash_password(
            password
        )
    )


    user_id = (
        uuid.uuid4().hex
    )


    now = utc_now_iso()


    try:

        with get_connection() as conn:

            conn.execute(
                """
                INSERT INTO users (
                    user_id,
                    name,
                    password_hash,
                    password_salt,
                    wins,
                    losses,
                    rating,
                    rank,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    password_hash,
                    password_salt,
                    INITIAL_RATING,
                    calculate_rank(
                        INITIAL_RATING
                    ),
                    now,
                    now
                )
            )


    except DB_INTEGRITY_ERRORS:

        raise ValueError(
            "そのプレイヤー名はすでに使われています"
        )


    return get_user_by_id(
        user_id
    )


# =============================================
# GET USER
# =============================================

def get_user_by_id(
    user_id
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                user_id,
                name,
                wins,
                losses,
                rating,
                rank,
                created_at,
                updated_at
            FROM users
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()


    return user_to_dict(
        row
    )


def get_user_by_name(
    name
):

    name = normalize_player_name(
        name
    )


    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                user_id,
                name,
                wins,
                losses,
                rating,
                rank,
                created_at,
                updated_at
            FROM users
            WHERE LOWER(name) = LOWER(?)
            """,
            (
                name,
            )
        ).fetchone()


    return user_to_dict(
        row
    )


# =============================================
# AUTHENTICATE
# =============================================

def authenticate_user(
    name,
    password
):

    name = normalize_player_name(
        name
    )


    if not name:

        return None


    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(name) = LOWER(?)
            """,
            (
                name,
            )
        ).fetchone()


    if row is None:

        return None


    if not verify_password(
        password,
        row["password_hash"],
        row["password_salt"]
    ):

        return None


    return user_to_dict(
        row
    )


# =============================================
# SESSION TOKEN
# =============================================

def hash_session_token(
    session_token
):

    return hashlib.sha256(
        session_token.encode(
            "utf-8"
        )
    ).hexdigest()


def create_session(
    user_id
):

    session_id = (
        uuid.uuid4().hex
    )


    session_token = (
        secrets.token_urlsafe(
            48
        )
    )


    token_hash = (
        hash_session_token(
            session_token
        )
    )


    created_at = utc_now()

    expires_at = (
        created_at
        +
        timedelta(
            days=SESSION_EXPIRE_DAYS
        )
    )


    with get_connection() as conn:

        user = conn.execute(
            """
            SELECT user_id
            FROM users
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()


        if user is None:

            raise ValueError(
                "ユーザーが見つかりません"
            )


        conn.execute(
            """
            INSERT INTO sessions (
                session_id,
                user_id,
                token_hash,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                token_hash,
                created_at.isoformat(),
                expires_at.isoformat()
            )
        )


    return session_token


# =============================================
# GET USER BY SESSION
# =============================================

def get_user_by_session_token(
    session_token
):

    if not session_token:

        return None


    token_hash = (
        hash_session_token(
            session_token
        )
    )


    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                users.user_id,
                users.name,
                users.wins,
                users.losses,
                users.rating,
                users.rank,
                users.created_at,
                users.updated_at,

                sessions.session_id,
                sessions.expires_at

            FROM sessions

            INNER JOIN users
                ON users.user_id
                =
                sessions.user_id

            WHERE sessions.token_hash = ?
            """,
            (
                token_hash,
            )
        ).fetchone()


        if row is None:

            return None


        try:

            expires_at = (
                datetime.fromisoformat(
                    row["expires_at"]
                )
            )

        except ValueError:

            conn.execute(
                """
                DELETE FROM sessions
                WHERE session_id = ?
                """,
                (
                    row["session_id"],
                )
            )

            return None


        if (
            expires_at.tzinfo
            is None
        ):

            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )


        if (
            expires_at
            <=
            utc_now()
        ):

            conn.execute(
                """
                DELETE FROM sessions
                WHERE session_id = ?
                """,
                (
                    row["session_id"],
                )
            )

            return None


        return user_to_dict(
            row
        )


# =============================================
# DELETE SESSION
# =============================================

def delete_session(
    session_token
):

    if not session_token:

        return


    token_hash = (
        hash_session_token(
            session_token
        )
    )


    with get_connection() as conn:

        conn.execute(
            """
            DELETE FROM sessions
            WHERE token_hash = ?
            """,
            (
                token_hash,
            )
        )


def delete_all_user_sessions(
    user_id
):

    with get_connection() as conn:

        conn.execute(
            """
            DELETE FROM sessions
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )


def delete_expired_sessions():

    now = utc_now_iso()


    with get_connection() as conn:

        conn.execute(
            """
            DELETE FROM sessions
            WHERE expires_at <= ?
            """,
            (
                now,
            )
        )


# =============================================
# UPDATE USER NAME
# =============================================

def update_user_name(
    user_id,
    new_name
):

    new_name = validate_player_name(
        new_name
    )


    now = utc_now_iso()


    try:

        with get_connection() as conn:

            cursor = conn.execute(
                """
                UPDATE users
                SET
                    name = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    new_name,
                    now,
                    user_id
                )
            )


            if (
                cursor.rowcount
                ==
                0
            ):

                raise ValueError(
                    "ユーザーが見つかりません"
                )


    except DB_INTEGRITY_ERRORS:

        raise ValueError(
            "そのプレイヤー名はすでに使われています"
        )


    return get_user_by_id(
        user_id
    )


# =============================================
# UPDATE PASSWORD
# =============================================

def update_password(
    user_id,
    current_password,
    new_password
):

    new_password = validate_password(
        new_password
    )


    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()


        if row is None:

            raise ValueError(
                "ユーザーが見つかりません"
            )


        if not verify_password(
            current_password,
            row["password_hash"],
            row["password_salt"]
        ):

            raise ValueError(
                "現在のパスワードが正しくありません"
            )


        new_hash, new_salt = (
            hash_password(
                new_password
            )
        )


        now = utc_now_iso()


        conn.execute(
            """
            UPDATE users
            SET
                password_hash = ?,
                password_salt = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                new_hash,
                new_salt,
                now,
                user_id
            )
        )


        conn.execute(
            """
            DELETE FROM sessions
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )


    return get_user_by_id(
        user_id
    )


# =============================================
# ELO
# =============================================

def calculate_new_rating(
    player_rating,
    opponent_rating,
    score,
    k_factor=ELO_K_FACTOR
):

    expected_score = (
        1
        /
        (
            1
            +
            10
            **
            (
                (
                    opponent_rating
                    -
                    player_rating
                )
                /
                400
            )
        )
    )


    new_rating = round(
        player_rating
        +
        k_factor
        *
        (
            score
            -
            expected_score
        )
    )


    return max(
        0,
        new_rating
    )


# =============================================
# RANKED MATCH
# =============================================

def record_ranked_match(
    match_id,
    winner_user_id,
    loser_user_id
):

    if not match_id:

        raise ValueError(
            "match_idが必要です"
        )


    if not winner_user_id:

        raise ValueError(
            "勝者のuser_idが必要です"
        )


    if not loser_user_id:

        raise ValueError(
            "敗者のuser_idが必要です"
        )


    if (
        winner_user_id
        ==
        loser_user_id
    ):

        raise ValueError(
            "同じユーザー同士の対戦結果は記録できません"
        )


    conn = get_connection()


    try:

        # 他のレート更新と同時に走らないようにする
        begin_ranked_transaction(
            conn,
            winner_user_id,
            loser_user_id
        )


        # =====================================
        # DUPLICATE CHECK
        # =====================================

        existing_match = (
            conn.execute(
                """
                SELECT *
                FROM matches
                WHERE match_id = ?
                """,
                (
                    match_id,
                )
            ).fetchone()
        )


        if (
            existing_match
            is not None
        ):

            conn.rollback()


            return {
                "already_recorded":
                    True,

                "match_id":
                    match_id,

                "winner_user":
                    get_user_by_id(
                        existing_match[
                            "winner_user_id"
                        ]
                    ),

                "loser_user":
                    get_user_by_id(
                        existing_match[
                            "loser_user_id"
                        ]
                    )
            }


        # =====================================
        # USERS
        # =====================================

        winner = (
            conn.execute(
                """
                SELECT *
                FROM users
                WHERE user_id = ?
                """,
                (
                    winner_user_id,
                )
            ).fetchone()
        )


        loser = (
            conn.execute(
                """
                SELECT *
                FROM users
                WHERE user_id = ?
                """,
                (
                    loser_user_id,
                )
            ).fetchone()
        )


        if winner is None:

            raise ValueError(
                "勝者のユーザーが見つかりません"
            )


        if loser is None:

            raise ValueError(
                "敗者のユーザーが見つかりません"
            )


        # =====================================
        # BEFORE RATING
        # =====================================

        winner_rating_before = int(
            winner["rating"]
        )

        loser_rating_before = int(
            loser["rating"]
        )


        # =====================================
        # AFTER RATING
        # =====================================

        winner_rating_after = (
            calculate_new_rating(
                winner_rating_before,
                loser_rating_before,
                1
            )
        )


        loser_rating_after = (
            calculate_new_rating(
                loser_rating_before,
                winner_rating_before,
                0
            )
        )


        winner_rank_after = (
            calculate_rank(
                winner_rating_after
            )
        )


        loser_rank_after = (
            calculate_rank(
                loser_rating_after
            )
        )


        now = utc_now_iso()


        # =====================================
        # WINNER UPDATE
        # =====================================

        conn.execute(
            """
            UPDATE users
            SET
                wins = wins + 1,
                rating = ?,
                rank = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                winner_rating_after,
                winner_rank_after,
                now,
                winner_user_id
            )
        )


        # =====================================
        # LOSER UPDATE
        # =====================================

        conn.execute(
            """
            UPDATE users
            SET
                losses = losses + 1,
                rating = ?,
                rank = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                loser_rating_after,
                loser_rank_after,
                now,
                loser_user_id
            )
        )


        # =====================================
        # MATCH HISTORY
        # =====================================

        conn.execute(
            """
            INSERT INTO matches (
                match_id,
                winner_user_id,
                loser_user_id,
                winner_rating_before,
                winner_rating_after,
                loser_rating_before,
                loser_rating_after,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                match_id,
                winner_user_id,
                loser_user_id,
                winner_rating_before,
                winner_rating_after,
                loser_rating_before,
                loser_rating_after,
                now
            )
        )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


    return {
        "already_recorded":
            False,

        "match_id":
            match_id,

        "winner_rating_before":
            winner_rating_before,

        "winner_rating_after":
            winner_rating_after,

        "winner_rating_change":
            (
                winner_rating_after
                -
                winner_rating_before
            ),

        "loser_rating_before":
            loser_rating_before,

        "loser_rating_after":
            loser_rating_after,

        "loser_rating_change":
            (
                loser_rating_after
                -
                loser_rating_before
            ),

        "winner_user":
            get_user_by_id(
                winner_user_id
            ),

        "loser_user":
            get_user_by_id(
                loser_user_id
            )
    }


# =============================================
# OLD SINGLE USER MATCH RESULT
# =============================================
# 既存コードとの互換用。
# QUICK MATCHでは使わず、
# record_ranked_match() を使う。

def record_match_result(
    user_id,
    opponent_rating,
    won
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()


        if row is None:

            raise ValueError(
                "ユーザーが見つかりません"
            )


        current_rating = int(
            row["rating"]
        )


        score = (
            1
            if won
            else 0
        )


        new_rating = (
            calculate_new_rating(
                current_rating,
                opponent_rating,
                score
            )
        )


        new_rank = (
            calculate_rank(
                new_rating
            )
        )


        now = utc_now_iso()


        if won:

            conn.execute(
                """
                UPDATE users
                SET
                    wins = wins + 1,
                    rating = ?,
                    rank = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    new_rating,
                    new_rank,
                    now,
                    user_id
                )
            )

        else:

            conn.execute(
                """
                UPDATE users
                SET
                    losses = losses + 1,
                    rating = ?,
                    rank = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    new_rating,
                    new_rank,
                    now,
                    user_id
                )
            )


    return get_user_by_id(
        user_id
    )


# =============================================
# RANKING
# =============================================

def get_ranking(
    limit=100
):

    limit = max(
        1,
        min(
            int(limit),
            100
        )
    )


    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                user_id,
                name,
                wins,
                losses,
                rating,
                rank,
                created_at,
                updated_at
            FROM users

            ORDER BY
                rating DESC,
                wins DESC,
                losses ASC,
                created_at ASC

            LIMIT ?
            """,
            (
                limit,
            )
        ).fetchall()


    return [
        user_to_dict(
            row
        )
        for row in rows
    ]


# =============================================
# MATCH HISTORY
# =============================================

def get_match_by_id(
    match_id
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM matches
            WHERE match_id = ?
            """,
            (
                match_id,
            )
        ).fetchone()


    if row is None:

        return None


    return dict(
        row
    )


# =============================================
# MAIN
# =============================================

if __name__ == "__main__":

    init_db()

    print(
        "Database initialized:"
    )

    if DATABASE_BACKEND == "postgresql":

        print(
            "PostgreSQL (DATABASE_URL)"
        )

    else:

        print(
            DB_PATH
        )