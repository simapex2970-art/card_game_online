import asyncio
import json

import websockets
from websockets.exceptions import ConnectionClosed


# 自分のPlayer番号
my_player_number = None

# 自分のターンか
my_turn = False

# waiting / question / guess / finished / waiting_rematch
my_phase = "waiting"


# =============================================
# サーバーから受信
# =============================================
async def receive_messages(websocket):
    global my_player_number
    global my_turn
    global my_phase

    try:
        while True:
            message = await websocket.recv()

            data = json.loads(
                message
            )

            message_type = data.get(
                "type"
            )

            # =================================
            # Player番号
            # =================================
            if message_type == "player_number":

                my_player_number = data[
                    "player"
                ]

                print(
                    f"あなたは Player "
                    f"{my_player_number} です"
                )

            # =================================
            # ゲーム開始
            # =================================
            elif message_type == "game_start":

                my_turn = data[
                    "your_turn"
                ]

                my_phase = data[
                    "phase"
                ]

                print()
                print("====================")
                print("新しいゲーム開始")
                print("====================")

                print()
                print(
                    f"あなたは Player "
                    f"{data['player']}"
                )

                print()
                print("あなたの手札")

                for card in data["hand"]:

                    print(
                        f"・{card}"
                    )

                print()
                print("====================")

                if my_turn:

                    print(
                        "あなたのターンです。"
                    )

                    show_question_menu()

                else:

                    print(
                        "相手のターンです。"
                    )

                    print(
                        "相手の操作を待っています。"
                    )

                print()

            # =================================
            # 質問結果
            # =================================
            elif message_type == "question_result":

                print()
                print("====================")

                print(
                    data["question"]
                )

                if data["answer"]:

                    print(
                        "答え：はい"
                    )

                else:

                    print(
                        "答え：いいえ"
                    )

                print("====================")
                print()

            # =================================
            # フェーズ変更
            # =================================
            elif message_type == "phase_changed":

                my_phase = data[
                    "phase"
                ]

                if my_phase == "guess":

                    print(
                        "続いてカードを"
                        "1枚予想してください。"
                    )

                    show_guess_menu()

            # =================================
            # カード予想結果
            # =================================
            elif message_type == "guess_result":

                print()
                print("====================")

                print(
                    f"予想：{data['guess']}"
                )

                if data["correct"]:

                    print(
                        "結果：正解！"
                    )

                else:

                    print(
                        "結果：不正解"
                    )

                print(
                    f"現在 "
                    f"{data['found_count']} "
                    f"/ 3 枚正解"
                )

                print("====================")
                print()

            # =================================
            # ターン変更
            # =================================
            elif message_type == "turn_changed":

                my_turn = data[
                    "your_turn"
                ]

                my_phase = data[
                    "phase"
                ]

                print()
                print("--------------------")

                if my_turn:

                    print(
                        "あなたのターンです！"
                    )

                    show_question_menu()

                else:

                    print(
                        f"Player "
                        f"{data['current_turn']} "
                        f"のターンです。"
                    )

                    print(
                        "相手の操作を待っています。"
                    )

                print("--------------------")
                print()

            # =================================
            # ゲーム終了
            # =================================
            elif message_type == "game_over":

                my_turn = False
                my_phase = "finished"

                print()
                print("====================")
                print("ゲーム終了")

                if (
                    data["winner"]
                    == my_player_number
                ):

                    print(
                        "あなたの勝ちです！"
                    )

                else:

                    print(
                        f"Player "
                        f"{data['winner']} "
                        f"の勝ちです。"
                    )

                print()
                print("Player 1 の手札")

                for card in data[
                    "player1_hand"
                ]:

                    print(
                        f"・{card}"
                    )

                print()
                print("Player 2 の手札")

                for card in data[
                    "player2_hand"
                ]:

                    print(
                        f"・{card}"
                    )

                print("====================")

                show_rematch_menu()

            # =================================
            # 再戦待ち
            # =================================
            elif message_type == "rematch_waiting":

                my_turn = False

                my_phase = (
                    "waiting_rematch"
                )

                print()
                print("====================")
                print(
                    "再戦を希望しました。"
                )

                print(
                    "相手の再戦選択を"
                    "待っています..."
                )

                print("====================")
                print()

            # =================================
            # 相手が終了
            # =================================
            elif message_type == "opponent_left":

                my_turn = False
                my_phase = "finished"

                print()
                print("====================")
                print(
                    "相手がゲームを終了しました。"
                )

                print(
                    "接続を終了します。"
                )

                print("====================")
                print()

            # =================================
            # 相手が切断
            # =================================
            elif message_type == "opponent_disconnected":

                my_turn = False
                my_phase = "finished"

                print()
                print("====================")
                print(
                    "相手が切断しました。"
                )

                print(
                    "ゲームを終了します。"
                )

                print("====================")
                print()

            # =================================
            # エラー
            # =================================
            elif message_type == "error":

                print()
                print(
                    f"エラー："
                    f"{data['message']}"
                )
                print()

    except ConnectionClosed:

        print()
        print(
            "サーバーとの接続が終了しました。"
        )


# =============================================
# 質問メニュー
# =============================================
def show_question_menu():

    print()
    print(
        "質問を選んでください。"
    )

    print()

    print(
        " 1：偶数はある？"
    )

    print(
        " 2：奇数はある？"
    )

    print(
        " 3：絵札はある？"
    )

    print(
        " 4：指定したランクはある？"
    )

    print(
        " 5：指定した数字以上はある？"
    )

    print(
        " 6：指定した数字以下はある？"
    )

    print(
        " 7：スペードはある？"
    )

    print(
        " 8：ハートはある？"
    )

    print(
        " 9：ダイヤはある？"
    )

    print(
        "10：クラブはある？"
    )

    print(
        "11：JOKERはある？"
    )

    print()


# =============================================
# カード予想メニュー
# =============================================
def show_guess_menu():

    print()
    print(
        "カード予想"
    )

    print()

    print(
        "通常カードは"
    )

    print(
        "「スペード A」のように入力します。"
    )

    print()

    print(
        "例："
    )

    print(
        "スペード A"
    )

    print(
        "ハート 10"
    )

    print(
        "ダイヤ Q"
    )

    print()

    print(
        "Jokerの場合："
    )

    print(
        "JOKER"
    )

    print()


# =============================================
# 再戦メニュー
# =============================================
def show_rematch_menu():

    print()
    print(
        "もう一度遊びますか？"
    )

    print()
    print(
        "1：もう一度遊ぶ"
    )

    print(
        "2：終了"
    )

    print()


# =============================================
# サーバーへ送信
# =============================================
async def send_messages(websocket):
    global my_turn
    global my_phase

    while True:

        user_input = await asyncio.to_thread(
            input,
            "入力："
        )

        user_input = user_input.strip()

        # =====================================
        # ゲーム終了後
        # =====================================
        if my_phase == "finished":

            # ---------------------------------
            # 再戦
            # ---------------------------------
            if user_input == "1":

                await websocket.send(
                    json.dumps({
                        "type": (
                            "rematch_request"
                        )
                    })
                )

                my_phase = (
                    "waiting_rematch"
                )

                print()
                print(
                    "再戦希望を送信しました。"
                )

                print(
                    "相手の選択を待っています..."
                )

                continue

            # ---------------------------------
            # 終了
            # ---------------------------------
            elif user_input == "2":

                await websocket.send(
                    json.dumps({
                        "type": "leave_game"
                    })
                )

                print()
                print(
                    "ゲームを終了します。"
                )

                return

            else:

                print(
                    "1 または 2 を"
                    "入力してください。"
                )

                continue

        # =====================================
        # 再戦相手待ち
        # =====================================
        if my_phase == "waiting_rematch":

            print(
                "相手の再戦選択を"
                "待っています。"
            )

            continue

        # =====================================
        # 相手のターン
        # =====================================
        if not my_turn:

            print(
                "今は相手のターンです。"
            )

            continue

        # =====================================
        # 質問フェーズ
        # =====================================
        if my_phase == "question":

            try:

                question_id = int(
                    user_input
                )

            except ValueError:

                print(
                    "質問番号を"
                    "1～11で入力してください。"
                )

                continue

            if (
                question_id < 1
                or question_id > 11
            ):

                print(
                    "質問番号は1～11です。"
                )

                continue

            # =================================
            # 4. 指定ランク
            # =================================
            if question_id == 4:

                rank = await asyncio.to_thread(
                    input,
                    "ランクを入力してください "
                    "(A, 2～10, J, Q, K)："
                )

                rank = (
                    rank
                    .strip()
                    .upper()
                )

                valid_ranks = [
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

                if rank not in valid_ranks:

                    print(
                        "ランクが正しくありません。"
                    )

                    continue

                await websocket.send(
                    json.dumps({
                        "type": "question",
                        "question_id": 4,
                        "rank": rank
                    })
                )

                my_phase = "waiting"

            # =================================
            # 5. 指定数字以上
            # =================================
            elif question_id == 5:

                number_text = (
                    await asyncio.to_thread(
                        input,
                        "数字を入力してください "
                        "(1～13)："
                    )
                )

                try:

                    number = int(
                        number_text
                    )

                except ValueError:

                    print(
                        "数字で入力してください。"
                    )

                    continue

                if (
                    number < 1
                    or number > 13
                ):

                    print(
                        "1～13で入力してください。"
                    )

                    continue

                await websocket.send(
                    json.dumps({
                        "type": "question",
                        "question_id": 5,
                        "number": number
                    })
                )

                my_phase = "waiting"

            # =================================
            # 6. 指定数字以下
            # =================================
            elif question_id == 6:

                number_text = (
                    await asyncio.to_thread(
                        input,
                        "数字を入力してください "
                        "(1～13)："
                    )
                )

                try:

                    number = int(
                        number_text
                    )

                except ValueError:

                    print(
                        "数字で入力してください。"
                    )

                    continue

                if (
                    number < 1
                    or number > 13
                ):

                    print(
                        "1～13で入力してください。"
                    )

                    continue

                await websocket.send(
                    json.dumps({
                        "type": "question",
                        "question_id": 6,
                        "number": number
                    })
                )

                my_phase = "waiting"

            # =================================
            # その他の質問
            # =================================
            else:

                await websocket.send(
                    json.dumps({
                        "type": "question",
                        "question_id": question_id
                    })
                )

                my_phase = "waiting"

        # =====================================
        # カード予想
        # =====================================
        elif my_phase == "guess":

            # =================================
            # Joker
            # =================================
            if (
                user_input.upper()
                == "JOKER"
            ):

                await websocket.send(
                    json.dumps({
                        "type": "guess_card",
                        "suit": "JOKER",
                        "rank": None
                    })
                )

                my_phase = "waiting"

                continue

            parts = (
                user_input.split()
            )

            if len(parts) != 2:

                print()

                print(
                    "「スペード A」のように"
                    "入力してください。"
                )

                print(
                    "Jokerの場合は "
                    "JOKER と入力してください。"
                )

                continue

            suit = parts[0]

            rank = (
                parts[1]
                .upper()
            )

            valid_suits = [
                "スペード",
                "ハート",
                "ダイヤ",
                "クラブ"
            ]

            valid_ranks = [
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

            if suit not in valid_suits:

                print(
                    "スートが正しくありません。"
                )

                print(
                    "スペード / ハート / "
                    "ダイヤ / クラブ"
                )

                continue

            if rank not in valid_ranks:

                print(
                    "ランクが正しくありません。"
                )

                print(
                    "A～10 / J / Q / K"
                )

                continue

            await websocket.send(
                json.dumps({
                    "type": "guess_card",
                    "suit": suit,
                    "rank": rank
                })
            )

            my_phase = "waiting"

        # =====================================
        # サーバー待ち
        # =====================================
        else:

            print(
                "サーバーからの返事を"
                "待っています。"
            )


# =============================================
# サーバー接続
# =============================================
async def connect_server():

    uri = (
        "ws://127.0.0.1:8000/ws"
    )

    print(
        "サーバーに接続します..."
    )

    try:

        async with websockets.connect(
            uri
        ) as websocket:

            print(
                "接続しました！"
            )

            await asyncio.gather(
                receive_messages(
                    websocket
                ),
                send_messages(
                    websocket
                )
            )

    except ConnectionClosed:

        print()
        print(
            "接続が終了しました。"
        )


asyncio.run(
    connect_server()
)