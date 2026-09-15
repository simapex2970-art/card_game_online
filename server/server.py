import asyncio
import random
import secrets
from pathlib import Path

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from game import Game
from card import Card


# =============================================
# FastAPI
# =============================================

app = FastAPI()


# =============================================
# Webファイル
# =============================================

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static",
)


@app.get("/")
async def web_index():

    return FileResponse(
        WEB_DIR / "index.html"
    )


@app.get(
    "/robots.txt",
    include_in_schema=False,
)
async def robots_txt():

    return FileResponse(
        WEB_DIR / "robots.txt",
        media_type="text/plain",
    )


@app.get(
    "/sitemap.xml",
    include_in_schema=False,
)
async def sitemap_xml():

    return FileResponse(
        WEB_DIR / "sitemap.xml",
        media_type="application/xml",
    )


# =============================================
# 定数
# =============================================

ROOM_ID_CHARACTERS = (
    "ABCDEFGHJKLMNPQRSTUVWXYZ"
    "23456789"
)

ROOM_ID_LENGTH = 4


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
    "K",
]


VALID_SUITS = [
    "スペード",
    "ハート",
    "ダイヤ",
    "クラブ",
]


# =============================================
# ルーム
# =============================================

rooms = {}


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
    room_id,
):

    if len(room_id) != ROOM_ID_LENGTH:

        return False

    for character in room_id:

        if character not in ROOM_ID_CHARACTERS:

            return False

    return True


def create_room(
    mode="pvp",
):

    return {
        "players": [],
        "game": None,
        "current_turn": 1,
        "current_phase": "question",
        "rematch_requests": set(),
        "mode": mode,
    }


# =============================================
# 対人ルーム作成
# =============================================

@app.post("/rooms")
async def create_room_endpoint():

    room_id = generate_room_id()

    rooms[room_id] = create_room(
        mode="pvp"
    )

    print(
        f"ルーム {room_id} "
        "を作成しました"
    )

    return {
        "room_id": room_id
    }


# =============================================
# CPUルーム作成
# =============================================

@app.post("/cpu-rooms")
async def create_cpu_room_endpoint():

    room_id = generate_room_id()

    rooms[room_id] = create_room(
        mode="cpu"
    )

    print(
        f"CPU対戦ルーム {room_id} "
        "を作成しました"
    )

    return {
        "room_id": room_id
    }


# =============================================
# 質問処理
# =============================================

def evaluate_question(
    game,
    asking_player,
    opponent,
    data,
):

    question_id = data.get(
        "question_id"
    )


    # =========================================
    # 1 偶数
    # =========================================

    if question_id == 1:

        question_text = (
            "偶数はある？"
        )

        answer = (
            game.question_manager.ask_even(
                opponent.hand,
                asking_player.found_cards,
            )
        )


    # =========================================
    # 2 奇数
    # =========================================

    elif question_id == 2:

        question_text = (
            "奇数はある？"
        )

        answer = (
            game.question_manager.ask_odd(
                opponent.hand,
                asking_player.found_cards,
            )
        )


    # =========================================
    # 3 絵札
    # =========================================

    elif question_id == 3:

        question_text = (
            "絵札はある？"
        )

        answer = (
            game.question_manager.ask_face(
                opponent.hand,
                asking_player.found_cards,
            )
        )


    # =========================================
    # 4 ランク
    # =========================================

    elif question_id == 4:

        rank = data.get(
            "rank"
        )

        if rank not in VALID_RANKS:

            raise ValueError(
                "指定したランクが"
                "正しくありません。"
            )

        question_text = (
            f"{rank} はある？"
        )

        answer = (
            game.question_manager.ask_rank(
                opponent.hand,
                asking_player.found_cards,
                rank,
            )
        )


    # =========================================
    # 5 以上
    # =========================================

    elif question_id == 5:

        number = data.get(
            "number"
        )

        if (
            not isinstance(
                number,
                int,
            )
            or number < 1
            or number > 13
        ):

            raise ValueError(
                "数字は1～13で"
                "指定してください。"
            )

        question_text = (
            f"{number} 以上の"
            "カードはある？"
        )

        answer = (
            game.question_manager.ask_more_than(
                opponent.hand,
                asking_player.found_cards,
                number,
            )
        )


    # =========================================
    # 6 以下
    # =========================================

    elif question_id == 6:

        number = data.get(
            "number"
        )

        if (
            not isinstance(
                number,
                int,
            )
            or number < 1
            or number > 13
        ):

            raise ValueError(
                "数字は1～13で"
                "指定してください。"
            )

        question_text = (
            f"{number} 以下の"
            "カードはある？"
        )

        answer = (
            game.question_manager.ask_less_than(
                opponent.hand,
                asking_player.found_cards,
                number,
            )
        )


    # =========================================
    # 7 スペード
    # =========================================

    elif question_id == 7:

        question_text = (
            "スペードはある？"
        )

        answer = (
            game.question_manager.ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "スペード",
            )
        )


    # =========================================
    # 8 ハート
    # =========================================

    elif question_id == 8:

        question_text = (
            "ハートはある？"
        )

        answer = (
            game.question_manager.ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "ハート",
            )
        )


    # =========================================
    # 9 ダイヤ
    # =========================================

    elif question_id == 9:

        question_text = (
            "ダイヤはある？"
        )

        answer = (
            game.question_manager.ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "ダイヤ",
            )
        )


    # =========================================
    # 10 クラブ
    # =========================================

    elif question_id == 10:

        question_text = (
            "クラブはある？"
        )

        answer = (
            game.question_manager.ask_suit(
                opponent.hand,
                asking_player.found_cards,
                "クラブ",
            )
        )


    # =========================================
    # 11 JOKER
    # =========================================

    elif question_id == 11:

        question_text = (
            "JOKERはある？"
        )

        answer = (
            game.question_manager.ask_joker(
                opponent.hand,
                asking_player.found_cards,
            )
        )


    # =========================================
    # 不正
    # =========================================

    else:

        raise ValueError(
            "質問番号が"
            "正しくありません。"
        )


    return (
        question_text,
        answer,
    )


# =============================================
# 予想カード作成
# =============================================

def create_guess_card(
    data,
):

    suit = data.get(
        "suit"
    )

    rank = data.get(
        "rank"
    )


    # JOKER

    if suit == "JOKER":

        return Card(
            "JOKER"
        )


    # 通常カード

    if suit not in VALID_SUITS:

        raise ValueError(
            "スートが"
            "正しくありません。"
        )


    if rank not in VALID_RANKS:

        raise ValueError(
            "ランクが"
            "正しくありません。"
        )


    return Card(
        suit,
        rank,
    )


# =============================================
# CPU用予想候補
# =============================================

def create_cpu_guess_candidates(
    cpu_player,
):

    cards = []


    # 通常52枚

    for suit in VALID_SUITS:

        for rank in VALID_RANKS:

            card = Card(
                suit,
                rank,
            )


            # CPU自身の手札は
            # 人間の手札には存在しない
            if card in cpu_player.hand:

                continue


            # すでに当てたカードも除外
            if card in cpu_player.found_cards:

                continue


            cards.append(
                card
            )


    # JOKER

    joker = Card(
        "JOKER"
    )


    if (
        joker not in cpu_player.hand
        and
        joker not in cpu_player.found_cards
    ):

        cards.append(
            joker
        )


    return cards


# =============================================
# CPUランダム質問
# =============================================

def cpu_random_question(
    room,
):

    game = room["game"]

    cpu_player = (
        game.player2
    )

    human_player = (
        game.player1
    )


    question_id = random.randint(
        1,
        11,
    )


    data = {
        "question_id": question_id
    }


    # ランク指定質問

    if question_id == 4:

        data["rank"] = (
            random.choice(
                VALID_RANKS
            )
        )


    # 以上 / 以下

    elif question_id in (
        5,
        6,
    ):

        data["number"] = (
            random.randint(
                1,
                13,
            )
        )


    return evaluate_question(
        game,
        cpu_player,
        human_player,
        data,
    )


# =============================================
# ゲーム終了
# =============================================

async def finish_game(
    room,
    winner,
):

    game = room["game"]


    player1_hand = [
        str(card)
        for card
        in game.player1.hand
    ]


    player2_hand = [
        str(card)
        for card
        in game.player2.hand
    ]


    room[
        "current_phase"
    ] = "finished"


    room[
        "rematch_requests"
    ].clear()


    for player_socket in list(
        room["players"]
    ):

        try:

            await player_socket.send_json({
                "type": "game_over",
                "winner": winner,
                "player1_hand": player1_hand,
                "player2_hand": player2_hand,
            })

        except Exception:

            pass


# =============================================
# 新しいゲーム
# =============================================

async def start_new_game(
    room_id,
):

    room = rooms.get(
        room_id
    )


    if room is None:

        raise ValueError(
            f"ルーム {room_id} が"
            "存在しません。"
        )


    # =========================================
    # 人数確認
    # =========================================

    if room["mode"] == "cpu":

        if len(
            room["players"]
        ) != 1:

            raise ValueError(
                "CPU対戦には"
                "Player 1が必要です。"
            )


    else:

        if len(
            room["players"]
        ) != 2:

            raise ValueError(
                f"ルーム {room_id} に"
                "2人揃っていません。"
            )


    # =========================================
    # ゲーム初期化
    # =========================================

    room["game"] = Game()

    room["current_turn"] = 1

    room[
        "current_phase"
    ] = "question"

    room[
        "rematch_requests"
    ].clear()


    player1_hand = [
        str(card)
        for card
        in room["game"].player1.hand
    ]


    player2_hand = [
        str(card)
        for card
        in room["game"].player2.hand
    ]


    # =========================================
    # Player 1
    # =========================================

    await room["players"][0].send_json({
        "type": "game_start",
        "player": 1,
        "hand": player1_hand,
        "your_turn": True,
        "phase": "question",
        "mode": room["mode"],
    })


    # =========================================
    # Player 2
    # 対人戦だけ送信
    # =========================================

    if room["mode"] == "pvp":

        await room["players"][1].send_json({
            "type": "game_start",
            "player": 2,
            "hand": player2_hand,
            "your_turn": False,
            "phase": "waiting",
            "mode": "pvp",
        })


    print(
        f"ルーム {room_id}: "
        "新しいゲームを開始しました"
    )

    print(
        f"ルーム {room_id}: "
        "Player 1 のターンです"
    )


# =============================================
# ターン情報送信
# =============================================

async def send_turn_changed(
    room,
):

    current_turn = (
        room["current_turn"]
    )


    # =========================================
    # CPU戦
    # =========================================

    if room["mode"] == "cpu":

        if not room["players"]:

            return


        await room["players"][0].send_json({
            "type": "turn_changed",
            "current_turn": current_turn,
            "your_turn": (
                current_turn == 1
            ),
            "phase": (
                "question"
                if current_turn == 1
                else "waiting"
            ),
        })

        return


    # =========================================
    # 対人戦
    # =========================================

    if len(
        room["players"]
    ) < 2:

        return


    await room["players"][0].send_json({
        "type": "turn_changed",
        "current_turn": current_turn,
        "your_turn": (
            current_turn == 1
        ),
        "phase": (
            "question"
            if current_turn == 1
            else "waiting"
        ),
    })


    await room["players"][1].send_json({
        "type": "turn_changed",
        "current_turn": current_turn,
        "your_turn": (
            current_turn == 2
        ),
        "phase": (
            "question"
            if current_turn == 2
            else "waiting"
        ),
    })


# =============================================
# CPUターン
# =============================================

async def cpu_take_turn(
    room_id,
):

    room = rooms.get(
        room_id
    )


    if room is None:

        return


    if room["mode"] != "cpu":

        return


    if room["game"] is None:

        return


    if room["current_turn"] != 2:

        return


    if not room["players"]:

        return


    human_socket = (
        room["players"][0]
    )

    game = room["game"]

    cpu_player = (
        game.player2
    )

    human_player = (
        game.player1
    )


    # =========================================
    # CPUが考えているように少し待つ
    # =========================================

    await asyncio.sleep(
        1.0
    )


    # 待っている間に
    # ルームが消えていないか確認

    if rooms.get(
        room_id
    ) is not room:

        return


    # =========================================
    # CPU質問
    # =========================================

    room[
        "current_phase"
    ] = "question"


    (
        question_text,
        answer,
    ) = cpu_random_question(
        room
    )


    print(
        f"ルーム {room_id}: "
        f"CPU質問 "
        f"{question_text} "
        f"→ {answer}"
    )


    try:

        await human_socket.send_json({
            "type": "cpu_question",
            "question": question_text,
            "answer": answer,
        })

    except Exception:

        return


    # =========================================
    # CPU予想まで少し待つ
    # =========================================

    room[
        "current_phase"
    ] = "guess"


    await asyncio.sleep(
        1.5
    )


    if rooms.get(
        room_id
    ) is not room:

        return


    # =========================================
    # CPUランダム予想
    # =========================================

    candidates = (
        create_cpu_guess_candidates(
            cpu_player
        )
    )


    if not candidates:

        return


    guess = random.choice(
        candidates
    )


    result = (
        game.guess_card(
            cpu_player,
            human_player,
            guess,
        )
    )


    found_count = len(
        cpu_player.found_cards
    )


    print(
        f"ルーム {room_id}: "
        f"CPU予想 "
        f"{guess} "
        f"→ {result}"
    )


    try:

        await human_socket.send_json({
            "type": "cpu_guess_result",
            "guess": str(guess),
            "correct": result,
            "found_count": found_count,
        })

    except Exception:

        return


    room[
        "current_phase"
    ] = "result"


    # =========================================
    # 結果を少し表示
    # =========================================

    await asyncio.sleep(
        1.5
    )


    if rooms.get(
        room_id
    ) is not room:

        return


    # =========================================
    # CPU勝利
    # =========================================

    if cpu_player.is_winner():

        print(
            f"ルーム {room_id}: "
            "CPUの勝ち！"
        )


        await finish_game(
            room,
            winner=2,
        )

        return


    # =========================================
    # Player 1へターンを戻す
    # =========================================

    room[
        "current_turn"
    ] = 1

    room[
        "current_phase"
    ] = "question"


    print(
        f"ルーム {room_id}: "
        "Player 1 のターンです"
    )


    try:

        await send_turn_changed(
            room
        )

    except Exception:

        return


# =============================================
# WebSocket
# =============================================

@app.websocket(
    "/ws/{room_id}"
)
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
):

    await websocket.accept()


    # =========================================
    # ルームID整形
    # =========================================

    room_id = (
        room_id
        .strip()
        .upper()
    )


    # =========================================
    # ルームID形式
    # =========================================

    if not is_valid_room_id(
        room_id
    ):

        await websocket.send_json({
            "type": "error",
            "code": "INVALID_ROOM_ID",
            "message": (
                "ルームIDの形式が"
                "正しくありません。"
            ),
        })


        await websocket.close(
            code=4400
        )

        return


    # =========================================
    # ルーム存在確認
    # =========================================

    if room_id not in rooms:

        await websocket.send_json({
            "type": "error",
            "code": "ROOM_NOT_FOUND",
            "message": (
                f"ルーム {room_id} は"
                "存在しません。"
            ),
        })


        await websocket.close(
            code=4404
        )

        return


    room = rooms[
        room_id
    ]


    # =========================================
    # 最大人数
    # =========================================

    if room["mode"] == "cpu":

        max_players = 1

    else:

        max_players = 2


    if len(
        room["players"]
    ) >= max_players:

        await websocket.send_json({
            "type": "error",
            "code": "ROOM_FULL",
            "message": (
                f"ルーム {room_id} は"
                "すでに満員です。"
            ),
        })


        await websocket.close(
            code=4409
        )

        return


    # =========================================
    # プレイヤー登録
    # =========================================

    room["players"].append(
        websocket
    )


    player_number = len(
        room["players"]
    )


    print(
        f"ルーム {room_id}: "
        f"Player {player_number} "
        "が接続しました"
    )


    await websocket.send_json({
        "type": "player_number",
        "player": player_number,
        "room_id": room_id,
        "mode": room["mode"],
    })


    # =========================================
    # CPU戦開始
    # =========================================

    if (
        room["mode"] == "cpu"
        and
        len(
            room["players"]
        ) == 1
    ):

        print(
            f"ルーム {room_id}: "
            "CPU対戦を開始します"
        )


        await start_new_game(
            room_id
        )


    # =========================================
    # 対人戦開始
    # =========================================

    elif (
        room["mode"] == "pvp"
        and
        len(
            room["players"]
        ) == 2
    ):

        print(
            f"ルーム {room_id}: "
            "2人揃いました！"
        )


        await start_new_game(
            room_id
        )


    # =============================================
    # メイン受信ループ
    # =============================================

    try:

        while True:

            data = (
                await websocket.receive_json()
            )


            # 途中でルームが削除された
            if rooms.get(
                room_id
            ) is not room:

                return


            # =====================================
            # Player番号更新
            # =====================================

            if websocket in room["players"]:

                player_number = (
                    room["players"].index(
                        websocket
                    )
                    + 1
                )


            print(
                f"ルーム {room_id} / "
                f"Player {player_number} "
                f"から受信：{data}"
            )


            message_type = data.get(
                "type"
            )


            # =====================================
            # 再戦
            # =====================================

            if message_type == (
                "rematch_request"
            ):

                if (
                    room["current_phase"]
                    != "finished"
                ):

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "今は再戦を"
                            "選択できません。"
                        ),
                    })

                    continue


                # =================================
                # CPU戦は相手の承認不要
                # =================================

                if room["mode"] == "cpu":

                    print(
                        f"ルーム {room_id}: "
                        "CPUと再戦します"
                    )


                    await start_new_game(
                        room_id
                    )

                    continue


                # =================================
                # 対人戦
                # =================================

                room[
                    "rematch_requests"
                ].add(
                    player_number
                )


                print(
                    f"ルーム {room_id}: "
                    f"Player {player_number} "
                    "が再戦希望"
                )


                if (
                    room[
                        "rematch_requests"
                    ]
                    == {1, 2}
                ):

                    await start_new_game(
                        room_id
                    )


                else:

                    await websocket.send_json({
                        "type": (
                            "rematch_waiting"
                        ),
                    })


                continue


            # =====================================
            # ゲーム終了
            # =====================================

            elif message_type == (
                "leave_game"
            ):

                print(
                    f"ルーム {room_id}: "
                    f"Player {player_number} "
                    "がゲームを終了しました"
                )


                sockets = list(
                    room["players"]
                )


                # 対人戦なら相手へ通知

                for player_socket in sockets:

                    if (
                        player_socket
                        != websocket
                    ):

                        try:

                            await player_socket.send_json({
                                "type": (
                                    "opponent_left"
                                ),
                            })

                        except Exception:

                            pass


                rooms.pop(
                    room_id,
                    None,
                )


                room[
                    "players"
                ].clear()


                for player_socket in sockets:

                    try:

                        await player_socket.close()

                    except Exception:

                        pass


                return


            # =====================================
            # ゲーム未開始
            # =====================================

            if room["game"] is None:

                await websocket.send_json({
                    "type": "error",
                    "message": (
                        "まだゲームが"
                        "開始されていません。"
                    ),
                })

                continue


            # =====================================
            # ゲーム終了後
            # =====================================

            if (
                room["current_phase"]
                == "finished"
            ):

                await websocket.send_json({
                    "type": "error",
                    "message": (
                        "ゲームは終了しています。"
                        "再戦または終了を"
                        "選択してください。"
                    ),
                })

                continue


            # =====================================
            # 自分のターンか
            # =====================================

            if (
                player_number
                != room["current_turn"]
            ):

                await websocket.send_json({
                    "type": "error",
                    "message": (
                        "今はあなたの"
                        "ターンではありません。"
                    ),
                })

                continue


            # =====================================
            # 質問
            # =====================================

            if message_type == "question":

                if (
                    room["current_phase"]
                    != "question"
                ):

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "今はカードを"
                            "予想する番です。"
                        ),
                    })

                    continue


                # =================================
                # プレイヤー
                # =================================

                if player_number == 1:

                    asking_player = (
                        room["game"].player1
                    )

                    opponent = (
                        room["game"].player2
                    )


                else:

                    asking_player = (
                        room["game"].player2
                    )

                    opponent = (
                        room["game"].player1
                    )


                # =================================
                # 質問判定
                # =================================

                try:

                    (
                        question_text,
                        answer,
                    ) = evaluate_question(
                        room["game"],
                        asking_player,
                        opponent,
                        data,
                    )


                except ValueError as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(
                            error
                        ),
                    })

                    continue


                # =================================
                # 質問結果
                # =================================

                await websocket.send_json({
                    "type": "question_result",
                    "question": question_text,
                    "answer": answer,
                })


                # =================================
                # 予想フェーズ
                # =================================

                room[
                    "current_phase"
                ] = "guess"


                await websocket.send_json({
                    "type": "phase_changed",
                    "phase": "guess",
                })


                print(
                    f"Player "
                    f"{player_number} "
                    "のカード予想フェーズ"
                )


            # =====================================
            # カード予想
            # =====================================

            elif message_type == (
                "guess_card"
            ):

                if (
                    room["current_phase"]
                    != "guess"
                ):

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "先に質問してください。"
                        ),
                    })

                    continue


                # =================================
                # プレイヤー
                # =================================

                if player_number == 1:

                    guessing_player = (
                        room["game"].player1
                    )

                    opponent = (
                        room["game"].player2
                    )


                else:

                    guessing_player = (
                        room["game"].player2
                    )

                    opponent = (
                        room["game"].player1
                    )


                # =================================
                # カード作成
                # =================================

                try:

                    guess = create_guess_card(
                        data
                    )


                except ValueError as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(
                            error
                        ),
                    })

                    continue


                # =================================
                # 正解判定
                # =================================

                result = (
                    room["game"].guess_card(
                        guessing_player,
                        opponent,
                        guess,
                    )
                )


                found_count = len(
                    guessing_player.found_cards
                )


                # =================================
                # 予想結果
                # =================================

                await websocket.send_json({
                    "type": "guess_result",
                    "guess": str(
                        guess
                    ),
                    "correct": result,
                    "found_count": found_count,
                })


                # =================================
                # 「次へ」待ち
                # =================================

                room[
                    "current_phase"
                ] = "result"


                print(
                    f"ルーム {room_id}: "
                    f"Player {player_number} "
                    "の予想結果確認待ち"
                )


            # =====================================
            # 「次へ」
            # =====================================

            elif message_type == (
                "continue_after_guess"
            ):

                if (
                    room["current_phase"]
                    != "result"
                ):

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "今は「次へ」を"
                            "押すタイミングでは"
                            "ありません。"
                        ),
                    })

                    continue


                # =================================
                # 現在プレイヤー
                # =================================

                if player_number == 1:

                    current_player = (
                        room["game"].player1
                    )


                else:

                    current_player = (
                        room["game"].player2
                    )


                # =================================
                # 勝利判定
                # =================================

                if current_player.is_winner():

                    print(
                        f"ルーム {room_id}: "
                        f"Player {player_number} "
                        "の勝ち！"
                    )


                    await finish_game(
                        room,
                        winner=player_number,
                    )

                    continue


                # =================================
                # CPU対戦
                # =================================

                if room["mode"] == "cpu":

                    room[
                        "current_turn"
                    ] = 2

                    room[
                        "current_phase"
                    ] = "question"


                    print(
                        f"ルーム {room_id}: "
                        "CPUのターンです"
                    )


                    await send_turn_changed(
                        room
                    )


                    await cpu_take_turn(
                        room_id
                    )


                    continue


                # =================================
                # 対人戦ターン交代
                # =================================

                if (
                    room["current_turn"]
                    == 1
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


                print(
                    f"ルーム {room_id}: "
                    f"Player "
                    f"{room['current_turn']} "
                    "のターンです"
                )


                await send_turn_changed(
                    room
                )


            # =====================================
            # 不明
            # =====================================

            else:

                await websocket.send_json({
                    "type": "error",
                    "message": (
                        "不明な操作です。"
                    ),
                })


    # =============================================
    # 切断
    # =============================================

    except WebSocketDisconnect:

        print(
            f"ルーム {room_id}: "
            f"Player {player_number} "
            "が切断しました"
        )


        # すでに削除済みなら終了

        if (
            rooms.get(
                room_id
            )
            is not room
        ):

            return


        if websocket in room["players"]:

            room["players"].remove(
                websocket
            )


        # =========================================
        # CPU戦
        # =========================================

        if room["mode"] == "cpu":

            rooms.pop(
                room_id,
                None,
            )


            room[
                "players"
            ].clear()


            print(
                f"CPUルーム {room_id} "
                "を削除しました"
            )

            return


        # =========================================
        # 対人戦
        # 誰も残っていない
        # =========================================

        if len(
            room["players"]
        ) == 0:

            rooms.pop(
                room_id,
                None,
            )


            print(
                f"ルーム {room_id} "
                "を削除しました"
            )

            return


        # =========================================
        # 対人戦
        # 相手が残っている
        # =========================================

        remaining_players = list(
            room["players"]
        )


        rooms.pop(
            room_id,
            None,
        )


        room[
            "players"
        ].clear()


        for remaining_player in (
            remaining_players
        ):

            try:

                await remaining_player.send_json({
                    "type": (
                        "opponent_disconnected"
                    ),
                })


            except Exception:

                pass


            try:

                await remaining_player.close()


            except Exception:

                pass


        print(
            f"ルーム {room_id}: "
            "対戦を終了し、"
            "ルームを削除しました"
        )