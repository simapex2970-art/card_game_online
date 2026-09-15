import asyncio
import random
import secrets

from itertools import combinations
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from game import Game
from card import Card


# =============================================
# FastAPI
# =============================================

app = FastAPI()


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static"
)


# =============================================
# 静的ページ
# =============================================

@app.get("/")
async def root():

    return FileResponse(
        WEB_DIR / "index.html"
    )


@app.get(
    "/robots.txt",
    include_in_schema=False
)
async def robots():

    return FileResponse(
        WEB_DIR / "robots.txt"
    )


@app.get(
    "/sitemap.xml",
    include_in_schema=False
)
async def sitemap():

    return FileResponse(
        WEB_DIR / "sitemap.xml"
    )


# =============================================
# カード
# =============================================

SUITS = [
    "スペード",
    "ハート",
    "ダイヤ",
    "クラブ"
]


RANKS = [
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


# =============================================
# ルームID
# =============================================

ROOM_ID_CHARACTERS = (
    "ABCDEFGHJKLMNPQRSTUVWXYZ"
    "23456789"
)

ROOM_ID_LENGTH = 4


# =============================================
# ルーム
# =============================================

rooms = {}


def create_room(
    mode="pvp",
    cpu_level=None
):

    return {
        "players": [],

        "game": None,

        "current_turn": 1,

        "current_phase": "question",

        "rematch_requests": set(),

        "mode": mode,

        "cpu_level": cpu_level,

        # CPU Lv.2用
        "cpu_candidate_hands": [],

        "cpu_question_history": [],

        "cpu_wrong_guesses": set(),
    }


# =============================================
# ルームID生成
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


        if room_id not in rooms:

            return room_id


def is_valid_room_id(
    room_id
):

    if len(
        room_id
    ) != ROOM_ID_LENGTH:

        return False


    for char in room_id:

        if char not in ROOM_ID_CHARACTERS:

            return False


    return True


# =============================================
# PvPルーム作成
# =============================================

@app.post("/rooms")
async def create_pvp_room():

    room_id = generate_room_id()


    rooms[
        room_id
    ] = create_room(
        mode="pvp"
    )


    return {
        "room_id": room_id,

        "mode": "pvp"
    }


# =============================================
# CPUルーム作成
# =============================================

@app.post("/cpu-rooms")
async def create_cpu_room(
    level: int = 1
):

    if level not in [
        1,
        2
    ]:

        raise HTTPException(
            status_code=400,
            detail="CPUレベルは1または2を指定してください。"
        )


    room_id = generate_room_id()


    rooms[
        room_id
    ] = create_room(
        mode="cpu",
        cpu_level=level
    )


    return {
        "room_id": room_id,

        "mode": "cpu",

        "cpu_level": level
    }


# =============================================
# 全カード生成
# =============================================

def create_all_cards():

    cards = []


    for suit in SUITS:

        for rank in RANKS:

            cards.append(
                Card(
                    suit,
                    rank
                )
            )


    cards.append(
        Card(
            "JOKER"
        )
    )


    return cards


# =============================================
# CPU Lv.2
# 初期候補手札
# =============================================

def initialize_cpu_candidates(
    room
):

    game = room[
        "game"
    ]


    cpu_player = (
        game.player2
    )


    cpu_hand = set(
        cpu_player.hand
    )


    possible_cards = [
        card
        for card
        in create_all_cards()
        if card not in cpu_hand
    ]


    room[
        "cpu_candidate_hands"
    ] = [
        tuple(
            hand
        )
        for hand
        in combinations(
            possible_cards,
            3
        )
    ]


    room[
        "cpu_question_history"
    ] = []


    room[
        "cpu_wrong_guesses"
    ] = set()


# =============================================
# CPU状態初期化
# =============================================

def initialize_cpu_state(
    room
):

    room[
        "cpu_candidate_hands"
    ] = []


    room[
        "cpu_question_history"
    ] = []


    room[
        "cpu_wrong_guesses"
    ] = set()


    if room[
        "cpu_level"
    ] == 2:

        initialize_cpu_candidates(
            room
        )


# =============================================
# 質問評価
# =============================================

def evaluate_question_on_hand(
    question_manager,
    hand,
    found_cards,
    question_id,
    rank=None,
    number=None
):

    if question_id == 1:

        return question_manager.ask_even(
            hand,
            found_cards
        )


    if question_id == 2:

        return question_manager.ask_odd(
            hand,
            found_cards
        )


    if question_id == 3:

        return question_manager.ask_face(
            hand,
            found_cards
        )


    if question_id == 4:

        return question_manager.ask_rank(
            hand,
            found_cards,
            rank
        )


    if question_id == 5:

        return question_manager.ask_more_than(
            hand,
            found_cards,
            number
        )


    if question_id == 6:

        return question_manager.ask_less_than(
            hand,
            found_cards,
            number
        )


    if question_id == 7:

        return question_manager.ask_suit(
            hand,
            found_cards,
            "スペード"
        )


    if question_id == 8:

        return question_manager.ask_suit(
            hand,
            found_cards,
            "ハート"
        )


    if question_id == 9:

        return question_manager.ask_suit(
            hand,
            found_cards,
            "ダイヤ"
        )


    if question_id == 10:

        return question_manager.ask_suit(
            hand,
            found_cards,
            "クラブ"
        )


    if question_id == 11:

        return question_manager.ask_joker(
            hand,
            found_cards
        )


    raise ValueError(
        "質問IDが正しくありません。"
    )


# =============================================
# 質問文章
# =============================================

def create_question_text(
    question_id,
    rank=None,
    number=None
):

    if question_id == 1:

        return "偶数のカードはありますか？"


    if question_id == 2:

        return "奇数のカードはありますか？"


    if question_id == 3:

        return "絵札はありますか？"


    if question_id == 4:

        return (
            f"{rank} はありますか？"
        )


    if question_id == 5:

        return (
            f"{number}以上のカードはありますか？"
        )


    if question_id == 6:

        return (
            f"{number}以下のカードはありますか？"
        )


    if question_id == 7:

        return "スペードはありますか？"


    if question_id == 8:

        return "ハートはありますか？"


    if question_id == 9:

        return "ダイヤはありますか？"


    if question_id == 10:

        return "クラブはありますか？"


    if question_id == 11:

        return "JOKERはありますか？"


    return "不明な質問"


# =============================================
# 人間の質問
# =============================================

def evaluate_question(
    game,
    asking_player,
    opponent,
    data
):

    question_id = data.get(
        "question_id"
    )


    rank = None
    number = None


    if question_id not in range(
        1,
        12
    ):

        raise ValueError(
            "質問IDが正しくありません。"
        )


    if question_id == 4:

        rank = str(
            data.get(
                "rank",
                ""
            )
        ).upper()


        if rank not in RANKS:

            raise ValueError(
                "ランクが正しくありません。"
            )


    if question_id in [
        5,
        6
    ]:

        number = data.get(
            "number"
        )


        if not isinstance(
            number,
            int
        ):

            raise ValueError(
                "数字が正しくありません。"
            )


        if (
            number < 1
            or
            number > 13
        ):

            raise ValueError(
                "数字は1〜13で指定してください。"
            )


    answer = evaluate_question_on_hand(
        game.question_manager,
        opponent.hand,
        asking_player.found_cards,
        question_id,
        rank,
        number
    )


    question_text = create_question_text(
        question_id,
        rank,
        number
    )


    return (
        answer,
        question_text
    )


# =============================================
# 予想カード生成
# =============================================

def create_guess_card(
    data
):

    suit = data.get(
        "suit"
    )


    if suit == "JOKER":

        return Card(
            "JOKER"
        )


    if suit not in SUITS:

        return None


    rank = str(
        data.get(
            "rank",
            ""
        )
    ).upper()


    if rank not in RANKS:

        return None


    return Card(
        suit,
        rank
    )


# =============================================
# CPU質問一覧
# =============================================

def create_cpu_question_pool():

    questions = []


    # 偶数 / 奇数 / 絵札 / スート / JOKER
    for question_id in [
        1,
        2,
        3,
        7,
        8,
        9,
        10,
        11
    ]:

        questions.append({
            "question_id":
                question_id
        })


    # ランク
    for rank in RANKS:

        questions.append({
            "question_id":
                4,

            "rank":
                rank
        })


    # 以上
    for number in range(
        1,
        14
    ):

        questions.append({
            "question_id":
                5,

            "number":
                number
        })


    # 以下
    for number in range(
        1,
        14
    ):

        questions.append({
            "question_id":
                6,

            "number":
                number
        })


    return questions


# =============================================
# CPU質問キー
# =============================================

def cpu_question_key(
    question
):

    return (
        question.get(
            "question_id"
        ),

        question.get(
            "rank"
        ),

        question.get(
            "number"
        )
    )


# =============================================
# CPU質問選択
# =============================================

def choose_cpu_question(
    room
):

    pool = (
        create_cpu_question_pool()
    )


    # =========================================
    # Lv.1
    # 完全ランダム
    # =========================================

    if room[
        "cpu_level"
    ] == 1:

        return random.choice(
            pool
        )


    # =========================================
    # Lv.2
    # 一度使った質問はなるべく避ける
    # =========================================

    used_keys = {
        cpu_question_key(
            item
        )
        for item
        in room[
            "cpu_question_history"
        ]
    }


    unused_questions = [
        question
        for question
        in pool
        if cpu_question_key(
            question
        )
        not in used_keys
    ]


    if unused_questions:

        return random.choice(
            unused_questions
        )


    return random.choice(
        pool
    )


# =============================================
# Lv.2
# 質問結果から候補を絞る
# =============================================

def filter_cpu_candidates_by_question(
    room,
    question,
    answer
):

    if room[
        "cpu_level"
    ] != 2:

        return


    game = room[
        "game"
    ]


    cpu_player = (
        game.player2
    )


    question_id = question[
        "question_id"
    ]


    rank = question.get(
        "rank"
    )


    number = question.get(
        "number"
    )


    filtered = []


    for candidate_hand in room[
        "cpu_candidate_hands"
    ]:

        candidate_answer = (
            evaluate_question_on_hand(
                game.question_manager,
                list(
                    candidate_hand
                ),
                cpu_player.found_cards,
                question_id,
                rank,
                number
            )
        )


        if candidate_answer == answer:

            filtered.append(
                candidate_hand
            )


    room[
        "cpu_candidate_hands"
    ] = filtered


# =============================================
# Lv.2
# 予想結果から候補を絞る
# =============================================

def filter_cpu_candidates_by_guess(
    room,
    guess,
    correct
):

    if room[
        "cpu_level"
    ] != 2:

        return


    current_candidates = room[
        "cpu_candidate_hands"
    ]


    if correct:

        room[
            "cpu_candidate_hands"
        ] = [
            hand
            for hand
            in current_candidates
            if guess in hand
        ]


    else:

        room[
            "cpu_candidate_hands"
        ] = [
            hand
            for hand
            in current_candidates
            if guess not in hand
        ]


        room[
            "cpu_wrong_guesses"
        ].add(
            guess
        )


# =============================================
# Lv.1
# ランダム予想
# =============================================

def choose_cpu_level1_guess(
    room
):

    game = room[
        "game"
    ]


    cpu_player = (
        game.player2
    )


    cpu_hand = set(
        cpu_player.hand
    )


    found_cards = set(
        cpu_player.found_cards
    )


    candidates = [
        card
        for card
        in create_all_cards()
        if (
            card not in cpu_hand
            and
            card not in found_cards
        )
    ]


    if not candidates:

        return None


    return random.choice(
        candidates
    )


# =============================================
# Lv.2
# 推理予想
# =============================================

def choose_cpu_level2_guess(
    room
):

    game = room[
        "game"
    ]


    cpu_player = (
        game.player2
    )


    found_cards = set(
        cpu_player.found_cards
    )


    wrong_guesses = room[
        "cpu_wrong_guesses"
    ]


    counts = {}


    # =========================================
    # 残っている候補手札に
    # 何回カードが登場するか数える
    # =========================================

    for candidate_hand in room[
        "cpu_candidate_hands"
    ]:

        for card in candidate_hand:

            if card in found_cards:

                continue


            if card in wrong_guesses:

                continue


            counts[
                card
            ] = (
                counts.get(
                    card,
                    0
                )
                + 1
            )


    if counts:

        max_count = max(
            counts.values()
        )


        best_cards = [
            card
            for card, count
            in counts.items()
            if count == max_count
        ]


        return random.choice(
            best_cards
        )


    # =========================================
    # 候補が万が一0になった場合の保険
    # =========================================

    cpu_hand = set(
        cpu_player.hand
    )


    fallback = [
        card
        for card
        in create_all_cards()
        if (
            card not in cpu_hand
            and
            card not in found_cards
            and
            card not in wrong_guesses
        )
    ]


    if not fallback:

        return None


    return random.choice(
        fallback
    )


# =============================================
# CPU予想選択
# =============================================

def choose_cpu_guess(
    room
):

    if room[
        "cpu_level"
    ] == 1:

        return choose_cpu_level1_guess(
            room
        )


    return choose_cpu_level2_guess(
        room
    )


# =============================================
# CPU質問実行
# =============================================

def cpu_ask_question(
    room
):

    game = room[
        "game"
    ]


    human_player = (
        game.player1
    )


    cpu_player = (
        game.player2
    )


    question = choose_cpu_question(
        room
    )


    question_id = question[
        "question_id"
    ]


    rank = question.get(
        "rank"
    )


    number = question.get(
        "number"
    )


    # =========================================
    # 実際のプレイヤー手札へ質問
    # =========================================

    answer = evaluate_question_on_hand(
        game.question_manager,
        human_player.hand,
        cpu_player.found_cards,
        question_id,
        rank,
        number
    )


    question_text = create_question_text(
        question_id,
        rank,
        number
    )


    # =========================================
    # Lv.2だけ履歴を利用
    # =========================================

    if room[
        "cpu_level"
    ] == 2:

        history = {
            "question_id":
                question_id,

            "rank":
                rank,

            "number":
                number,

            "question":
                question_text,

            "answer":
                answer
        }


        room[
            "cpu_question_history"
        ].append(
            history
        )


        filter_cpu_candidates_by_question(
            room,
            question,
            answer
        )


        candidate_count = len(
            room[
                "cpu_candidate_hands"
            ]
        )


    else:

        candidate_count = None


    return {
        "question":
            question_text,

        "answer":
            answer,

        "candidate_count":
            candidate_count
    }


# =============================================
# 安全送信
# =============================================

async def send_json_safe(
    websocket,
    data
):

    try:

        await websocket.send_json(
            data
        )

        return True


    except Exception:

        return False


# =============================================
# GAME OVER
# =============================================

async def finish_game(
    room,
    winner
):

    game = room[
        "game"
    ]


    room[
        "current_phase"
    ] = "finished"


    message = {
        "type":
            "game_over",

        "winner":
            winner,

        "player1_hand": [
            str(
                card
            )
            for card
            in game.player1.hand
        ],

        "player2_hand": [
            str(
                card
            )
            for card
            in game.player2.hand
        ]
    }


    for websocket in list(
        room[
            "players"
        ]
    ):

        await send_json_safe(
            websocket,
            message
        )


# =============================================
# ターン変更通知
# =============================================

async def send_turn_changed(
    room
):

    current_turn = room[
        "current_turn"
    ]


    phase = room[
        "current_phase"
    ]


    # =========================================
    # CPU戦
    # =========================================

    if room[
        "mode"
    ] == "cpu":

        if not room[
            "players"
        ]:

            return


        await send_json_safe(
            room[
                "players"
            ][0],

            {
                "type":
                    "turn_changed",

                "current_turn":
                    current_turn,

                "your_turn":
                    current_turn == 1,

                "phase":
                    phase,

                "mode":
                    "cpu",

                "cpu_level":
                    room[
                        "cpu_level"
                    ]
            }
        )


        return


    # =========================================
    # PvP
    # =========================================

    for index, websocket in enumerate(
        list(
            room[
                "players"
            ]
        ),
        start=1
    ):

        await send_json_safe(
            websocket,
            {
                "type":
                    "turn_changed",

                "current_turn":
                    current_turn,

                "your_turn":
                    current_turn == index,

                "phase":
                    phase,

                "mode":
                    "pvp"
            }
        )


# =============================================
# 新しいゲーム
# =============================================

async def start_new_game(
    room_id
):

    if room_id not in rooms:

        return


    room = rooms[
        room_id
    ]


    room[
        "game"
    ] = Game()


    room[
        "current_turn"
    ] = 1


    room[
        "current_phase"
    ] = "question"


    room[
        "rematch_requests"
    ] = set()


    game = room[
        "game"
    ]


    # =========================================
    # CPU戦
    # =========================================

    if room[
        "mode"
    ] == "cpu":

        initialize_cpu_state(
            room
        )


        if not room[
            "players"
        ]:

            return


        websocket = room[
            "players"
        ][0]


        candidate_count = None


        if room[
            "cpu_level"
        ] == 2:

            candidate_count = len(
                room[
                    "cpu_candidate_hands"
                ]
            )


        await send_json_safe(
            websocket,
            {
                "type":
                    "game_start",

                "player":
                    1,

                "hand": [
                    str(
                        card
                    )
                    for card
                    in game.player1.hand
                ],

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
                    candidate_count
            }
        )


        return


    # =========================================
    # PvP
    # =========================================

    if len(
        room[
            "players"
        ]
    ) < 2:

        return


    player1_socket = room[
        "players"
    ][0]


    player2_socket = room[
        "players"
    ][1]


    await send_json_safe(
        player1_socket,
        {
            "type":
                "game_start",

            "player":
                1,

            "hand": [
                str(
                    card
                )
                for card
                in game.player1.hand
            ],

            "your_turn":
                True,

            "phase":
                "question",

            "mode":
                "pvp"
        }
    )


    await send_json_safe(
        player2_socket,
        {
            "type":
                "game_start",

            "player":
                2,

            "hand": [
                str(
                    card
                )
                for card
                in game.player2.hand
            ],

            "your_turn":
                False,

            "phase":
                "question",

            "mode":
                "pvp"
        }
    )


# =============================================
# CPUターン
# =============================================

async def cpu_take_turn(
    room_id
):

    if room_id not in rooms:

        return


    room = rooms[
        room_id
    ]


    if room[
        "mode"
    ] != "cpu":

        return


    if not room[
        "players"
    ]:

        return


    game = room[
        "game"
    ]


    if game is None:

        return


    if room[
        "current_turn"
    ] != 2:

        return


    cpu_level = room[
        "cpu_level"
    ]


    # =========================================
    # CPU思考
    # =========================================

    await asyncio.sleep(
        1.0
    )


    if room_id not in rooms:

        return


    # =========================================
    # CPU質問
    # =========================================

    question_result = (
        cpu_ask_question(
            room
        )
    )


    if not room[
        "players"
    ]:

        return


    await send_json_safe(
        room[
            "players"
        ][0],

        {
            "type":
                "cpu_question",

            "question":
                question_result[
                    "question"
                ],

            "answer":
                question_result[
                    "answer"
                ],

            "candidate_count":
                question_result[
                    "candidate_count"
                ],

            "cpu_level":
                cpu_level
        }
    )


    await asyncio.sleep(
        1.5
    )


    if room_id not in rooms:

        return


    # =========================================
    # CPU予想
    # =========================================

    guess = choose_cpu_guess(
        room
    )


    if guess is None:

        return


    correct = game.guess_card(
        game.player2,
        game.player1,
        guess
    )


    # =========================================
    # Lv.2だけ結果を記憶
    # =========================================

    if cpu_level == 2:

        filter_cpu_candidates_by_guess(
            room,
            guess,
            correct
        )


        candidate_count = len(
            room[
                "cpu_candidate_hands"
            ]
        )


    else:

        candidate_count = None


    await send_json_safe(
        room[
            "players"
        ][0],

        {
            "type":
                "cpu_guess_result",

            "guess":
                str(
                    guess
                ),

            "correct":
                correct,

            "found_count":
                len(
                    game.player2.found_cards
                ),

            "candidate_count":
                candidate_count,

            "cpu_level":
                cpu_level
        }
    )


    await asyncio.sleep(
        1.5
    )


    if room_id not in rooms:

        return


    # =========================================
    # CPU勝利
    # =========================================

    if game.player2.is_winner():

        await finish_game(
            room,
            2
        )

        return


    # =========================================
    # 人間ターン
    # =========================================

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
# WebSocket
# =============================================

@app.websocket(
    "/ws/{room_id}"
)
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str
):

    room_id = (
        room_id
        .strip()
        .upper()
    )


    await websocket.accept()


    # =========================================
    # ID形式
    # =========================================

    if not is_valid_room_id(
        room_id
    ):

        await websocket.send_json({
            "type":
                "error",

            "code":
                "INVALID_ROOM_ID",

            "message":
                "ルームIDの形式が正しくありません。"
        })


        await websocket.close()

        return


    # =========================================
    # 存在しない
    # =========================================

    if room_id not in rooms:

        await websocket.send_json({
            "type":
                "error",

            "code":
                "ROOM_NOT_FOUND",

            "message":
                "ルームが見つかりません。"
        })


        await websocket.close()

        return


    room = rooms[
        room_id
    ]


    # =========================================
    # 満員
    # =========================================

    if (
        room[
            "mode"
        ] == "pvp"
        and
        len(
            room[
                "players"
            ]
        ) >= 2
    ):

        await websocket.send_json({
            "type":
                "error",

            "code":
                "ROOM_FULL",

            "message":
                "ルームは満員です。"
        })


        await websocket.close()

        return


    if (
        room[
            "mode"
        ] == "cpu"
        and
        len(
            room[
                "players"
            ]
        ) >= 1
    ):

        await websocket.send_json({
            "type":
                "error",

            "code":
                "ROOM_FULL",

            "message":
                "CPUルームは使用中です。"
        })


        await websocket.close()

        return


    # =========================================
    # プレイヤー追加
    # =========================================

    room[
        "players"
    ].append(
        websocket
    )


    if room[
        "mode"
    ] == "cpu":

        player_number = 1


    else:

        player_number = len(
            room[
                "players"
            ]
        )


    await websocket.send_json({
        "type":
            "player_number",

        "player":
            player_number,

        "room_id":
            room_id,

        "mode":
            room[
                "mode"
            ],

        "cpu_level":
            room[
                "cpu_level"
            ]
    })


    # =========================================
    # 開始
    # =========================================

    if room[
        "mode"
    ] == "cpu":

        await start_new_game(
            room_id
        )


    elif len(
        room[
            "players"
        ]
    ) == 2:

        await start_new_game(
            room_id
        )


    try:

        while True:

            data = (
                await websocket.receive_json()
            )


            if room_id not in rooms:

                break


            room = rooms[
                room_id
            ]


            game = room[
                "game"
            ]


            # =================================
            # 質問
            # =================================

            if data.get(
                "type"
            ) == "question":

                if game is None:

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "ゲームが開始していません。"
                    })

                    continue


                if room[
                    "current_turn"
                ] != player_number:

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "あなたのターンではありません。"
                    })

                    continue


                if room[
                    "current_phase"
                ] != "question":

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "今は質問できません。"
                    })

                    continue


                if player_number == 1:

                    asking_player = (
                        game.player1
                    )

                    opponent = (
                        game.player2
                    )


                else:

                    asking_player = (
                        game.player2
                    )

                    opponent = (
                        game.player1
                    )


                try:

                    (
                        answer,
                        question_text
                    ) = evaluate_question(
                        game,
                        asking_player,
                        opponent,
                        data
                    )


                except ValueError as error:

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            str(
                                error
                            )
                    })

                    continue


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


                continue


            # =================================
            # 予想
            # =================================

            if data.get(
                "type"
            ) == "guess_card":

                if game is None:

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "ゲームが開始していません。"
                    })

                    continue


                if room[
                    "current_turn"
                ] != player_number:

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "あなたのターンではありません。"
                    })

                    continue


                if room[
                    "current_phase"
                ] != "guess":

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "今は予想できません。"
                    })

                    continue


                guess = create_guess_card(
                    data
                )


                if guess is None:

                    await websocket.send_json({
                        "type":
                            "error",

                        "message":
                            "カード指定が正しくありません。"
                    })

                    continue


                if player_number == 1:

                    asking_player = (
                        game.player1
                    )

                    opponent = (
                        game.player2
                    )


                else:

                    asking_player = (
                        game.player2
                    )

                    opponent = (
                        game.player1
                    )


                correct = game.guess_card(
                    asking_player,
                    opponent,
                    guess
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
                            asking_player.found_cards
                        )
                })


                continue


            # =================================
            # 次へ
            # =================================

            if data.get(
                "type"
            ) == "continue_after_guess":

                if game is None:

                    continue


                if room[
                    "current_turn"
                ] != player_number:

                    continue


                if room[
                    "current_phase"
                ] != "result":

                    continue


                if player_number == 1:

                    current_player = (
                        game.player1
                    )


                else:

                    current_player = (
                        game.player2
                    )


                # =============================
                # 勝利
                # =============================

                if current_player.is_winner():

                    await finish_game(
                        room,
                        player_number
                    )

                    continue


                # =============================
                # CPU戦
                # =============================

                if room[
                    "mode"
                ] == "cpu":

                    room[
                        "current_turn"
                    ] = 2


                    room[
                        "current_phase"
                    ] = "question"


                    await send_turn_changed(
                        room
                    )


                    await cpu_take_turn(
                        room_id
                    )


                    continue


                # =============================
                # PvP
                # =============================

                room[
                    "current_turn"
                ] = (
                    2
                    if player_number == 1
                    else 1
                )


                room[
                    "current_phase"
                ] = "question"


                await send_turn_changed(
                    room
                )


                continue


            # =================================
            # 再戦
            # =================================

            if data.get(
                "type"
            ) == "rematch_request":

                # CPUは即再戦
                if room[
                    "mode"
                ] == "cpu":

                    await start_new_game(
                        room_id
                    )

                    continue


                room[
                    "rematch_requests"
                ].add(
                    player_number
                )


                if len(
                    room[
                        "rematch_requests"
                    ]
                ) >= 2:

                    await start_new_game(
                        room_id
                    )


                else:

                    await websocket.send_json({
                        "type":
                            "rematch_waiting"
                    })


                continue


            # =================================
            # 終了
            # =================================

            if data.get(
                "type"
            ) == "leave_game":

                if room[
                    "mode"
                ] == "pvp":

                    for other_socket in list(
                        room[
                            "players"
                        ]
                    ):

                        if other_socket is websocket:

                            continue


                        await send_json_safe(
                            other_socket,
                            {
                                "type":
                                    "opponent_left"
                            }
                        )


                if room_id in rooms:

                    del rooms[
                        room_id
                    ]


                try:

                    await websocket.close()


                except Exception:

                    pass


                break


            # =================================
            # 不明
            # =================================

            await websocket.send_json({
                "type":
                    "error",

                "message":
                    "不明なメッセージです。"
            })


    except WebSocketDisconnect:

        pass


    except Exception as error:

        print(
            "WebSocket error:",
            error
        )


    finally:

        if room_id not in rooms:

            return


        room = rooms[
            room_id
        ]


        if websocket in room[
            "players"
        ]:

            room[
                "players"
            ].remove(
                websocket
            )


        # =====================================
        # CPU
        # =====================================

        if room[
            "mode"
        ] == "cpu":

            if room_id in rooms:

                del rooms[
                    room_id
                ]


            return


        # =====================================
        # PvP
        # =====================================

        for other_socket in list(
            room[
                "players"
            ]
        ):

            await send_json_safe(
                other_socket,
                {
                    "type":
                        "opponent_disconnected"
                }
            )


            try:

                await other_socket.close()


            except Exception:

                pass


        if room_id in rooms:

            del rooms[
                room_id
            ]