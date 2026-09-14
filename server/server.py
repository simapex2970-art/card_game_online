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


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():

    return FileResponse(
        WEB_DIR / "robots.txt",
        media_type="text/plain"
    )


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():

    return FileResponse(
        WEB_DIR / "sitemap.xml",
        media_type="application/xml"
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
# ルーム管理
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


def create_room():

    return {
        "players": [],
        "game": None,
        "current_turn": 1,
        "current_phase": "question",
        "rematch_requests": set(),
    }


# =============================================
# ルーム作成API
# =============================================

@app.post("/rooms")
async def create_room_endpoint():

    room_id = generate_room_id()

    rooms[room_id] = create_room()

    print(
        f"ルーム {room_id} を作成しました"
    )

    return {
        "room_id": room_id
    }


# =============================================
# 新しいゲーム開始
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


    if len(
        room["players"]
    ) != 2:

        raise ValueError(
            f"ルーム {room_id} に"
            "2人揃っていません。"
        )


    room["game"] = Game()

    room["current_turn"] = 1

    room["current_phase"] = (
        "question"
    )

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
    })


    # =========================================
    # Player 2
    # =========================================

    await room["players"][1].send_json({
        "type": "game_start",
        "player": 2,
        "hand": player2_hand,
        "your_turn": False,
        "phase": "waiting",
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
# ターン情報
# =============================================

async def send_turn_changed(
    room,
):

    if len(
        room["players"]
    ) != 2:

        return


    current_turn = (
        room["current_turn"]
    )


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
    # ルームID形式チェック
    # =========================================

    if (
        len(room_id)
        != ROOM_ID_LENGTH
        or any(
            character
            not in ROOM_ID_CHARACTERS
            for character
            in room_id
        )
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

    if (
        room_id
        not in rooms
    ):

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
    # 満員確認
    # =========================================

    if (
        len(
            room["players"]
        )
        >= 2
    ):

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
    })


    # =========================================
    # 2人揃ったらゲーム開始
    # =========================================

    if len(
        room["players"]
    ) == 2:

        print(
            f"ルーム {room_id}: "
            "2人揃いました！"
        )


        await start_new_game(
            room_id
        )


    # =========================================
    # メインループ
    # =========================================

    try:

        while True:

            data = (
                await websocket.receive_json()
            )


            # =================================
            # 現在のPlayer番号
            # =================================

            if (
                websocket
                in room["players"]
            ):

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

            if (
                message_type
                == "rematch_request"
            ):

                if (
                    room[
                        "current_phase"
                    ]
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

            if (
                message_type
                == "leave_game"
            ):

                print(
                    f"ルーム {room_id}: "
                    f"Player {player_number} "
                    "がゲームを終了しました"
                )


                # -----------------------------
                # 相手へ通知
                # -----------------------------

                for player_socket in list(
                    room["players"]
                ):

                    if (
                        player_socket
                        != websocket
                    ):

                        try:

                            await (
                                player_socket
                                .send_json({
                                    "type": (
                                        "opponent_left"
                                    ),
                                })
                            )

                        except Exception:

                            pass


                # -----------------------------
                # 接続一覧をコピー
                # -----------------------------

                sockets = list(
                    room["players"]
                )


                # -----------------------------
                # ルーム削除
                # -----------------------------

                rooms.pop(
                    room_id,
                    None,
                )


                room[
                    "players"
                ].clear()

                room["game"] = None

                room[
                    "current_turn"
                ] = 1

                room[
                    "current_phase"
                ] = "question"

                room[
                    "rematch_requests"
                ].clear()


                # -----------------------------
                # 全接続を閉じる
                # -----------------------------

                for player_socket in sockets:

                    try:

                        await (
                            player_socket
                            .close()
                        )

                    except Exception:

                        pass


                return


            # =====================================
            # ゲーム未開始
            # =====================================

            if (
                room["game"]
                is None
            ):

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
                room[
                    "current_phase"
                ]
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
            # ターン確認
            # =====================================

            if (
                player_number
                != room[
                    "current_turn"
                ]
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

            if (
                message_type
                == "question"
            ):

                if (
                    room[
                        "current_phase"
                    ]
                    != "question"
                ):

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "今は質問する"
                            "タイミングではありません。"
                        ),
                    })

                    continue


                # =============================
                # プレイヤー
                # =============================

                if (
                    player_number
                    == 1
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


                question_id = data.get(
                    "question_id"
                )


                answer = None

                question_text = None


                # =============================
                # 1 偶数
                # =============================

                if (
                    question_id
                    == 1
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_even(
                            opponent.hand,
                            asking_player
                            .found_cards,
                        )
                    )

                    question_text = (
                        "偶数はある？"
                    )


                # =============================
                # 2 奇数
                # =============================

                elif (
                    question_id
                    == 2
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_odd(
                            opponent.hand,
                            asking_player
                            .found_cards,
                        )
                    )

                    question_text = (
                        "奇数はある？"
                    )


                # =============================
                # 3 絵札
                # =============================

                elif (
                    question_id
                    == 3
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_face(
                            opponent.hand,
                            asking_player
                            .found_cards,
                        )
                    )

                    question_text = (
                        "絵札はある？"
                    )


                # =============================
                # 4 ランク
                # =============================

                elif (
                    question_id
                    == 4
                ):

                    rank = data.get(
                        "rank"
                    )


                    if (
                        rank
                        not in VALID_RANKS
                    ):

                        await websocket.send_json({
                            "type": "error",
                            "message": (
                                "指定したランクが"
                                "正しくありません。"
                            ),
                        })

                        continue


                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_rank(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            rank,
                        )
                    )


                    question_text = (
                        f"{rank} はある？"
                    )


                # =============================
                # 5 以上
                # =============================

                elif (
                    question_id
                    == 5
                ):

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

                        await websocket.send_json({
                            "type": "error",
                            "message": (
                                "数字は1～13で"
                                "指定してください。"
                            ),
                        })

                        continue


                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_more_than(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            number,
                        )
                    )


                    question_text = (
                        f"{number} 以上の"
                        "カードはある？"
                    )


                # =============================
                # 6 以下
                # =============================

                elif (
                    question_id
                    == 6
                ):

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

                        await websocket.send_json({
                            "type": "error",
                            "message": (
                                "数字は1～13で"
                                "指定してください。"
                            ),
                        })

                        continue


                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_less_than(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            number,
                        )
                    )


                    question_text = (
                        f"{number} 以下の"
                        "カードはある？"
                    )


                # =============================
                # 7 スペード
                # =============================

                elif (
                    question_id
                    == 7
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_suit(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            "スペード",
                        )
                    )

                    question_text = (
                        "スペードはある？"
                    )


                # =============================
                # 8 ハート
                # =============================

                elif (
                    question_id
                    == 8
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_suit(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            "ハート",
                        )
                    )

                    question_text = (
                        "ハートはある？"
                    )


                # =============================
                # 9 ダイヤ
                # =============================

                elif (
                    question_id
                    == 9
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_suit(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            "ダイヤ",
                        )
                    )

                    question_text = (
                        "ダイヤはある？"
                    )


                # =============================
                # 10 クラブ
                # =============================

                elif (
                    question_id
                    == 10
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_suit(
                            opponent.hand,
                            asking_player
                            .found_cards,
                            "クラブ",
                        )
                    )

                    question_text = (
                        "クラブはある？"
                    )


                # =============================
                # 11 JOKER
                # =============================

                elif (
                    question_id
                    == 11
                ):

                    answer = (
                        room[
                            "game"
                        ]
                        .question_manager
                        .ask_joker(
                            opponent.hand,
                            asking_player
                            .found_cards,
                        )
                    )

                    question_text = (
                        "JOKERはある？"
                    )


                # =============================
                # 不正な質問番号
                # =============================

                else:

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "質問番号が"
                            "正しくありません。"
                        ),
                    })

                    continue


                # =============================
                # 質問結果
                # =============================

                await websocket.send_json({
                    "type": "question_result",
                    "question": question_text,
                    "answer": answer,
                })


                # =============================
                # 予想フェーズへ
                # =============================

                room[
                    "current_phase"
                ] = "guess"


                await websocket.send_json({
                    "type": "phase_changed",
                    "phase": "guess",
                })


                print(
                    f"ルーム {room_id}: "
                    f"Player {player_number} "
                    "のカード予想フェーズ"
                )


            # =====================================
            # カード予想
            # =====================================

            elif (
                message_type
                == "guess_card"
            ):

                if (
                    room[
                        "current_phase"
                    ]
                    != "guess"
                ):

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "先に質問してください。"
                        ),
                    })

                    continue


                # =============================
                # プレイヤー
                # =============================

                if (
                    player_number
                    == 1
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


                suit = data.get(
                    "suit"
                )

                rank = data.get(
                    "rank"
                )


                # =============================
                # JOKER
                # =============================

                if (
                    suit
                    == "JOKER"
                ):

                    guess = Card(
                        "JOKER"
                    )


                # =============================
                # 通常カード
                # =============================

                else:

                    if (
                        suit
                        not in VALID_SUITS
                    ):

                        await websocket.send_json({
                            "type": "error",
                            "message": (
                                "スートが"
                                "正しくありません。"
                            ),
                        })

                        continue


                    if (
                        rank
                        not in VALID_RANKS
                    ):

                        await websocket.send_json({
                            "type": "error",
                            "message": (
                                "ランクが"
                                "正しくありません。"
                            ),
                        })

                        continue


                    guess = Card(
                        suit,
                        rank,
                    )


                # =============================
                # 正解判定
                # =============================

                result = (
                    room[
                        "game"
                    ].guess_card(
                        guessing_player,
                        opponent,
                        guess,
                    )
                )


                found_count = len(
                    guessing_player
                    .found_cards
                )


                # =============================
                # 予想結果
                # =============================

                await websocket.send_json({
                    "type": "guess_result",
                    "guess": str(guess),
                    "correct": result,
                    "found_count": (
                        found_count
                    ),
                })


                # =============================
                # 次へ待ち
                # =============================

                room[
                    "current_phase"
                ] = "result"


                print(
                    f"ルーム {room_id}: "
                    f"Player {player_number} "
                    "の予想結果確認待ち"
                )


            # =====================================
            # 次へ
            # =====================================

            elif (
                message_type
                == "continue_after_guess"
            ):

                if (
                    room[
                        "current_phase"
                    ]
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


                # =============================
                # 現在Player
                # =============================

                if (
                    player_number
                    == 1
                ):

                    current_player = (
                        room[
                            "game"
                        ].player1
                    )

                else:

                    current_player = (
                        room[
                            "game"
                        ].player2
                    )


                # =============================
                # 勝利判定
                # =============================

                if (
                    current_player
                    .is_winner()
                ):

                    print(
                        f"ルーム {room_id}: "
                        f"Player {player_number} "
                        "の勝ち！"
                    )


                    player1_hand = [
                        str(card)
                        for card
                        in room[
                            "game"
                        ].player1.hand
                    ]


                    player2_hand = [
                        str(card)
                        for card
                        in room[
                            "game"
                        ].player2.hand
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

                        await (
                            player_socket
                            .send_json({
                                "type": (
                                    "game_over"
                                ),
                                "winner": (
                                    player_number
                                ),
                                "player1_hand": (
                                    player1_hand
                                ),
                                "player2_hand": (
                                    player2_hand
                                ),
                            })
                        )


                    continue


                # =============================
                # ターン交代
                # =============================

                if (
                    room[
                        "current_turn"
                    ]
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
            # 不明な操作
            # =====================================

            else:

                await websocket.send_json({
                    "type": "error",
                    "message": (
                        "不明な操作です。"
                    ),
                })


    # =============================================
    # 予期しない切断
    # =============================================

    except WebSocketDisconnect:

        print(
            f"ルーム {room_id}: "
            f"Player {player_number} "
            "が切断しました"
        )


        # =========================================
        # leave_gameですでに削除されていたら終了
        # =========================================

        if (
            rooms.get(
                room_id
            )
            is not room
        ):

            return


        # =========================================
        # 切断したPlayerを削除
        # =========================================

        if (
            websocket
            in room["players"]
        ):

            room[
                "players"
            ].remove(
                websocket
            )


        # =========================================
        # 残っている相手
        # =========================================

        remaining_players = list(
            room["players"]
        )


        # =========================================
        # 相手へ通知
        # =========================================

        for player_socket in (
            remaining_players
        ):

            try:

                await (
                    player_socket
                    .send_json({
                        "type": (
                            "opponent_disconnected"
                        ),
                    })
                )

            except Exception:

                pass


        # =========================================
        # ルーム終了
        # =========================================

        rooms.pop(
            room_id,
            None,
        )


        room[
            "players"
        ].clear()

        room["game"] = None

        room[
            "current_turn"
        ] = 1

        room[
            "current_phase"
        ] = "question"

        room[
            "rematch_requests"
        ].clear()


        print(
            f"ルーム {room_id}: "
            "切断のためルームを終了しました"
        )


        # =========================================
        # 残ったWebSocketも閉じる
        # =========================================

        for player_socket in (
            remaining_players
        ):

            try:

                await (
                    player_socket
                    .close()
                )

            except Exception:

                pass


        return