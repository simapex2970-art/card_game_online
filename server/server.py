import asyncio
import random
import secrets
import time
from itertools import combinations
from pathlib import Path


from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from game import Game
from card import Card

from database import (
    init_db,
    create_user,
    authenticate_user,
    create_session,
    get_user_by_name,
    get_user_by_session_token,
    delete_session,
    record_ranked_match
)


# =============================================
# FastAPI
# =============================================

app = FastAPI()

init_db()


# =============================================
# CACHE CONTROL
# =============================================

@app.middleware("http")
async def disable_web_file_cache(
    request,
    call_next
):
    response = await call_next(request)

    no_cache_paths = {
        "/",
        "/static/app.js",
        "/static/style.css",
    }

    if request.url.path in no_cache_paths:
        response.headers["Cache-Control"] = (
            "no-store, no-cache, "
            "must-revalidate, max-age=0"
        )

        response.headers["Pragma"] = (
            "no-cache"
        )

        response.headers["Expires"] = (
            "0"
        )

    return response


# =============================================
# USER API
# =============================================

class UserRegisterRequest(BaseModel):
    name: str
    password: str


class UserLoginRequest(BaseModel):
    name: str
    password: str


def get_bearer_token(
    authorization: str | None
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="ログインが必要です"
        )

    parts = authorization.split(
        " ",
        1
    )

    if (
        len(parts) != 2
        or
        parts[0].lower() != "bearer"
        or
        not parts[1].strip()
    ):
        raise HTTPException(
            status_code=401,
            detail="認証情報が正しくありません"
        )

    return parts[1].strip()


@app.post("/users/register")
async def register_user_api(
    request: UserRegisterRequest
):
    try:
        user = create_user(
            request.name,
            request.password
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    session_token = create_session(
        user["user_id"]
    )

    return {
        "user": user,
        "session_token": session_token
    }


@app.post("/users/login")
async def login_user_api(
    request: UserLoginRequest
):

    # まずアカウント自体が存在するか確認
    existing_user = get_user_by_name(
        request.name
    )

    if existing_user is None:

        raise HTTPException(
            status_code=401,
            detail="そのアカウントは存在しません。"
        )


    # アカウントが存在する場合は
    # パスワードを確認
    user = authenticate_user(
        request.name,
        request.password
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="パスワードが正しくありません。"
        )


    session_token = create_session(
        user["user_id"]
    )


    return {
        "user": user,
        "session_token": session_token
    }


@app.get("/users/me")
async def get_current_user_api(
    authorization: str | None = Header(
        default=None
    )
):
    session_token = get_bearer_token(
        authorization
    )

    user = get_user_by_session_token(
        session_token
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "セッションの有効期限が"
                "切れているか、"
                "認証情報が正しくありません"
            )
        )

    return user


@app.post("/users/logout")
async def logout_user_api(
    authorization: str | None = Header(
        default=None
    )
):
    session_token = get_bearer_token(
        authorization
    )

    delete_session(
        session_token
    )

    return {
        "message":
            "ログアウトしました"
    }


# =============================================
# Webファイル
# =============================================

BASE_DIR = Path(__file__).resolve().parent

WEB_DIR = (
    BASE_DIR
    / "web"
)


app.mount(
    "/static",
    StaticFiles(
        directory=WEB_DIR
    ),
    name="static"
)


@app.get("/")
async def web_index():

    return FileResponse(
        WEB_DIR
        / "index.html"
    )


@app.get("/robots.txt")
async def robots_txt():

    return FileResponse(
        WEB_DIR
        / "robots.txt"
    )


@app.get("/sitemap.xml")
async def sitemap_xml():

    return FileResponse(
        WEB_DIR
        / "sitemap.xml"
    )


# =============================================
# 定数
# =============================================

ROOM_ID_CHARACTERS = (
    "ABCDEFGHJKLMNPQRSTUVWXYZ"
    "23456789"
)

ROOM_ID_LENGTH = 4

PLAYER_NAME_MAX_LENGTH = 12

RECONNECT_GRACE_SECONDS = 30


VALID_RANKS = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K"
]


VALID_SUITS = [
    "スペード",
    "ハート",
    "ダイヤ",
    "クラブ"
]


# =============================================
# ルーム
# =============================================

rooms = {}


# =============================================
# QUICK MATCH
# =============================================

waiting_room_id = None

matchmaking_lock = (
    asyncio.Lock()
)


# =============================================
# PLAYER NAME
# =============================================

def normalize_player_name(
    name
):

    if name is None:

        return ""

    return (
        str(
            name
        )
        .strip()
    )


def is_valid_player_name(
    name
):

    if not name:

        return False

    if (
        len(
            name
        )
        >
        PLAYER_NAME_MAX_LENGTH
    ):

        return False

    return True


# =============================================
# CPU NAME
# =============================================

def get_cpu_name(
    room
):

    return (
        f"CPU Lv."
        f"{room['cpu_level']}"
    )


# =============================================
# ROOM ID
# =============================================

def generate_room_id():

    while True:

        room_id = "".join(
            secrets.choice(
                ROOM_ID_CHARACTERS
            )
            for _ in range(
                ROOM_ID_LENGTH
            )
        )

        if (
            room_id
            not in rooms
        ):

            return room_id


def is_valid_room_id(
    room_id
):

    if (
        len(
            room_id
        )
        !=
        ROOM_ID_LENGTH
    ):

        return False


    return all(
        character
        in ROOM_ID_CHARACTERS

        for character
        in room_id
    )


# =============================================
# ROOM DATA
# =============================================

def create_room(
    mode="pvp",
    cpu_level=None,
    ranked=False
):

    return {

        "players":
            [],

        "player_names":
            [],

        "player_user_ids":
            [],

        "disconnected_players":
            {},

        "reconnect_tasks":
            {},

        "game":
            None,

        "current_turn":
            1,

        "current_phase":
            "question",

        "rematch_requests":
            set(),

        "mode":
            mode,

        "ranked":
            ranked,

        "current_match_id":
            None,

        "game_started_at":
            None,

        "cpu_level":
            cpu_level,

        "cpu_candidate_hands":
            [],

        "cpu_wrong_guesses":
            set(),

        "cpu_used_questions":
            set()
    }

# =============================================
# PLAYER NUMBER BY USER ID
# =============================================

def get_player_number_by_user_id(
    room,
    user_id
):

    try:

        index = (
            room[
                "player_user_ids"
            ]
            .index(
                user_id
            )
        )

    except ValueError:

        return None


    return index + 1


# =============================================
# RECONNECT TASK CANCEL
# =============================================

def cancel_reconnect_task(
    room,
    player_number
):

    task = (
        room[
            "reconnect_tasks"
        ].pop(
            player_number,
            None
        )
    )


    if (
        task is not None
        and
        not task.done()
    ):

        task.cancel()


# =============================================
# RECONNECT TIMEOUT
# =============================================

async def wait_for_reconnect_timeout(
    room_id,
    room,
    player_number,
    user_id
):

    try:

        await asyncio.sleep(
            RECONNECT_GRACE_SECONDS
        )

    except asyncio.CancelledError:

        return


    # すでにルームが削除・置換されていたら終了
    if (
        rooms.get(
            room_id
        )
        is not room
    ):

        return


    disconnected_player = (
        room[
            "disconnected_players"
        ].get(
            player_number
        )
    )


    # すでに再接続済みなら終了
    if (
        disconnected_player
        is None
    ):

        return


    # 別のプレイヤー情報なら終了
    if (
        disconnected_player.get(
            "user_id"
        )
        !=
        user_id
    ):

        return


    # このPlayerのタイマーを削除
    room[
        "reconnect_tasks"
    ].pop(
        player_number,
        None
    )


    # =========================================
    # 残っている相手のSocketを取得
    # =========================================

    remaining_sockets = [

        player_socket

        for index, player_socket
        in enumerate(
            room[
                "players"
            ],
            start=1
        )

        if (
            index
            !=
            player_number
        )
    ]


    # =========================================
    # ROOM DELETE
    # =========================================

    rooms.pop(
        room_id,
        None
    )


    # 他の再接続タイマーがあれば停止
    for task in list(
        room[
            "reconnect_tasks"
        ].values()
    ):

        if (
            not task.done()
        ):

            task.cancel()


    room[
        "reconnect_tasks"
    ].clear()


    room[
        "disconnected_players"
    ].clear()


    room[
        "players"
    ].clear()


    room[
        "player_names"
    ].clear()


    room[
        "player_user_ids"
    ].clear()


    # =========================================
    # 相手に切断確定を通知
    # =========================================

    for player_socket in (
        remaining_sockets
    ):

        try:

            await player_socket.send_json({

                "type":
                    "opponent_disconnected"
            })

        except Exception:

            pass


    print(
        f"ルーム {room_id}: "
        f"Player {player_number} "
        f"{RECONNECT_GRACE_SECONDS}秒以内に"
        "再接続しなかったため"
        "ルームを削除しました"
    )


# =============================================
# START RECONNECT WAIT
# =============================================

def start_reconnect_wait(
    room_id,
    room,
    player_number,
    user_id,
    player_name
):

    # 同じPlayerの古いタイマーがあれば止める
    cancel_reconnect_task(
        room,
        player_number
    )


    # 切断中プレイヤーとして記録
    room[
        "disconnected_players"
    ][
        player_number
    ] = {
        "user_id":
            user_id,

        "player_name":
            player_name
    }


    # 再接続待ちタイマー開始
    task = asyncio.create_task(
        wait_for_reconnect_timeout(
            room_id,
            room,
            player_number,
            user_id
        )
    )


    room[
        "reconnect_tasks"
    ][
        player_number
    ] = task


    print(
        f"ルーム {room_id}: "
        f"Player {player_number} "
        f"再接続待ち開始 "
        f"({RECONNECT_GRACE_SECONDS}秒)"
    )


# =============================================
# RECONNECT PLAYER CHECK
# =============================================

def get_reconnecting_player_number(
    room,
    user_id
):

    player_number = (
        get_player_number_by_user_id(
            room,
            user_id
        )
    )


    if (
        player_number
        is None
    ):

        return None


    disconnected_player = (
        room[
            "disconnected_players"
        ].get(
            player_number
        )
    )


    if (
        disconnected_player
        is None
    ):

        return None


    if (
        disconnected_player.get(
            "user_id"
        )
        !=
        user_id
    ):

        return None


    return player_number


# =============================================
# RECONNECT WAITING CHECK
# =============================================

def is_reconnect_waiting(
    room
):

    if (
        room[
            "mode"
        ]
        !=
        "pvp"
    ):

        return False


    return any(

        player_socket
        is None

        for player_socket
        in room[
            "players"
        ]
    )


# =============================================
# PvP ROOM CREATE
# =============================================

@app.post("/rooms")
async def create_pvp_room():

    room_id = (
        generate_room_id()
    )


    rooms[
        room_id
    ] = create_room(
        mode="pvp"
    )


    print(
        f"PvPルーム "
        f"{room_id} "
        "を作成しました"
    )


    return {

        "room_id":
            room_id,

        "mode":
            "pvp"
    }


# =============================================
# QUICK MATCH RECONNECT CHECK
# =============================================

@app.get("/matchmaking/reconnect")
async def get_matchmaking_reconnect_room(
    authorization: str | None = Header(
        default=None
    )
):

    session_token = (
        get_bearer_token(
            authorization
        )
    )


    user = (
        get_user_by_session_token(
            session_token
        )
    )


    if (
        user is None
    ):

        raise HTTPException(
            status_code=401,
            detail="ログイン情報が無効です。"
        )


    user_id = (
        user[
            "user_id"
        ]
    )


    for room_id, room in rooms.items():

        if (
            room[
                "mode"
            ]
            !=
            "pvp"
        ):

            continue


        if (
            room[
                "ranked"
            ]
            is not True
        ):

            continue


        if (
            room[
                "game"
            ]
            is None
        ):

            continue


        for disconnected_player in (
            room[
                "disconnected_players"
            ].values()
        ):

            if (
                disconnected_player.get(
                    "user_id"
                )
                ==
                user_id
            ):

                return {

                    "reconnect_available":
                        True,

                    "room_id":
                        room_id
                }


    return {

        "reconnect_available":
            False,

        "room_id":
            None
    }


# =============================================
# QUICK MATCH
# =============================================

@app.post("/matchmaking")
async def matchmaking():

    global waiting_room_id


    async with matchmaking_lock:

        # =====================================
        # 待機中ルームがある
        # =====================================

        if (
            waiting_room_id
            is not None
        ):

            waiting_room = (
                rooms.get(
                    waiting_room_id
                )
            )


            if (
                waiting_room
                is not None

                and

                waiting_room[
                    "mode"
                ]
                ==
                "pvp"

                and

                len(
                    waiting_room[
                        "players"
                    ]
                )
                <
                2
            ):

                room_id = (
                    waiting_room_id
                )


                # 2人目が見つかったので
                # 待機ルームから外す
                waiting_room_id = (
                    None
                )


                return {

                    "room_id":
                        room_id,

                    "mode":
                        "pvp",

                    "matched":
                        True
                }


            waiting_room_id = (
                None
            )


        # =====================================
        # 待機中ルームがない
        #
        # → 新規作成
        # =====================================

        room_id = (
            generate_room_id()
        )


        rooms[
            room_id
        ] = create_room(
            mode="pvp",
            ranked=True
        )


        waiting_room_id = (
            room_id
        )


        return {

            "room_id":
                room_id,

            "mode":
                "pvp",

            "matched":
                False
        }


# =============================================
# QUICK MATCH CANCEL
# =============================================

@app.post(
    "/matchmaking/cancel/{room_id}"
)
async def cancel_matchmaking(
    room_id: str
):

    global waiting_room_id


    room_id = (
        room_id
        .strip()
        .upper()
    )


    async with matchmaking_lock:

        # =====================================
        # すでに待機対象ではない
        #
        # ＝相手が見つかった可能性が高い
        # =====================================

        if (
            waiting_room_id
            !=
            room_id
        ):

            return {

                "cancelled":
                    False,

                "reason":
                    "already_matched"
            }


        room = (
            rooms.get(
                room_id
            )
        )


        # =====================================
        # ルームがすでに消えている
        # =====================================

        if (
            room
            is None
        ):

            waiting_room_id = (
                None
            )


            return {

                "cancelled":
                    True
            }


        # =====================================
        # すでに対戦開始状態
        # =====================================

        if (
            room[
                "mode"
            ]
            !=
            "pvp"

            or

            len(
                room[
                    "players"
                ]
            )
            >=
            2

            or

            room[
                "game"
            ]
            is not None
        ):

            waiting_room_id = (
                None
            )


            return {

                "cancelled":
                    False,

                "reason":
                    "already_matched"
            }


        # =====================================
        # キャンセル成功
        # =====================================

        waiting_room_id = (
            None
        )


        rooms.pop(
            room_id,
            None
        )


        print(
            f"QUICK MATCH "
            f"{room_id} "
            "をキャンセルしました"
        )


        return {

            "cancelled":
                True
        }


# =============================================
# CPU ROOM CREATE
# =============================================

@app.post("/cpu-rooms")
async def create_cpu_room(
    level: int = 1
):

    if (
        level
        not in [
            1,
            2,
            3
        ]
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "CPUレベルは"
                "1、2、3のいずれかを"
                "指定してください。"
            )
        )


    room_id = (
        generate_room_id()
    )


    rooms[
        room_id
    ] = create_room(
        mode="cpu",
        cpu_level=level
    )


    print(
        f"CPU Lv.{level} "
        f"ルーム {room_id} "
        "を作成しました"
    )


    return {

        "room_id":
            room_id,

        "mode":
            "cpu",

        "cpu_level":
            level
    }


# =============================================
# CPU DECK
# =============================================

def build_full_deck():

    deck = []


    for suit in VALID_SUITS:

        for rank in VALID_RANKS:

            deck.append(
                Card(
                    suit,
                    rank
                )
            )


    deck.append(
        Card(
            "JOKER"
        )
    )


    return deck


# =============================================
# CPU CANDIDATE HANDS
# =============================================

def build_cpu_candidate_hands(
    game
):

    cpu_cards = set(
        game
        .player2
        .hand
    )


    unknown_cards = [

        card

        for card
        in build_full_deck()

        if card
        not in cpu_cards
    ]


    # CPU自身の3枚を除外
    # 50枚から3枚
    #
    # C(50, 3) = 19600
    return list(
        combinations(
            unknown_cards,
            3
        )
    )


# =============================================
# CPU QUESTION SPECS
# =============================================

def get_all_question_specs():

    specs = [

        (
            "even",
            None
        ),

        (
            "odd",
            None
        ),

        (
            "face",
            None
        )
    ]


    # ランク
    for rank in VALID_RANKS:

        specs.append(
            (
                "rank",
                rank
            )
        )


    # 以上
    for number in range(
        1,
        14
    ):

        specs.append(
            (
                "more_than",
                number
            )
        )


    # 以下
    for number in range(
        1,
        14
    ):

        specs.append(
            (
                "less_than",
                number
            )
        )


    # スート
    for suit in VALID_SUITS:

        specs.append(
            (
                "suit",
                suit
            )
        )


    # JOKER
    specs.append(
        (
            "joker",
            None
        )
    )


    return specs


# =============================================
# CPU QUESTION TEXT
# =============================================

def get_question_text(
    spec
):

    question_type, value = (
        spec
    )


    if (
        question_type
        ==
        "even"
    ):

        return (
            "偶数はある？"
        )


    if (
        question_type
        ==
        "odd"
    ):

        return (
            "奇数はある？"
        )


    if (
        question_type
        ==
        "face"
    ):

        return (
            "絵札はある？"
        )


    if (
        question_type
        ==
        "rank"
    ):

        return (
            f"{value} はある？"
        )


    if (
        question_type
        ==
        "more_than"
    ):

        return (
            f"{value} 以上の"
            "カードはある？"
        )


    if (
        question_type
        ==
        "less_than"
    ):

        return (
            f"{value} 以下の"
            "カードはある？"
        )


    if (
        question_type
        ==
        "suit"
    ):

        return (
            f"{value}はある？"
        )


    if (
        question_type
        ==
        "joker"
    ):

        return (
            "JOKERはある？"
        )


    return (
        "不明な質問"
    )


# =============================================
# CPU QUESTION EVALUATION
# =============================================

def evaluate_question_spec(
    game,
    hand,
    found_cards,
    spec
):

    question_type, value = (
        spec
    )


    manager = (
        game
        .question_manager
    )


    if (
        question_type
        ==
        "even"
    ):

        return (
            manager
            .ask_even(
                hand,
                found_cards
            )
        )


    if (
        question_type
        ==
        "odd"
    ):

        return (
            manager
            .ask_odd(
                hand,
                found_cards
            )
        )


    if (
        question_type
        ==
        "face"
    ):

        return (
            manager
            .ask_face(
                hand,
                found_cards
            )
        )


    if (
        question_type
        ==
        "rank"
    ):

        return (
            manager
            .ask_rank(
                hand,
                found_cards,
                value
            )
        )


    if (
        question_type
        ==
        "more_than"
    ):

        return (
            manager
            .ask_more_than(
                hand,
                found_cards,
                value
            )
        )


    if (
        question_type
        ==
        "less_than"
    ):

        return (
            manager
            .ask_less_than(
                hand,
                found_cards,
                value
            )
        )


    if (
        question_type
        ==
        "suit"
    ):

        return (
            manager
            .ask_suit(
                hand,
                found_cards,
                value
            )
        )


    if (
        question_type
        ==
        "joker"
    ):

        return (
            manager
            .ask_joker(
                hand,
                found_cards
            )
        )


    raise ValueError(
        "不明なCPU質問です。"
    )


# =============================================
# CPU UNUSED QUESTIONS
# =============================================

def get_unused_question_specs(
    room
):

    all_specs = (
        get_all_question_specs()
    )


    unused = [

        spec

        for spec
        in all_specs

        if spec
        not in room[
            "cpu_used_questions"
        ]
    ]


    if unused:

        return unused


    room[
        "cpu_used_questions"
    ].clear()


    return all_specs


# =============================================
# CPU QUESTION SELECT
# =============================================

def choose_cpu_question(
    room
):

    level = (
        room[
            "cpu_level"
        ]
    )


    game = (
        room[
            "game"
        ]
    )


    cpu_player = (
        game
        .player2
    )


    # =========================================
    # Lv.1
    #
    # 完全ランダム
    # =========================================

    if (
        level
        ==
        1
    ):

        spec = (
            random.choice(
                get_all_question_specs()
            )
        )


        return {

            "spec":
                spec,

            "before_candidate_count":
                None,

            "yes_prediction_count":
                None,

            "no_prediction_count":
                None,

            "split_score":
                None
        }


    available_specs = (
        get_unused_question_specs(
            room
        )
    )


    # =========================================
    # Lv.2
    #
    # 未使用質問からランダム
    # =========================================

    if (
        level
        ==
        2
    ):

        spec = (
            random.choice(
                available_specs
            )
        )


        room[
            "cpu_used_questions"
        ].add(
            spec
        )


        return {

            "spec":
                spec,

            "before_candidate_count":
                len(
                    room[
                        "cpu_candidate_hands"
                    ]
                ),

            "yes_prediction_count":
                None,

            "no_prediction_count":
                None,

            "split_score":
                None
        }


    # =========================================
    # Lv.3
    #
    # YES / NO が最も半分になる質問
    # =========================================

    candidates = (
        room[
            "cpu_candidate_hands"
        ]
    )


    before_count = (
        len(
            candidates
        )
    )


    best_entries = []

    best_score = None


    for spec in available_specs:

        yes_count = 0


        for candidate in candidates:

            answer = (
                evaluate_question_spec(
                    game,
                    candidate,
                    cpu_player.found_cards,
                    spec
                )
            )


            if answer:

                yes_count += 1


        no_count = (
            before_count
            -
            yes_count
        )


        # 全部YESまたは全部NOなら
        # 情報量が増えない
        if (
            yes_count
            ==
            0

            or

            no_count
            ==
            0
        ):

            continue


        score = abs(
            yes_count
            -
            no_count
        )


        entry = {

            "spec":
                spec,

            "before_candidate_count":
                before_count,

            "yes_prediction_count":
                yes_count,

            "no_prediction_count":
                no_count,

            "split_score":
                score
        }


        if (
            best_score
            is None

            or

            score
            <
            best_score
        ):

            best_score = (
                score
            )

            best_entries = [
                entry
            ]


        elif (
            score
            ==
            best_score
        ):

            best_entries.append(
                entry
            )


    # =========================================
    # 最良質問があった
    # =========================================

    if best_entries:

        selected = (
            random.choice(
                best_entries
            )
        )


        room[
            "cpu_used_questions"
        ].add(
            selected[
                "spec"
            ]
        )


        return selected


    # =========================================
    # 全質問が情報量0
    #
    # → 未使用からランダム
    # =========================================

    spec = (
        random.choice(
            available_specs
        )
    )


    room[
        "cpu_used_questions"
    ].add(
        spec
    )


    return {

        "spec":
            spec,

        "before_candidate_count":
            before_count,

        "yes_prediction_count":
            None,

        "no_prediction_count":
            None,

        "split_score":
            None
    }


# =============================================
# CPU CANDIDATE FILTER
# =============================================

def filter_cpu_candidates_by_question(
    room,
    spec,
    actual_answer
):

    game = (
        room[
            "game"
        ]
    )


    cpu_player = (
        game
        .player2
    )


    room[
        "cpu_candidate_hands"
    ] = [

        candidate

        for candidate
        in room[
            "cpu_candidate_hands"
        ]

        if (
            evaluate_question_spec(
                game,
                candidate,
                cpu_player.found_cards,
                spec
            )
            ==
            actual_answer
        )
    ]


# =============================================
# CPU RANDOM GUESS
# =============================================

def choose_random_cpu_guess(
    room
):

    game = (
        room[
            "game"
        ]
    )


    cpu_player = (
        game
        .player2
    )


    blocked = (

        set(
            cpu_player.hand
        )

        |

        set(
            cpu_player.found_cards
        )

        |

        room[
            "cpu_wrong_guesses"
        ]
    )


    possible_cards = [

        card

        for card
        in build_full_deck()

        if card
        not in blocked
    ]


    if (
        not possible_cards
    ):

        possible_cards = (
            build_full_deck()
        )


    return (
        random.choice(
            possible_cards
        )
    )


# =============================================
# CPU THINKING GUESS
# =============================================

def choose_thinking_cpu_guess(
    room
):

    game = (
        room[
            "game"
        ]
    )


    cpu_player = (
        game
        .player2
    )


    blocked = (

        set(
            cpu_player.hand
        )

        |

        set(
            cpu_player.found_cards
        )

        |

        room[
            "cpu_wrong_guesses"
        ]
    )


    frequencies = {}


    for candidate in room[
        "cpu_candidate_hands"
    ]:

        for card in candidate:

            if (
                card
                in blocked
            ):

                continue


            frequencies[
                card
            ] = (
                frequencies.get(
                    card,
                    0
                )
                +
                1
            )


    if (
        not frequencies
    ):

        return (
            choose_random_cpu_guess(
                room
            )
        )


    highest = max(
        frequencies.values()
    )


    best_cards = [

        card

        for card, count
        in frequencies.items()

        if (
            count
            ==
            highest
        )
    ]


    return (
        random.choice(
            best_cards
        )
    )


# =============================================
# CPU GUESS FILTER
# =============================================

def update_cpu_candidates_after_guess(
    room,
    guess,
    correct
):

    if correct:

        room[
            "cpu_candidate_hands"
        ] = [

            candidate

            for candidate
            in room[
                "cpu_candidate_hands"
            ]

            if (
                guess
                in candidate
            )
        ]


    else:

        room[
            "cpu_candidate_hands"
        ] = [

            candidate

            for candidate
            in room[
                "cpu_candidate_hands"
            ]

            if (
                guess
                not in candidate
            )
        ]


        room[
            "cpu_wrong_guesses"
        ].add(
            guess
        )


# =============================================
# NEW GAME
# =============================================

async def start_new_game(
    room_id
):

    room = (
        rooms.get(
            room_id
        )
    )


    if (
        room
        is None
    ):

        return


    # =========================================
    # PvP
    # =========================================

    if (
        room[
            "mode"
        ]
        ==
        "pvp"
    ):

        if (
            len(
                room[
                    "players"
                ]
            )
            !=
            2
        ):

            return


    # =========================================
    # CPU
    # =========================================

    else:

        if (
            len(
                room[
                    "players"
                ]
            )
            !=
            1
        ):

            return


    room[
        "game"
    ] = Game()


    room[
        "game_started_at"
    ] = time.monotonic()


    # =========================================
    # RANKED MATCH ID
    # =========================================

    if (
        room[
            "mode"
        ]
        ==
        "pvp"

        and

        room[
            "ranked"
        ]
    ):

        room[
            "current_match_id"
        ] = secrets.token_urlsafe(24)

    else:

        room[
            "current_match_id"
        ] = None


    room[
        "current_turn"
    ] = 1


    room[
        "current_phase"
    ] = "question"


    room[
        "rematch_requests"
    ].clear()


    room[
        "cpu_wrong_guesses"
    ].clear()


    room[
        "cpu_used_questions"
    ].clear()


    game = (
        room[
            "game"
        ]
    )


    player1_hand = [

        str(
            card
        )

        for card
        in game.player1.hand
    ]


    player2_hand = [

        str(
            card
        )

        for card
        in game.player2.hand
    ]


    # =========================================
    # CPU GAME
    # =========================================

    if (
        room[
            "mode"
        ]
        ==
        "cpu"
    ):

        room[
            "cpu_candidate_hands"
        ] = (
            build_cpu_candidate_hands(
                game
            )
        )


        player1_name = (
            room[
                "player_names"
            ][
                0
            ]
        )


        player2_name = (
            get_cpu_name(
                room
            )
        )


        await (
            room[
                "players"
            ][
                0
            ]
            .send_json({

                "type":
                    "game_start",

                "player":
                    1,

                "hand":
                    player1_hand,

                "your_turn":
                    True,

                "phase":
                    "question",

                "mode":
                    "cpu",

                "cpu_level":
                    room[
                        "cpu_level"
                    ],

                "candidate_count":
                    len(
                        room[
                            "cpu_candidate_hands"
                        ]
                    ),

                "player1_name":
                    player1_name,

                "player2_name":
                    player2_name
            })
        )


        print(
            f"ルーム {room_id}: "
            f"{player1_name} "
            "vs "
            f"{player2_name} "
            "開始"
        )


        return


    # =========================================
    # PvP GAME
    # =========================================

    room[
        "cpu_candidate_hands"
    ] = []


    player1_name = (
        room[
            "player_names"
        ][
            0
        ]
    )


    player2_name = (
        room[
            "player_names"
        ][
            1
        ]
    )


    await (
        room[
            "players"
        ][
            0
        ]
        .send_json({

            "type":
                "game_start",

            "player":
                1,

            "hand":
                player1_hand,

            "your_turn":
                True,

            "phase":
                "question",

            "mode":
                "pvp",

            "ranked":
                room[
                    "ranked"
                ],

            "player1_name":
                player1_name,

            "player2_name":
                player2_name
        })
    )


    await (
        room[
            "players"
        ][
            1
        ]
        .send_json({

            "type":
                "game_start",

            "player":
                2,

            "hand":
                player2_hand,

            "your_turn":
                False,

            "phase":
                "waiting",

            "mode":
                "pvp",

            "ranked":
                room[
                    "ranked"
                ],

            "player1_name":
                player1_name,

            "player2_name":
                player2_name
        })
    )


    print(
        f"ルーム {room_id}: "
        f"{player1_name} "
        "vs "
        f"{player2_name} "
        "開始"
    )


# =============================================
# RECONNECT STATE
# =============================================

async def send_reconnect_state(
    websocket,
    room,
    player_number
):

    game = (
        room[
            "game"
        ]
    )


    if (
        game is None
    ):

        return


    if (
        player_number
        ==
        1
    ):

        player = (
            game.player1
        )

    else:

        player = (
            game.player2
        )


    hand = [

        str(
            card
        )

        for card
        in player.hand
    ]


    if (
        room[
            "mode"
        ]
        ==
        "cpu"
    ):

        player1_name = (
            room[
                "player_names"
            ][
                0
            ]
        )

        player2_name = (
            get_cpu_name(
                room
            )
        )

    else:

        player1_name = (
            room[
                "player_names"
            ][
                0
            ]
        )

        player2_name = (
            room[
                "player_names"
            ][
                1
            ]
        )


    await websocket.send_json({

        "type":
            "reconnect_state",

        "player":
            player_number,

        "hand":
            hand,

        "current_turn":
            room[
                "current_turn"
            ],

        "your_turn":
            (
                room[
                    "current_turn"
                ]
                ==
                player_number
            ),

        "phase":
            room[
                "current_phase"
            ],

        "found_count":
            len(
                player.found_cards
            ),

        "mode":
            room[
                "mode"
            ],

        "ranked":
            room[
                "ranked"
            ],

        "cpu_level":
            room[
                "cpu_level"
            ],

        "player1_name":
            player1_name,

        "player2_name":
            player2_name
    })


# =============================================
# GAME OVER
# =============================================

async def finish_game(
    room,
    winner
):

    if (
        room[
            "game"
        ]
        is None
    ):

        return


    game_started_at = (
        room.get(
            "game_started_at"
        )
    )


    if (
        game_started_at
        is None
    ):

        duration_seconds = 0

    else:

        duration_seconds = int(
            time.monotonic()
            -
            game_started_at
        )


    room[
        "current_phase"
    ] = "finished"


    room[
        "rematch_requests"
    ].clear()


    player1_hand = [

        str(
            card
        )

        for card
        in room[
            "game"
        ].player1.hand
    ]


    player2_hand = [

        str(
            card
        )

        for card
        in room[
            "game"
        ].player2.hand
    ]


    if (
        room[
            "player_names"
        ]
    ):

        player1_name = (
            room[
                "player_names"
            ][
                0
            ]
        )

    else:

        player1_name = (
            "PLAYER 1"
        )


    if (
        room[
            "mode"
        ]
        ==
        "cpu"
    ):

        player2_name = (
            get_cpu_name(
                room
            )
        )

    elif (
        len(
            room[
                "player_names"
            ]
        )
        >=
        2
    ):

        player2_name = (
            room[
                "player_names"
            ][
                1
            ]
        )

    else:

        player2_name = (
            "PLAYER 2"
        )


    # =========================================
    # RANKED RESULT
    # =========================================

    ranked_result = None


    if (
        room[
            "mode"
        ]
        ==
        "pvp"

        and

        room[
            "ranked"
        ]

        and

        winner
        in [
            1,
            2
        ]

        and

        len(
            room[
                "player_user_ids"
            ]
        )
        >=
        2

        and

        room.get(
            "current_match_id"
        )
    ):

        if (
            winner
            ==
            1
        ):

            winner_user_id = (
                room[
                    "player_user_ids"
                ][
                    0
                ]
            )

            loser_user_id = (
                room[
                    "player_user_ids"
                ][
                    1
                ]
            )

        else:

            winner_user_id = (
                room[
                    "player_user_ids"
                ][
                    1
                ]
            )

            loser_user_id = (
                room[
                    "player_user_ids"
                ][
                    0
                ]
            )


        try:

            ranked_result = await asyncio.to_thread(
                record_ranked_match,
                room[
                    "current_match_id"
                ],
                winner_user_id,
                loser_user_id
            )


            print(
                "RANKED MATCH: "
                f"{player1_name} vs {player2_name} / "
                f"winner=Player {winner} / "
                f"match_id={room['current_match_id']}"
            )

        except Exception as error:

            print(
                "RANKED RESULT ERROR: "
                f"{error}"
            )


    data = {

        "type":
            "game_over",

        "winner":
            winner,

        "player1_hand":
            player1_hand,

        "player2_hand":
            player2_hand,

        "player1_name":
            player1_name,

        "player2_name":
            player2_name,

        "mode":
            room[
                "mode"
            ],

        "ranked":
            room[
                "ranked"
            ],

        "ranked_result":
            ranked_result,

        "duration_seconds":
            duration_seconds,

        "cpu_level":
            room[
                "cpu_level"
            ]
    }


    for player_socket in list(
        room[
            "players"
        ]
    ):

        try:

            await (
                player_socket
                .send_json(
                    data
                )
            )

        except Exception:

            pass


# =============================================
# TURN CHANGE
# =============================================

async def send_turn_changed(
    room
):

    current_turn = (
        room[
            "current_turn"
        ]
    )


    # =========================================
    # CPU
    # =========================================

    if (
        room[
            "mode"
        ]
        ==
        "cpu"
    ):

        if (
            not room[
                "players"
            ]
        ):

            return


        await (
            room[
                "players"
            ][
                0
            ]
            .send_json({

                "type":
                    "turn_changed",

                "current_turn":
                    current_turn,

                "your_turn":
                    (
                        current_turn
                        ==
                        1
                    ),

                "phase":
                    (
                        "question"

                        if (
                            current_turn
                            ==
                            1
                        )

                        else

                        "waiting"
                    ),

                "mode":
                    "cpu",

                "cpu_level":
                    room[
                        "cpu_level"
                    ]
            })
        )


        return


    # =========================================
    # PvP
    # =========================================

    if (
        len(
            room[
                "players"
            ]
        )
        <
        2
    ):

        return


    await (
        room[
            "players"
        ][
            0
        ]
        .send_json({

            "type":
                "turn_changed",

            "current_turn":
                current_turn,

            "your_turn":
                (
                    current_turn
                    ==
                    1
                ),

            "phase":
                (
                    "question"

                    if (
                        current_turn
                        ==
                        1
                    )

                    else

                    "waiting"
                ),

            "mode":
                "pvp"
        })
    )


    await (
        room[
            "players"
        ][
            1
        ]
        .send_json({

            "type":
                "turn_changed",

            "current_turn":
                current_turn,

            "your_turn":
                (
                    current_turn
                    ==
                    2
                ),

            "phase":
                (
                    "question"

                    if (
                        current_turn
                        ==
                        2
                    )

                    else

                    "waiting"
                ),

            "mode":
                "pvp"
        })
    )


# =============================================
# CPU TURN
# =============================================

async def cpu_turn(
    room_id
):

    room = (
        rooms.get(
            room_id
        )
    )


    if (
        room
        is None

        or

        room[
            "mode"
        ]
        !=
        "cpu"

        or

        room[
            "game"
        ]
        is None

        or

        not room[
            "players"
        ]

        or

        room[
            "current_phase"
        ]
        ==
        "finished"
    ):

        return


    game = (
        room[
            "game"
        ]
    )


    human = (
        game
        .player1
    )


    cpu = (
        game
        .player2
    )


    websocket = (
        room[
            "players"
        ][
            0
        ]
    )


    room[
        "current_turn"
    ] = 2


    room[
        "current_phase"
    ] = "question"


    # =========================================
    # CPU QUESTION
    # =========================================

    question_info = (
        choose_cpu_question(
            room
        )
    )


    spec = (
        question_info[
            "spec"
        ]
    )


    actual_answer = (
        evaluate_question_spec(
            game,
            human.hand,
            cpu.found_cards,
            spec
        )
    )


    # =========================================
    # Lv.2 / Lv.3
    #
    # 質問結果で候補を絞る
    # =========================================

    if (
        room[
            "cpu_level"
        ]
        in [
            2,
            3
        ]
    ):

        filter_cpu_candidates_by_question(
            room,
            spec,
            actual_answer
        )


    await asyncio.sleep(
        0.7
    )


    await websocket.send_json({

        "type":
            "cpu_question",

        "cpu_level":
            room[
                "cpu_level"
            ],

        "question":
            get_question_text(
                spec
            ),

        "answer":
            actual_answer,

        "candidate_count":
            (
                len(
                    room[
                        "cpu_candidate_hands"
                    ]
                )

                if (
                    room[
                        "cpu_level"
                    ]
                    in [
                        2,
                        3
                    ]
                )

                else

                None
            ),

        "before_candidate_count":
            question_info[
                "before_candidate_count"
            ],

        "yes_prediction_count":
            question_info[
                "yes_prediction_count"
            ],

        "no_prediction_count":
            question_info[
                "no_prediction_count"
            ],

        "split_score":
            question_info[
                "split_score"
            ]
    })


    await asyncio.sleep(
        1.0
    )


    # =========================================
    # CPU GUESS
    # =========================================

    if (
        room[
            "cpu_level"
        ]
        ==
        1
    ):

        guess = (
            choose_random_cpu_guess(
                room
            )
        )

    else:

        guess = (
            choose_thinking_cpu_guess(
                room
            )
        )


    correct = (
        game
        .guess_card(
            cpu,
            human,
            guess
        )
    )


    # =========================================
    # CPU候補更新
    # =========================================

    if (
        room[
            "cpu_level"
        ]
        in [
            2,
            3
        ]
    ):

        update_cpu_candidates_after_guess(
            room,
            guess,
            correct
        )

    elif (
        not correct
    ):

        room[
            "cpu_wrong_guesses"
        ].add(
            guess
        )


    await websocket.send_json({

        "type":
            "cpu_guess_result",

        "cpu_level":
            room[
                "cpu_level"
            ],

        "guess":
            str(
                guess
            ),

        "correct":
            correct,

        "found_count":
            len(
                cpu
                .found_cards
            ),

        "candidate_count":
            (
                len(
                    room[
                        "cpu_candidate_hands"
                    ]
                )

                if (
                    room[
                        "cpu_level"
                    ]
                    in [
                        2,
                        3
                    ]
                )

                else

                None
            )
    })


    # =========================================
    # CPU WIN
    # =========================================

    if (
        cpu
        .is_winner()
    ):

        await asyncio.sleep(
            0.8
        )


        await finish_game(
            room,
            2
        )


        return


    # =========================================
    # HUMAN TURN
    # =========================================

    await asyncio.sleep(
        0.8
    )


    room = (
        rooms.get(
            room_id
        )
    )


    if (
        room
        is None

        or

        room[
            "game"
        ]
        is None

        or

        not room[
            "players"
        ]
    ):

        return


    room[
        "current_turn"
    ] = 1


    room[
        "current_phase"
    ] = "question"


    await send_turn_changed(
        room
    )


# =============================================
# HUMAN QUESTION
# =============================================

async def process_human_question(
    websocket,
    room,
    player_number,
    data
):

    if (
        room[
            "current_phase"
        ]
        !=
        "question"
    ):

        await websocket.send_json({

            "type":
                "error",

            "message":
                "今はカードを"
                "予想する番です。"
        })


        return False


    if (
        player_number
        ==
        1
    ):

        asking_player = (
            room[
                "game"
            ].player1
        )


        opponent = (
            room[
                "game"
            ].player2
        )

    else:

        asking_player = (
            room[
                "game"
            ].player2
        )


        opponent = (
            room[
                "game"
            ].player1
        )


    question_id = (
        data.get(
            "question_id"
        )
    )


    manager = (
        room[
            "game"
        ]
        .question_manager
    )


    # =========================================
    # 1 EVEN
    # =========================================

    if (
        question_id
        ==
        1
    ):

        answer = (
            manager
            .ask_even(
                opponent.hand,
                asking_player.found_cards
            )
        )


        question_text = (
            "偶数はある？"
        )


    # =========================================
    # 2 ODD
    # =========================================

    elif (
        question_id
        ==
        2
    ):

        answer = (
            manager
            .ask_odd(
                opponent.hand,
                asking_player.found_cards
            )
        )


        question_text = (
            "奇数はある？"
        )


    # =========================================
    # 3 FACE
    # =========================================

    elif (
        question_id
        ==
        3
    ):

        answer = (
            manager
            .ask_face(
                opponent.hand,
                asking_player.found_cards
            )
        )


        question_text = (
            "絵札はある？"
        )


    # =========================================
    # 4 RANK
    # =========================================

    elif (
        question_id
        ==
        4
    ):

        rank = (
            str(
                data.get(
                    "rank",
                    ""
                )
            )
            .upper()
        )


        if (
            rank
            not in VALID_RANKS
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "指定したランクが"
                    "正しくありません。"
            })


            return False


        answer = (
            manager
            .ask_rank(
                opponent.hand,
                asking_player.found_cards,
                rank
            )
        )


        question_text = (
            f"{rank} はある？"
        )


    # =========================================
    # 5 >=
    # =========================================

    elif (
        question_id
        ==
        5
    ):

        number = (
            data.get(
                "number"
            )
        )


        if (
            not isinstance(
                number,
                int
            )

            or

            number
            <
            1

            or

            number
            >
            13
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "数字は1～13で"
                    "指定してください。"
            })


            return False


        answer = (
            manager
            .ask_more_than(
                opponent.hand,
                asking_player.found_cards,
                number
            )
        )


        question_text = (
            f"{number} 以上の"
            "カードはある？"
        )


    # =========================================
    # 6 <=
    # =========================================

    elif (
        question_id
        ==
        6
    ):

        number = (
            data.get(
                "number"
            )
        )


        if (
            not isinstance(
                number,
                int
            )

            or

            number
            <
            1

            or

            number
            >
            13
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "数字は1～13で"
                    "指定してください。"
            })


            return False


        answer = (
            manager
            .ask_less_than(
                opponent.hand,
                asking_player.found_cards,
                number
            )
        )


        question_text = (
            f"{number} 以下の"
            "カードはある？"
        )


    # =========================================
    # 7 SPADE
    # =========================================

    elif (
        question_id
        ==
        7
    ):

        answer = (
            manager
            .ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "スペード"
            )
        )


        question_text = (
            "スペードはある？"
        )


    # =========================================
    # 8 HEART
    # =========================================

    elif (
        question_id
        ==
        8
    ):

        answer = (
            manager
            .ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "ハート"
            )
        )


        question_text = (
            "ハートはある？"
        )


    # =========================================
    # 9 DIAMOND
    # =========================================

    elif (
        question_id
        ==
        9
    ):

        answer = (
            manager
            .ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "ダイヤ"
            )
        )


        question_text = (
            "ダイヤはある？"
        )


    # =========================================
    # 10 CLUB
    # =========================================

    elif (
        question_id
        ==
        10
    ):

        answer = (
            manager
            .ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "クラブ"
            )
        )


        question_text = (
            "クラブはある？"
        )


    # =========================================
    # 11 JOKER
    # =========================================

    elif (
        question_id
        ==
        11
    ):

        answer = (
            manager
            .ask_joker(
                opponent.hand,
                asking_player.found_cards
            )
        )


        question_text = (
            "JOKERはある？"
        )


    # =========================================
    # INVALID
    # =========================================

    else:

        await websocket.send_json({

            "type":
                "error",

            "message":
                "質問番号が"
                "正しくありません。"
        })


        return False


    # =========================================
    # GUESS PHASE
    # =========================================

    room[
        "current_phase"
    ] = "guess"


    await websocket.send_json({

        "type":
            "question_result",

        "question":
            question_text,

        "answer":
            answer
    })


    return True


# =============================================
# HUMAN GUESS
# =============================================

async def process_human_guess(
    websocket,
    room,
    player_number,
    data
):

    if (
        room[
            "current_phase"
        ]
        !=
        "guess"
    ):

        await websocket.send_json({

            "type":
                "error",

            "message":
                "先に質問してください。"
        })


        return False


    if (
        player_number
        ==
        1
    ):

        guessing_player = (
            room[
                "game"
            ].player1
        )


        opponent = (
            room[
                "game"
            ].player2
        )

    else:

        guessing_player = (
            room[
                "game"
            ].player2
        )


        opponent = (
            room[
                "game"
            ].player1
        )


    suit = (
        data.get(
            "suit"
        )
    )


    rank = (
        data.get(
            "rank"
        )
    )


    # =========================================
    # JOKER
    # =========================================

    if (
        suit
        ==
        "JOKER"
    ):

        guess = (
            Card(
                "JOKER"
            )
        )


    # =========================================
    # NORMAL CARD
    # =========================================

    else:

        if (
            suit
            not in VALID_SUITS
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "スートが"
                    "正しくありません。"
            })


            return False


        if (
            rank
            not in VALID_RANKS
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "ランクが"
                    "正しくありません。"
            })


            return False


        guess = (
            Card(
                suit,
                rank
            )
        )


    # =========================================
    # RESULT
    # =========================================

    correct = (
        room[
            "game"
        ]
        .guess_card(
            guessing_player,
            opponent,
            guess
        )
    )


    room[
        "current_phase"
    ] = "result"


    await websocket.send_json({

        "type":
            "guess_result",

        "guess":
            str(
                guess
            ),

        "correct":
            correct,

        "found_count":
            len(
                guessing_player
                .found_cards
            )
    })


    return True


# =============================================
# QUICK MATCH WAIT CLEAR
# =============================================

async def clear_waiting_room_if_needed(
    room_id
):

    global waiting_room_id


    async with matchmaking_lock:

        if (
            waiting_room_id
            ==
            room_id
        ):

            waiting_room_id = (
                None
            )


# =============================================
# WEBSOCKET
# =============================================

@app.websocket(
    "/ws/{room_id}"
)
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str
):

    await websocket.accept()


    # =========================================
    # ROOM ID
    # =========================================

    room_id = (
        room_id
        .strip()
        .upper()
    )


    # =========================================
    # WEBSOCKET AUTH
    # =========================================

    try:

        auth_data = await asyncio.wait_for(
            websocket.receive_json(),
            timeout=10
        )

    except Exception:

        try:
            await websocket.send_json({
                "type": "error",
                "code": "AUTH_REQUIRED",
                "message": "ログイン認証に失敗しました。"
            })
        except Exception:
            pass

        try:
            await websocket.close()
        except Exception:
            pass

        return


    if (
        not isinstance(auth_data, dict)
        or
        auth_data.get("type") != "authenticate"
    ):

        await websocket.send_json({
            "type": "error",
            "code": "AUTH_REQUIRED",
            "message": "最初にログイン認証が必要です。"
        })

        await websocket.close()

        return


    session_token = (
        auth_data.get("session_token")
        or
        ""
    )


    authenticated_user = (
        get_user_by_session_token(
            session_token
        )
    )


    if authenticated_user is None:

        await websocket.send_json({
            "type": "error",
            "code": "INVALID_SESSION",
            "message": (
                "ログイン情報が無効です。"
                "もう一度ログインしてください。"
            )
        })

        await websocket.close()

        return


    player_user_id = (
        authenticated_user[
            "user_id"
        ]
    )

    player_name = (
        authenticated_user[
            "name"
        ]
    )


    # =========================================
    # ROOM ID VALIDATION
    # =========================================

    if (
        not is_valid_room_id(
            room_id
        )
    ):

        await websocket.send_json({

            "type":
                "error",

            "code":
                "INVALID_ROOM_ID",

            "message":
                "ルームIDが"
                "正しくありません。"
        })


        await websocket.close()


        return


    # =========================================
    # ROOM EXISTS
    # =========================================

    room = (
        rooms.get(
            room_id
        )
    )


    if (
        room
        is None
    ):

        await websocket.send_json({

            "type":
                "error",

            "code":
                "ROOM_NOT_FOUND",

            "message":
                (
                    f"ルーム "
                    f"{room_id} "
                    "は存在しません。"
                )
        })


        await websocket.close()


        return


    # =========================================
    # RECONNECT CHECK
    # =========================================

    reconnecting_player_number = (
        get_reconnecting_player_number(
            room,
            player_user_id
        )
    )


    # =========================================
    # MAX PLAYERS
    # =========================================

    max_players = (

        1

        if (
            room[
                "mode"
            ]
            ==
            "cpu"
        )

        else

        2
    )


    if (
        len(
            room[
                "players"
            ]
        )
        >=
        max_players

        and

        reconnecting_player_number
        is None
    ):

        await websocket.send_json({

            "type":
                "error",

            "code":
                "ROOM_FULL",

            "message":
                (
                    f"ルーム "
                    f"{room_id} "
                    "は満員です。"
                )
        })


        await websocket.close()


        return


    # =========================================
    # SAME ACCOUNT CHECK
    # =========================================

    if (
        player_user_id
        in
        room[
            "player_user_ids"
        ]


        and

        reconnecting_player_number
        is None
    ):

        await websocket.send_json({
            "type": "error",
            "code": "SAME_ACCOUNT",
            "message": (
                "同じアカウントで同じルームに"
                "2人参加することはできません。"
            )
        })

        await websocket.close()

        return


    # =========================================
    # PLAYER REGISTER
    # =========================================

    if (
        reconnecting_player_number
        is not None
    ):

        # =====================================
        # RECONNECT
        # =====================================

        player_number = (
            reconnecting_player_number
        )


        player_index = (
            player_number - 1
        )


        # 元の席に新しいSocketを戻す
        room[
            "players"
        ][
            player_index
        ] = websocket


        # 再接続待ちタイマーを停止
        cancel_reconnect_task(
            room,
            player_number
        )


        # 切断中リストから削除
        room[
            "disconnected_players"
        ].pop(
            player_number,
            None
        )


        # =====================================
        # 相手に再接続成功を通知
        # =====================================

        if (
            room[
                "mode"
            ]
            ==
            "pvp"
        ):

            for other_socket in room[
                "players"
            ]:

                if (
                    other_socket
                    is None
                    or
                    other_socket
                    is websocket
                ):

                    continue


                try:

                    await other_socket.send_json({

                        "type":
                            "opponent_reconnected"
                    })

                except Exception:

                    pass


        print(
            f"ルーム {room_id}: "
            f"Player {player_number} "
            "再接続"
        )


    else:

        # =====================================
        # NEW PLAYER
        # =====================================

        room[
            "players"
        ].append(
            websocket
        )


        room[
            "player_names"
        ].append(
            player_name
        )


        room[
            "player_user_ids"
        ].append(
            player_user_id
        )


        player_number = (
            len(
                room[
                    "players"
                ]
            )
        )

    await websocket.send_json({

        "type":
            "player_number",

        "player":
            player_number,

        "player_name":
            player_name,

        "room_id":
            room_id,

        "mode":
            room[
                "mode"
            ],

        "ranked":
            room[
                "ranked"
            ],

        "cpu_level":
            room[
                "cpu_level"
            ]
    })


    print(
        f"ルーム {room_id}: "
        f"{player_name} / "
        f"Player {player_number} "
        "接続"
    )


        # =========================================
    # SEND RECONNECT STATE
    # =========================================

    if (
        reconnecting_player_number
        is not None
    ):

        await send_reconnect_state(
            websocket,
            room,
            player_number
        )


    # =========================================
    # START GAME
    # =========================================

    if (
        reconnecting_player_number
        is None
    ):

        # =========================================
        # START CPU
        # =========================================

        if (
            room[
                "mode"
            ]
            ==
            "cpu"
        ):

            await start_new_game(
                room_id
            )


        # =========================================
        # START PvP
        # =========================================

        elif (
            len(
                room[
                    "players"
                ]
            )
            ==
            2
        ):

            await start_new_game(
                room_id
            )

    # =============================================
    # MAIN LOOP
    # =============================================

    try:

        while True:

            data = (
                await websocket
                .receive_json()
            )


            # キャンセルなどで
            # 既にルーム削除済み
            if (
                rooms.get(
                    room_id
                )
                is not room
            ):

                return


            if (
                websocket
                not in room[
                    "players"
                ]
            ):

                return


            player_number = (
                room[
                    "players"
                ]
                .index(
                    websocket
                )
                +
                1
            )


            message_type = (
                data.get(
                    "type"
                )
            )


            # =====================================
            # REMATCH
            # =====================================

            if (
                message_type
                ==
                "rematch_request"
            ):

                if (
                    room[
                        "current_phase"
                    ]
                    !=
                    "finished"
                ):

                    await websocket.send_json({

                        "type":
                            "error",

                        "message":
                            "今は再戦を"
                            "選択できません。"
                    })


                    continue


                # =============================
                # CPU
                # =============================

                if (
                    room[
                        "mode"
                    ]
                    ==
                    "cpu"
                ):

                    await start_new_game(
                        room_id
                    )


                    continue


                # =============================
                # PvP
                # =============================

                room[
                    "rematch_requests"
                ].add(
                    player_number
                )


                if (
                    room[
                        "rematch_requests"
                    ]
                    ==
                    {
                        1,
                        2
                    }
                ):

                    await start_new_game(
                        room_id
                    )


                else:

                    await websocket.send_json({

                        "type":
                            "rematch_waiting"
                    })


                continue


            # =====================================
            # LEAVE
            # =====================================

            if (
                message_type
                ==
                "leave_game"
            ):

                await (
                    clear_waiting_room_if_needed(
                        room_id
                    )
                )


                other_sockets = [

                    player_socket

                    for player_socket
                    in room[
                        "players"
                    ]

                    if (
                        player_socket
                        !=
                        websocket
                    )
                ]


                rooms.pop(
                    room_id,
                    None
                )


                room[
                    "players"
                ].clear()


                room[
                    "player_names"
                ].clear()


                room[
                    "player_user_ids"
                ].clear()


                for player_socket in (
                    other_sockets
                ):

                    try:

                        await (
                            player_socket
                            .send_json({

                                "type":
                                    "opponent_left"
                            })
                        )

                    except Exception:

                        pass


                return


            # =====================================
            # GAME NOT STARTED
            # =====================================

            if (
                room[
                    "game"
                ]
                is None
            ):

                await websocket.send_json({

                    "type":
                        "error",

                    "message":
                        "まだゲームが"
                        "開始されていません。"
                })


                continue


            # =====================================
            # FINISHED
            # =====================================

            if (
                room[
                    "current_phase"
                ]
                ==
                "finished"
            ):

                await websocket.send_json({

                    "type":
                        "error",

                    "message":
                        (
                            "ゲームは終了しています。"
                            "再戦または終了を"
                            "選択してください。"
                        )
                })


                continue


            # =====================================
            # RECONNECT WAITING
            # =====================================

            if (
                is_reconnect_waiting(
                    room
                )
            ):

                await websocket.send_json({

                    "type":
                        "error",

                    "message":
                        (
                            "相手が再接続中です。\n"
                            "少し待ってください。"
                        )
                })


                continue


            # =====================================
            # CPUはHuman = Player 1
            # =====================================

            if (
                room[
                    "mode"
                ]
                ==
                "cpu"

                and

                player_number
                !=
                1
            ):

                continue


            # =====================================
            # TURN CHECK
            # =====================================

            if (
                player_number
                !=
                room[
                    "current_turn"
                ]
            ):

                await websocket.send_json({

                    "type":
                        "error",

                    "message":
                        "今はあなたの"
                        "ターンではありません。"
                })


                continue


            # =====================================
            # QUESTION
            # =====================================

            if (
                message_type
                ==
                "question"
            ):

                await process_human_question(
                    websocket,
                    room,
                    player_number,
                    data
                )


                continue


            # =====================================
            # GUESS
            # =====================================

            if (
                message_type
                ==
                "guess_card"
            ):

                await process_human_guess(
                    websocket,
                    room,
                    player_number,
                    data
                )


                continue


            # =====================================
            # NEXT
            # =====================================

            if (
                message_type
                ==
                "continue_after_guess"
            ):

                if (
                    room[
                        "current_phase"
                    ]
                    !=
                    "result"
                ):

                    await websocket.send_json({

                        "type":
                            "error",

                        "message":
                            "今は「次へ」を"
                            "押すタイミングでは"
                            "ありません。"
                    })


                    continue


                # =============================
                # Current Player
                # =============================

                if (
                    player_number
                    ==
                    1
                ):

                    current_player = (
                        room[
                            "game"
                        ]
                        .player1
                    )

                else:

                    current_player = (
                        room[
                            "game"
                        ]
                        .player2
                    )


                # =============================
                # WIN CHECK
                # =============================

                if (
                    current_player
                    .is_winner()
                ):

                    await finish_game(
                        room,
                        player_number
                    )


                    continue


                # =============================
                # CPU TURN
                # =============================

                if (
                    room[
                        "mode"
                    ]
                    ==
                    "cpu"
                ):

                    room[
                        "current_turn"
                    ] = 2


                    room[
                        "current_phase"
                    ] = "question"


                    await send_turn_changed(
                        room
                    )


                    await cpu_turn(
                        room_id
                    )


                    continue


                # =============================
                # PvP TURN CHANGE
                # =============================

                if (
                    room[
                        "current_turn"
                    ]
                    ==
                    1
                ):

                    room[
                        "current_turn"
                    ] = 2

                else:

                    room[
                        "current_turn"
                    ] = 1


                room[
                    "current_phase"
                ] = "question"


                await send_turn_changed(
                    room
                )


                continue


            # =====================================
            # UNKNOWN
            # =====================================

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "不明な操作です。"
            })


    # =============================================
    # DISCONNECT
    # =============================================

    except WebSocketDisconnect:

        pass


    except Exception as error:

        print(
            f"ルーム {room_id}: "
            f"WebSocket error: "
            f"{error}"
        )


    finally:

        # leave_game / cancel などで
        # すでに削除済みなら何もしない
        if rooms.get(room_id) is room:

            if (
                websocket
                in room[
                    "players"
                ]
            ):

                index = (
                    room[
                        "players"
                    ]
                    .index(
                        websocket
                    )
                )


                player_number = (
                    index + 1
                )


                # =========================================
                # 対戦開始後
                #
                # → プレイヤー情報を残して
                #   再接続を30秒待つ
                # =========================================

                if (
                    room[
                        "game"
                    ]
                    is not None
                ):

                    player_name_for_reconnect = (
                        room[
                            "player_names"
                        ][
                            index
                        ]
                    )


                    user_id_for_reconnect = (
                        room[
                            "player_user_ids"
                        ][
                            index
                        ]
                    )


                    # Socketだけ切断状態にする
                    #
                    # 名前とuser_idは残す
                    room[
                        "players"
                    ][
                        index
                    ] = None


                    start_reconnect_wait(
                        room_id,
                        room,
                        player_number,
                        user_id_for_reconnect,
                        player_name_for_reconnect
                    )


                    # =========================================
                    # 相手に再接続待ちを通知
                    # =========================================

                    if (
                        room[
                            "mode"
                        ]
                        ==
                        "pvp"
                    ):

                        for other_socket in room[
                            "players"
                        ]:

                            if (
                                other_socket
                                is None
                            ):

                                continue


                            try:

                                await other_socket.send_json({

                                    "type":
                                        "opponent_reconnecting",

                                    "seconds":
                                        RECONNECT_GRACE_SECONDS
                                })

                            except Exception:

                                pass


                    print(
                        f"ルーム {room_id}: "
                        f"Player {player_number} "
                        "一時切断"
                    )


                # =========================================
                # 対戦開始前
                #
                # → 今まで通りルーム終了
                # =========================================

                else:

                    room[
                        "players"
                    ].pop(
                        index
                    )


                    if (
                        index
                        <
                        len(
                            room[
                                "player_names"
                            ]
                        )
                    ):

                        room[
                            "player_names"
                        ].pop(
                            index
                        )


                    if (
                        index
                        <
                        len(
                            room[
                                "player_user_ids"
                            ]
                        )
                    ):

                        room[
                            "player_user_ids"
                        ].pop(
                            index
                        )


                    await (
                        clear_waiting_room_if_needed(
                            room_id
                        )
                    )


                    rooms.pop(
                        room_id,
                        None
                    )


                    room[
                        "players"
                    ].clear()


                    room[
                        "player_names"
                    ].clear()


                    room[
                        "player_user_ids"
                    ].clear()


                    print(
                        f"ルーム {room_id}: "
                        "対戦開始前に切断されたため"
                        "ルームを削除しました"
                    )