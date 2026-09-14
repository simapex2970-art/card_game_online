import asyncio
import json
import threading
import tkinter as tk
from tkinter import messagebox
from urllib.error import URLError
from urllib.request import Request, urlopen

import websockets
from websockets.exceptions import ConnectionClosed

from card import Card


class OnlineGameGUI:

    def __init__(self, root):
        self.root = root

        self.root.title(
            "カード推理ゲーム - オンライン"
        )

        self.root.geometry(
            "850x900"
        )

        # ========================================
        # ネットワーク
        # ========================================
        self.websocket = None
        self.event_loop = None
        self.network_thread = None
        self.room_id = None

        # ========================================
        # プレイヤー状態
        # ========================================
        self.player_number = None
        self.my_turn = False
        self.phase = "connecting"

        self.my_hand = []

        # ========================================
        # 正解枚数
        # ========================================
        self.found_count = 0

        # ========================================
        # 質問
        # ========================================
        self.selected_question = None
        self.number_question_type = None
        self.last_question_answer = None

        # ========================================
        # 予想
        # ========================================
        self.saved_guess_suit = "スペード"
        self.saved_guess_rank = "A"

        self.last_guess_text = None
        self.last_guess_result = None

        # ========================================
        # 予想結果表示用
        # ========================================
        self.awaiting_guess_result = False
        self.showing_guess_result = False

        self.pending_turn_change = None
        self.pending_game_over = None

        self.next_button = None

        # ========================================
        # 通信待ち
        # ========================================
        self.waiting_for_server = False

        # ========================================
        # タイトル
        # ========================================
        title_label = tk.Label(
            self.root,
            text="カード推理ゲーム",
            font=("Arial", 24, "bold")
        )

        title_label.pack(
            pady=20
        )

        # ========================================
        # Player表示
        # ========================================
        self.player_label = tk.Label(
            self.root,
            text="サーバー接続中...",
            font=("Arial", 18)
        )

        self.player_label.pack(
            pady=10
        )

        # ========================================
        # メッセージ
        # ========================================
        self.message_label = tk.Label(
            self.root,
            text="サーバーに接続しています...",
            font=("Arial", 14)
        )

        self.message_label.pack(
            pady=10
        )

        # ========================================
        # メイン表示
        # ========================================
        self.content_frame = tk.Frame(
            self.root
        )

        self.content_frame.pack(
            pady=20
        )

        # ========================================
        # 起動直後はルームID入力画面
        # ========================================
        self.show_room_screen()

    # =========================================================
    # ルーム選択
    # =========================================================
    def show_room_screen(self):

        self.clear_content_frame()

        self.player_label.config(
            text="ルーム選択"
        )

        self.message_label.config(
            text="ルームを作るか、既存ルームに参加してください"
        )

        create_title = tk.Label(
            self.content_frame,
            text="新しいルームを作る",
            font=("Arial", 20, "bold")
        )

        create_title.pack(
            pady=(20, 10)
        )

        create_button = tk.Button(
            self.content_frame,
            text="ルームを作る",
            font=("Arial", 15),
            width=18,
            command=self.create_new_room
        )

        create_button.pack(
            pady=10
        )

        separator = tk.Label(
            self.content_frame,
            text="────────────",
            font=("Arial", 16)
        )

        separator.pack(
            pady=20
        )

        join_title = tk.Label(
            self.content_frame,
            text="既存ルームに参加",
            font=("Arial", 20, "bold")
        )

        join_title.pack(
            pady=(5, 10)
        )

        self.room_entry = tk.Entry(
            self.content_frame,
            font=("Arial", 20),
            width=16,
            justify="center"
        )

        self.room_entry.pack(
            pady=10
        )

        self.room_entry.focus_set()

        info_label = tk.Label(
            self.content_frame,
            text="相手から教えてもらったルームIDを入力",
            font=("Arial", 12)
        )

        info_label.pack(
            pady=5
        )

        join_button = tk.Button(
            self.content_frame,
            text="ルームに参加",
            font=("Arial", 15),
            width=18,
            command=self.join_room
        )

        join_button.pack(
            pady=15
        )

        self.room_entry.bind(
            "<Return>",
            lambda event: self.join_room()
        )

    # =========================================================
    # 新しいルームを作る
    # =========================================================
    def create_new_room(self):

        if (
            self.network_thread is not None
            and self.network_thread.is_alive()
        ):
            return

        self.clear_content_frame()

        self.player_label.config(
            text="ルーム作成中"
        )

        self.message_label.config(
            text="サーバーにルーム作成を依頼しています..."
        )

        label = tk.Label(
            self.content_frame,
            text="ルームを作成しています...",
            font=("Arial", 20)
        )

        label.pack(
            pady=60
        )

        self.network_thread = threading.Thread(
            target=self.create_room_and_connect,
            daemon=True
        )

        self.network_thread.start()

    # =========================================================
    # サーバーにルーム作成を依頼して接続
    # =========================================================
    def create_room_and_connect(self):

        try:

            request = Request(
                "http://127.0.0.1:8000/rooms",
                data=b"",
                method="POST"
            )

            with urlopen(
                request,
                timeout=5
            ) as response:

                response_data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            self.room_id = response_data[
                "room_id"
            ]

            self.root.after(
                0,
                self.show_connecting_screen
            )

            self.start_network()

        except (
            URLError,
            KeyError,
            ValueError,
            json.JSONDecodeError
        ) as error:

            self.root.after(
                0,
                self.show_connection_error,
                (
                    "ルームを作成できませんでした。\n"
                    f"{error}"
                )
            )

    # =========================================================
    # 既存ルームに参加
    # =========================================================
    def join_room(self):

        room_id = (
            self.room_entry
            .get()
            .strip()
            .upper()
        )

        if not room_id:

            messagebox.showwarning(
                "入力エラー",
                "ルームIDを入力してください。"
            )

            return

        if not room_id.isalnum():

            messagebox.showwarning(
                "入力エラー",
                "ルームIDは英数字で入力してください。"
            )

            return

        self.room_id = room_id

        self.show_connecting_screen()

        if (
            self.network_thread is not None
            and self.network_thread.is_alive()
        ):
            return

        self.network_thread = threading.Thread(
            target=self.start_network,
            daemon=True
        )

        self.network_thread.start()

    # =========================================================
    # 接続中
    # =========================================================
    def show_connecting_screen(self):

        self.clear_content_frame()

        label = tk.Label(
            self.content_frame,
            text=(
                f"ルーム {self.room_id} に\n"
                "接続しています..."
            ),
            font=("Arial", 20),
            justify="center"
        )

        label.pack(
            pady=60
        )

    # =========================================================
    # 相手待ち
    # =========================================================
    def show_waiting_screen(self):

        self.clear_content_frame()

        self.message_label.config(
            text="相手の接続を待っています..."
        )

        room_label = tk.Label(
            self.content_frame,
            text=f"ルームID：{self.room_id}",
            font=("Arial", 28, "bold")
        )

        room_label.pack(
            pady=(35, 15)
        )

        waiting_label = tk.Label(
            self.content_frame,
            text=(
                "このルームIDを相手に伝えてください。\n\n"
                "もう1人のプレイヤーを\n"
                "待っています..."
            ),
            font=("Arial", 18),
            justify="center"
        )

        waiting_label.pack(
            pady=20
        )

    # =========================================================
    # ゲーム開始
    # =========================================================
    def show_game_start_screen(self):

        self.clear_content_frame()

        self.player_label.config(
            text=(f"Room {self.room_id} / Player {self.player_number}")
        )

        if self.my_turn:

            self.message_label.config(
                text="あなたのターンです"
            )

        else:

            self.message_label.config(
                text="相手のターンです"
            )

        hand_title = tk.Label(
            self.content_frame,
            text="あなたの手札",
            font=("Arial", 20, "bold")
        )

        hand_title.pack(
            pady=(5, 20)
        )

        cards_frame = tk.Frame(
            self.content_frame
        )

        cards_frame.pack(
            pady=5
        )

        for card in self.my_hand:

            card_widget = self.create_card_widget(
                cards_frame,
                card
            )

            card_widget.pack(
                side="left",
                padx=12
            )

        if self.my_turn:

            question_button = tk.Button(
                self.content_frame,
                text="質問を選ぶ",
                font=("Arial", 14),
                width=18,
                command=self.show_question_screen
            )

            question_button.pack(
                pady=30
            )

        else:

            waiting_label = tk.Label(
                self.content_frame,
                text=(
                    "相手のターンです。\n"
                    "相手の操作を待っています。"
                ),
                font=("Arial", 15),
                justify="center"
            )

            waiting_label.pack(
                pady=30
            )

    # =========================================================
    # 質問画面
    # =========================================================
    def show_question_screen(self):

        if not self.my_turn:
            return

        if self.phase != "question":
            return

        self.clear_content_frame()

        self.message_label.config(
            text="質問を1つ選んでください"
        )

        title_label = tk.Label(
            self.content_frame,
            text="質問",
            font=("Arial", 20, "bold")
        )

        title_label.pack(
            pady=10
        )

        questions = [
            "偶数はある？",
            "奇数はある？",
            "絵札はある？",
            "指定したランクはある？",
            "指定した数字以上はある？",
            "指定した数字以下はある？",
            "スペードはある？",
            "ハートはある？",
            "ダイヤはある？",
            "クラブはある？",
            "JOKERはある？"
        ]

        for number, question in enumerate(
            questions,
            start=1
        ):

            button = tk.Button(
                self.content_frame,
                text=f"{number}. {question}",
                font=("Arial", 12),
                width=32,
                command=lambda n=number: (
                    self.select_question(n)
                )
            )

            button.pack(
                pady=3
            )

        hand_button = tk.Button(
            self.content_frame,
            text="自分の手札を見る",
            font=("Arial", 12),
            command=lambda: self.show_hand_screen(
                "question"
            )
        )

        hand_button.pack(
            pady=15
        )

    # =========================================================
    # 質問選択
    # =========================================================
    def select_question(
        self,
        question_number
    ):

        if self.waiting_for_server:
            return

        if question_number == 4:

            self.show_rank_input_screen()
            return

        if question_number == 5:

            self.show_number_input_screen(
                "more"
            )
            return

        if question_number == 6:

            self.show_number_input_screen(
                "less"
            )
            return

        question_names = {
            1: "偶数はある？",
            2: "奇数はある？",
            3: "絵札はある？",
            7: "スペードはある？",
            8: "ハートはある？",
            9: "ダイヤはある？",
            10: "クラブはある？",
            11: "JOKERはある？"
        }

        self.selected_question = (
            question_names.get(
                question_number
            )
        )

        data = {
            "type": "question",
            "question_id": question_number
        }

        self.send_json_to_server(
            data
        )

        self.show_sending_screen(
            "質問の回答を待っています..."
        )

    # =========================================================
    # ランク入力
    # =========================================================
    def show_rank_input_screen(self):

        self.clear_content_frame()

        self.message_label.config(
            text="指定するランクを入力してください"
        )

        title_label = tk.Label(
            self.content_frame,
            text="ランク指定",
            font=("Arial", 20, "bold")
        )

        title_label.pack(
            pady=15
        )

        explanation_label = tk.Label(
            self.content_frame,
            text="A / 2〜10 / J / Q / K",
            font=("Arial", 16)
        )

        explanation_label.pack(
            pady=20
        )

        self.rank_entry = tk.Entry(
            self.content_frame,
            font=("Arial", 18),
            width=10,
            justify="center"
        )

        self.rank_entry.pack(
            pady=10
        )

        decide_button = tk.Button(
            self.content_frame,
            text="決定",
            font=("Arial", 14),
            command=self.process_rank_question
        )

        decide_button.pack(
            pady=15
        )

        back_button = tk.Button(
            self.content_frame,
            text="戻る",
            font=("Arial", 12),
            command=self.show_question_screen
        )

        back_button.pack(
            pady=5
        )

    # =========================================================
    # ランク質問
    # =========================================================
    def process_rank_question(self):

        if self.waiting_for_server:
            return

        rank = (
            self.rank_entry
            .get()
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

            self.message_label.config(
                text=(
                    "A、2〜10、J、Q、Kの"
                    "どれかを入力してください"
                )
            )

            return

        self.selected_question = (
            f"{rank} はある？"
        )

        data = {
            "type": "question",
            "question_id": 4,
            "rank": rank
        }

        self.send_json_to_server(
            data
        )

        self.show_sending_screen(
            "質問の回答を待っています..."
        )

    # =========================================================
    # 数字入力
    # =========================================================
    def show_number_input_screen(
        self,
        question_type
    ):

        self.number_question_type = (
            question_type
        )

        self.clear_content_frame()

        self.message_label.config(
            text="指定する数字を入力してください"
        )

        title_label = tk.Label(
            self.content_frame,
            text="数字指定",
            font=("Arial", 20, "bold")
        )

        title_label.pack(
            pady=15
        )

        explanation_label = tk.Label(
            self.content_frame,
            text=(
                "1〜13を入力してください\n"
                "A=1 / J=11 / Q=12 / K=13"
            ),
            font=("Arial", 15)
        )

        explanation_label.pack(
            pady=20
        )

        self.number_entry = tk.Entry(
            self.content_frame,
            font=("Arial", 18),
            width=10,
            justify="center"
        )

        self.number_entry.pack(
            pady=10
        )

        decide_button = tk.Button(
            self.content_frame,
            text="決定",
            font=("Arial", 14),
            command=self.process_number_question
        )

        decide_button.pack(
            pady=15
        )

        back_button = tk.Button(
            self.content_frame,
            text="戻る",
            font=("Arial", 12),
            command=self.show_question_screen
        )

        back_button.pack(
            pady=5
        )

    # =========================================================
    # 数字質問
    # =========================================================
    def process_number_question(self):

        if self.waiting_for_server:
            return

        text = (
            self.number_entry
            .get()
            .strip()
        )

        try:

            number = int(text)

        except ValueError:

            self.message_label.config(
                text="数字を入力してください"
            )

            return

        if (
            number < 1
            or number > 13
        ):

            self.message_label.config(
                text="1〜13の範囲で入力してください"
            )

            return

        if self.number_question_type == "more":

            question_id = 5

            self.selected_question = (
                f"{number} 以上のカードはある？"
            )

        else:

            question_id = 6

            self.selected_question = (
                f"{number} 以下のカードはある？"
            )

        data = {
            "type": "question",
            "question_id": question_id,
            "number": number
        }

        self.send_json_to_server(
            data
        )

        self.show_sending_screen(
            "質問の回答を待っています..."
        )

    # =========================================================
    # 質問結果
    # =========================================================
    def show_question_result(
        self,
        question,
        answer
    ):

        self.waiting_for_server = False

        self.phase = "guess"

        self.selected_question = question
        self.last_question_answer = answer

        self.clear_content_frame()

        self.message_label.config(
            text="質問結果"
        )

        question_label = tk.Label(
            self.content_frame,
            text=question,
            font=("Arial", 18)
        )

        question_label.pack(
            pady=20
        )

        answer_text = (
            "はい"
            if answer
            else "いいえ"
        )

        answer_label = tk.Label(
            self.content_frame,
            text=answer_text,
            font=("Arial", 32, "bold")
        )

        answer_label.pack(
            pady=25
        )

        guess_button = tk.Button(
            self.content_frame,
            text="カードを予想する",
            font=("Arial", 14),
            width=18,
            command=self.show_guess_screen
        )

        guess_button.pack(
            pady=20
        )

        hand_button = tk.Button(
            self.content_frame,
            text="自分の手札を見る",
            font=("Arial", 12),
            command=lambda: self.show_hand_screen(
                "question_result"
            )
        )

        hand_button.pack(
            pady=5
        )

    # =========================================================
    # 予想画面
    # =========================================================
    def show_guess_screen(self):

        if not self.my_turn:
            return

        if self.phase != "guess":
            return

        self.clear_content_frame()

        self.message_label.config(
            text="相手のカードを1枚予想してください"
        )

        title_label = tk.Label(
            self.content_frame,
            text="カード予想",
            font=("Arial", 20, "bold")
        )

        title_label.pack(
            pady=15
        )

        suit_label = tk.Label(
            self.content_frame,
            text="スート",
            font=("Arial", 14)
        )

        suit_label.pack(
            pady=5
        )

        self.guess_suit = tk.StringVar(
            value=self.saved_guess_suit
        )

        suit_menu = tk.OptionMenu(
            self.content_frame,
            self.guess_suit,
            "スペード",
            "ハート",
            "ダイヤ",
            "クラブ",
            "JOKER"
        )

        suit_menu.config(
            font=("Arial", 13),
            width=12
        )

        suit_menu.pack(
            pady=5
        )

        rank_label = tk.Label(
            self.content_frame,
            text="ランク",
            font=("Arial", 14)
        )

        rank_label.pack(
            pady=5
        )

        self.guess_rank = tk.StringVar(
            value=self.saved_guess_rank
        )

        self.rank_menu = tk.OptionMenu(
            self.content_frame,
            self.guess_rank,
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
        )

        self.rank_menu.config(
            font=("Arial", 13),
            width=12
        )

        self.rank_menu.pack(
            pady=5
        )

        info_label = tk.Label(
            self.content_frame,
            text=(
                "JOKERを選んだ場合、"
                "ランクは使用しません"
            ),
            font=("Arial", 11)
        )

        info_label.pack(
            pady=10
        )

        self.guess_suit.trace_add(
            "write",
            self.update_rank_menu_state
        )

        self.update_rank_menu_state()

        guess_button = tk.Button(
            self.content_frame,
            text="このカードで予想する",
            font=("Arial", 14),
            command=self.process_guess
        )

        guess_button.pack(
            pady=20
        )

        hand_button = tk.Button(
            self.content_frame,
            text="自分の手札を見る",
            font=("Arial", 12),
            command=lambda: self.show_hand_screen(
                "guess"
            )
        )

        hand_button.pack(
            pady=5
        )

    # =========================================================
    # Joker時ランク無効
    # =========================================================
    def update_rank_menu_state(
        self,
        *args
    ):

        if self.guess_suit.get() == "JOKER":

            self.rank_menu.config(
                state="disabled"
            )

        else:

            self.rank_menu.config(
                state="normal"
            )

    # =========================================================
    # 予想送信
    # =========================================================
    def process_guess(self):

        if self.waiting_for_server:
            return

        if not self.my_turn:
            return

        if self.phase != "guess":
            return

        suit = self.guess_suit.get()
        rank = self.guess_rank.get()

        if suit == "JOKER":

            self.last_guess_text = "JOKER"

            data = {
                "type": "guess_card",
                "suit": "JOKER"
            }

        else:

            self.last_guess_text = (
                f"{suit} {rank}"
            )

            data = {
                "type": "guess_card",
                "suit": suit,
                "rank": rank
            }

        self.awaiting_guess_result = True
        self.showing_guess_result = False

        self.pending_turn_change = None
        self.pending_game_over = None

        self.send_json_to_server(
            data
        )

        self.show_sending_screen(
            "予想結果を待っています..."
        )

    # =========================================================
    # 予想結果
    # =========================================================
    def show_guess_result(
        self,
        is_correct,
        found_count
    ):

        self.awaiting_guess_result = False
        self.showing_guess_result = True

        self.waiting_for_server = False

        self.last_guess_result = is_correct
        self.found_count = found_count

        self.clear_content_frame()

        self.message_label.config(
            text="予想結果"
        )

        guess_label = tk.Label(
            self.content_frame,
            text=(
                f"予想：{self.last_guess_text}"
            ),
            font=("Arial", 18)
        )

        guess_label.pack(
            pady=15
        )

        if is_correct:

            result_text = "当たり！"

        else:

            result_text = "ハズレ！"

        result_label = tk.Label(
            self.content_frame,
            text=result_text,
            font=("Arial", 36, "bold")
        )

        result_label.pack(
            pady=25
        )

        found_label = tk.Label(
            self.content_frame,
            text=(
                f"現在 "
                f"{self.found_count}"
                " / 3 枚正解"
            ),
            font=("Arial", 18)
        )

        found_label.pack(
            pady=15
        )

        # 3枚正解なら説明変更
        if self.found_count >= 3:

            info_text = (
                "相手のカードを\n"
                "すべて当てました！"
            )

        else:

            info_text = (
                "予想結果を確認したら\n"
                "次へ進んでください。"
            )

        info_label = tk.Label(
            self.content_frame,
            text=info_text,
            font=("Arial", 14),
            justify="center"
        )

        info_label.pack(
            pady=10
        )

        self.next_button = tk.Button(
            self.content_frame,
            text="次へ",
            font=("Arial", 15),
            width=15,
            command=self.continue_after_guess_result
        )

        self.next_button.pack(
            pady=25
        )

        # サーバーから次の情報がまだ来ていない
        if (
            self.pending_turn_change is None
            and self.pending_game_over is None
        ):

            self.next_button.config(
                state="disabled"
            )

    # =========================================================
    # 予想結果後の「次へ」
    # =========================================================
    def continue_after_guess_result(self):

        # ========================================
        # 勝敗が決まった場合
        # ========================================
        if self.pending_game_over is not None:

            winner = self.pending_game_over[
                "winner"
            ]

            player1_hand = self.pending_game_over[
                "player1_hand"
            ]

            player2_hand = self.pending_game_over[
                "player2_hand"
            ]

            self.pending_game_over = None

            self.showing_guess_result = False

            self.show_game_over_screen(
                winner,
                player1_hand,
                player2_hand
            )

            return

        # ========================================
        # 通常のターン交代
        # ========================================
        if self.pending_turn_change is not None:

            your_turn, phase = (
                self.pending_turn_change
            )

            self.pending_turn_change = None

            self.showing_guess_result = False

            self.apply_turn_change(
                your_turn,
                phase
            )

    # =========================================================
    # ターン変更を受信
    # =========================================================
    def handle_turn_changed(
        self,
        your_turn,
        phase
    ):

        self.my_turn = your_turn
        self.phase = phase

        self.waiting_for_server = False

        if (
            self.awaiting_guess_result
            or self.showing_guess_result
        ):

            self.pending_turn_change = (
                your_turn,
                phase
            )

            self.enable_next_button()

            return

        self.apply_turn_change(
            your_turn,
            phase
        )

    # =========================================================
    # 実際のターン変更
    # =========================================================
    def apply_turn_change(
        self,
        your_turn,
        phase
    ):

        self.my_turn = your_turn
        self.phase = phase

        if self.my_turn:

            self.show_my_turn_screen()

        else:

            self.show_opponent_turn_screen()

    # =========================================================
    # game_over受信
    # =========================================================
    def handle_game_over(
        self,
        winner,
        player1_hand,
        player2_hand
    ):

        self.phase = "finished"

        game_over_data = {
            "winner": winner,
            "player1_hand": player1_hand,
            "player2_hand": player2_hand
        }

        # ========================================
        # 自分が予想した直後なら
        # 当たり画面を先に見せる
        # ========================================
        if (
            self.awaiting_guess_result
            or self.showing_guess_result
        ):

            self.pending_game_over = (
                game_over_data
            )

            self.enable_next_button()

            return

        # ========================================
        # 相手が勝った場合など
        # そのまま終了画面
        # ========================================
        self.show_game_over_screen(
            winner,
            player1_hand,
            player2_hand
        )

    # =========================================================
    # 次へボタン有効化
    # =========================================================
    def enable_next_button(self):

        try:

            if (
                self.next_button is not None
                and self.next_button.winfo_exists()
            ):

                self.next_button.config(
                    state="normal"
                )

        except tk.TclError:
            pass

    # =========================================================
    # ゲーム終了画面
    # =========================================================
    def show_game_over_screen(
        self,
        winner,
        player1_hand,
        player2_hand
    ):

        self.phase = "finished"

        self.waiting_for_server = False
        self.awaiting_guess_result = False
        self.showing_guess_result = False

        self.pending_turn_change = None
        self.pending_game_over = None

        self.clear_content_frame()

        self.message_label.config(
            text="ゲーム終了"
        )

        # ========================================
        # 勝敗表示
        # ========================================
        if winner == self.player_number:

            result_text = "あなたの勝ち！"

        else:

            result_text = "あなたの負けです"

        result_label = tk.Label(
            self.content_frame,
            text=result_text,
            font=("Arial", 30, "bold")
        )

        result_label.pack(
            pady=(5, 10)
        )

        winner_label = tk.Label(
            self.content_frame,
            text=f"Player {winner} の勝利",
            font=("Arial", 18)
        )

        winner_label.pack(
            pady=(0, 15)
        )

        # ========================================
        # Player 1
        # ========================================
        p1_title = tk.Label(
            self.content_frame,
            text="Player 1 の手札",
            font=("Arial", 16, "bold")
        )

        p1_title.pack(
            pady=(5, 5)
        )

        p1_frame = tk.Frame(
            self.content_frame
        )

        p1_frame.pack(
            pady=5
        )

        for card_text in player1_hand:

            card = self.text_to_card(
                card_text
            )

            if card is not None:

                widget = self.create_small_card_widget(
                    p1_frame,
                    card
                )

                widget.pack(
                    side="left",
                    padx=5
                )

        # ========================================
        # Player 2
        # ========================================
        p2_title = tk.Label(
            self.content_frame,
            text="Player 2 の手札",
            font=("Arial", 16, "bold")
        )

        p2_title.pack(
            pady=(15, 5)
        )

        p2_frame = tk.Frame(
            self.content_frame
        )

        p2_frame.pack(
            pady=5
        )

        for card_text in player2_hand:

            card = self.text_to_card(
                card_text
            )

            if card is not None:

                widget = self.create_small_card_widget(
                    p2_frame,
                    card
                )

                widget.pack(
                    side="left",
                    padx=5
                )

        # ========================================
        # 再戦
        # ========================================
        rematch_button = tk.Button(
            self.content_frame,
            text="もう一度遊ぶ",
            font=("Arial", 14),
            width=18,
            command=self.request_rematch
        )

        rematch_button.pack(
            pady=(25, 8)
        )

        # ========================================
        # 終了
        # ========================================
        leave_button = tk.Button(
            self.content_frame,
            text="終了",
            font=("Arial", 14),
            width=18,
            command=self.leave_game
        )

        leave_button.pack(
            pady=5
        )

    # =========================================================
    # 再戦希望
    # =========================================================
    def request_rematch(self):

        if self.phase != "finished":
            return

        data = {
            "type": "rematch_request"
        }

        self.send_json_to_server(
            data
        )

        self.show_rematch_waiting_screen()

    # =========================================================
    # 再戦待ち
    # =========================================================
    def show_rematch_waiting_screen(self):

        self.clear_content_frame()

        self.message_label.config(
            text="再戦待ち"
        )

        label = tk.Label(
            self.content_frame,
            text=(
                "再戦を希望しました！\n\n"
                "相手の選択を待っています..."
            ),
            font=("Arial", 20),
            justify="center"
        )

        label.pack(
            pady=60
        )

    # =========================================================
    # ゲーム終了
    # =========================================================
    def leave_game(self):

        data = {
            "type": "leave_game"
        }

        self.send_json_to_server(
            data
        )

        self.clear_content_frame()

        self.message_label.config(
            text="ゲームを終了しました"
        )

        label = tk.Label(
            self.content_frame,
            text=(
                "ゲームを終了しました。\n\n"
                "ウィンドウを閉じてください。"
            ),
            font=("Arial", 18),
            justify="center"
        )

        label.pack(
            pady=60
        )

    # =========================================================
    # 相手ターン
    # =========================================================
    def show_opponent_turn_screen(self):

        self.clear_content_frame()

        self.player_label.config(
            text=(f"Room {self.room_id} / Player {self.player_number}")
        )

        self.message_label.config(
            text="相手のターンです"
        )

        waiting_label = tk.Label(
            self.content_frame,
            text=(
                "相手が考えています...\n\n"
                "相手の操作を待っています。"
            ),
            font=("Arial", 20),
            justify="center"
        )

        waiting_label.pack(
            pady=50
        )

        found_label = tk.Label(
            self.content_frame,
            text=(
                f"現在 "
                f"{self.found_count}"
                " / 3 枚正解"
            ),
            font=("Arial", 15)
        )

        found_label.pack(
            pady=10
        )

        hand_button = tk.Button(
            self.content_frame,
            text="自分の手札を見る",
            font=("Arial", 12),
            command=lambda: self.show_hand_screen(
                "waiting"
            )
        )

        hand_button.pack(
            pady=20
        )

    # =========================================================
    # 自分のターン
    # =========================================================
    def show_my_turn_screen(self):

        self.clear_content_frame()

        self.player_label.config(
            text=(f"Room {self.room_id} / Player {self.player_number}")
        )

        self.message_label.config(
            text="あなたのターンです"
        )

        turn_label = tk.Label(
            self.content_frame,
            text="あなたのターンです！",
            font=("Arial", 24, "bold")
        )

        turn_label.pack(
            pady=30
        )

        found_label = tk.Label(
            self.content_frame,
            text=(
                f"現在 "
                f"{self.found_count}"
                " / 3 枚正解"
            ),
            font=("Arial", 16)
        )

        found_label.pack(
            pady=10
        )

        question_button = tk.Button(
            self.content_frame,
            text="質問を選ぶ",
            font=("Arial", 14),
            width=18,
            command=self.show_question_screen
        )

        question_button.pack(
            pady=25
        )

        hand_button = tk.Button(
            self.content_frame,
            text="自分の手札を見る",
            font=("Arial", 12),
            command=lambda: self.show_hand_screen(
                "question"
            )
        )

        hand_button.pack(
            pady=5
        )

    # =========================================================
    # 手札確認
    # =========================================================
    def show_hand_screen(
        self,
        return_screen
    ):

        self.clear_content_frame()

        self.message_label.config(
            text="あなたの手札"
        )

        title_label = tk.Label(
            self.content_frame,
            text="あなたの手札",
            font=("Arial", 20, "bold")
        )

        title_label.pack(
            pady=(10, 25)
        )

        cards_frame = tk.Frame(
            self.content_frame
        )

        cards_frame.pack(
            pady=10
        )

        for card in self.my_hand:

            card_widget = self.create_card_widget(
                cards_frame,
                card
            )

            card_widget.pack(
                side="left",
                padx=12
            )

        found_label = tk.Label(
            self.content_frame,
            text=(
                f"現在 "
                f"{self.found_count}"
                " / 3 枚正解"
            ),
            font=("Arial", 15)
        )

        found_label.pack(
            pady=15
        )

        back_button = tk.Button(
            self.content_frame,
            text="戻る",
            font=("Arial", 14),
            command=lambda: self.return_from_hand(
                return_screen
            )
        )

        back_button.pack(
            pady=20
        )

    # =========================================================
    # 手札から戻る
    # =========================================================
    def return_from_hand(
        self,
        return_screen
    ):

        if return_screen == "question":

            if self.my_turn:

                self.show_question_screen()

            else:

                self.show_opponent_turn_screen()

        elif return_screen == "question_result":

            self.show_question_result(
                self.selected_question,
                self.last_question_answer
            )

        elif return_screen == "guess":

            self.show_guess_screen()

        elif return_screen == "waiting":

            self.show_opponent_turn_screen()

    # =========================================================
    # 通信中
    # =========================================================
    def show_sending_screen(
        self,
        text
    ):

        self.waiting_for_server = True

        self.clear_content_frame()

        self.message_label.config(
            text=text
        )

        waiting_label = tk.Label(
            self.content_frame,
            text="通信中...",
            font=("Arial", 22, "bold")
        )

        waiting_label.pack(
            pady=60
        )

    # =========================================================
    # スート記号
    # =========================================================
    def get_suit_symbol(
        self,
        suit
    ):

        suit_symbols = {
            "スペード": "♠",
            "ハート": "♥",
            "ダイヤ": "♦",
            "クラブ": "♣"
        }

        return suit_symbols.get(
            suit,
            ""
        )

    # =========================================================
    # スート色
    # =========================================================
    def get_suit_color(
        self,
        suit
    ):

        if suit in [
            "ハート",
            "ダイヤ"
        ]:

            return "red"

        return "black"

    # =========================================================
    # 通常サイズカード
    # =========================================================
    def create_card_widget(
        self,
        parent,
        card
    ):

        card_frame = tk.Frame(
            parent,
            width=140,
            height=200,
            background="white",
            highlightbackground="black",
            highlightthickness=2
        )

        card_frame.pack_propagate(
            False
        )

        if card.is_joker():

            joker_label = tk.Label(
                card_frame,
                text="JOKER\n\n★",
                font=("Arial", 22, "bold"),
                background="white",
                foreground="black"
            )

            joker_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            return card_frame

        symbol = self.get_suit_symbol(
            card.suit
        )

        color = self.get_suit_color(
            card.suit
        )

        top_label = tk.Label(
            card_frame,
            text=f"{card.rank}\n{symbol}",
            font=("Arial", 15, "bold"),
            background="white",
            foreground=color
        )

        top_label.place(
            x=8,
            y=5
        )

        bottom_label = tk.Label(
            card_frame,
            text=f"{card.rank}\n{symbol}",
            font=("Arial", 15, "bold"),
            background="white",
            foreground=color
        )

        bottom_label.place(
            relx=1.0,
            rely=1.0,
            x=-8,
            y=-5,
            anchor="se"
        )

        if card.rank == "A":

            center_label = tk.Label(
                card_frame,
                text=symbol,
                font=("Arial", 50),
                background="white",
                foreground=color
            )

            center_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            return card_frame

        if card.rank in [
            "J",
            "Q",
            "K"
        ]:

            face_label = tk.Label(
                card_frame,
                text=f"{card.rank}\n{symbol}",
                font=("Arial", 38, "bold"),
                background="white",
                foreground=color
            )

            face_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            return card_frame

        number = int(
            card.rank
        )

        self.create_number_pips(
            card_frame,
            number,
            symbol,
            color
        )

        return card_frame

    # =========================================================
    # 終了画面用小さいカード
    # =========================================================
    def create_small_card_widget(
        self,
        parent,
        card
    ):

        card_frame = tk.Frame(
            parent,
            width=90,
            height=125,
            background="white",
            highlightbackground="black",
            highlightthickness=2
        )

        card_frame.pack_propagate(
            False
        )

        if card.is_joker():

            label = tk.Label(
                card_frame,
                text="JOKER\n★",
                font=("Arial", 14, "bold"),
                background="white"
            )

            label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            return card_frame

        symbol = self.get_suit_symbol(
            card.suit
        )

        color = self.get_suit_color(
            card.suit
        )

        label = tk.Label(
            card_frame,
            text=(
                f"{card.rank}\n"
                f"{symbol}"
            ),
            font=("Arial", 24, "bold"),
            background="white",
            foreground=color
        )

        label.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        return card_frame

    # =========================================================
    # 数字カードのマーク
    # =========================================================
    def create_number_pips(
        self,
        card_frame,
        number,
        symbol,
        color
    ):

        left = 0.30
        center = 0.50
        right = 0.70

        top = 0.22
        upper_middle = 0.36
        middle = 0.50
        lower_middle = 0.64
        bottom = 0.78

        pip_positions = {

            2: [
                (center, top),
                (center, bottom)
            ],

            3: [
                (center, top),
                (center, middle),
                (center, bottom)
            ],

            4: [
                (left, top),
                (right, top),
                (left, bottom),
                (right, bottom)
            ],

            5: [
                (left, top),
                (right, top),
                (center, middle),
                (left, bottom),
                (right, bottom)
            ],

            6: [
                (left, top),
                (right, top),
                (left, middle),
                (right, middle),
                (left, bottom),
                (right, bottom)
            ],

            7: [
                (left, top),
                (right, top),
                (center, upper_middle),
                (left, middle),
                (right, middle),
                (left, bottom),
                (right, bottom)
            ],

            8: [
                (left, top),
                (right, top),
                (center, upper_middle),
                (left, middle),
                (right, middle),
                (center, lower_middle),
                (left, bottom),
                (right, bottom)
            ],

            9: [
                (left, top),
                (right, top),
                (left, upper_middle),
                (right, upper_middle),
                (center, middle),
                (left, lower_middle),
                (right, lower_middle),
                (left, bottom),
                (right, bottom)
            ],

            10: [
                (left, top),
                (right, top),
                (center, 0.30),
                (left, upper_middle),
                (right, upper_middle),
                (left, lower_middle),
                (right, lower_middle),
                (center, 0.70),
                (left, bottom),
                (right, bottom)
            ]
        }

        positions = pip_positions.get(
            number,
            []
        )

        for x, y in positions:

            pip_label = tk.Label(
                card_frame,
                text=symbol,
                font=("Arial", 24),
                background="white",
                foreground=color
            )

            pip_label.place(
                relx=x,
                rely=y,
                anchor="center"
            )

    # =========================================================
    # 文字列 → Card
    # =========================================================
    def text_to_card(
        self,
        card_text
    ):

        if card_text == "JOKER":

            return Card(
                "JOKER"
            )

        parts = card_text.split()

        if len(parts) != 2:
            return None

        return Card(
            parts[0],
            parts[1]
        )

    # =========================================================
    # JSON送信
    # =========================================================
    def send_json_to_server(
        self,
        data
    ):

        if (
            self.websocket is None
            or self.event_loop is None
        ):

            self.show_server_error(
                "サーバーに接続されていません。"
            )

            return

        future = asyncio.run_coroutine_threadsafe(
            self.websocket.send(
                json.dumps(
                    data
                )
            ),
            self.event_loop
        )

        future.add_done_callback(
            self.check_send_result
        )

    # =========================================================
    # 送信エラー
    # =========================================================
    def check_send_result(
        self,
        future
    ):

        try:

            future.result()

        except Exception as error:

            self.root.after(
                0,
                self.show_server_error,
                str(error)
            )

    # =========================================================
    # ネットワーク開始
    # =========================================================
    def start_network(self):

        try:

            asyncio.run(
                self.connect_server()
            )

        except Exception as error:

            print(
                "ネットワークエラー：",
                error
            )

            self.root.after(
                0,
                self.show_connection_error,
                str(error)
            )

    # =========================================================
    # WebSocket
    # =========================================================
    async def connect_server(self):

        self.event_loop = (
            asyncio.get_running_loop()
        )

        uri = (
            f"ws://127.0.0.1:8000/ws/"
            f"{self.room_id}"
        )

        try:

            async with websockets.connect(
                uri
            ) as websocket:

                self.websocket = websocket

                self.root.after(
                    0,
                    self.show_waiting_screen
                )

                while True:

                    message = (
                        await websocket.recv()
                    )

                    data = json.loads(
                        message
                    )

                    print(
                        "サーバーから受信：",
                        data
                    )

                    message_type = data.get(
                        "type"
                    )

                    # =============================
                    # Player番号
                    # =============================
                    if message_type == "player_number":

                        self.player_number = (
                            data["player"]
                        )

                        self.room_id = data.get(
                            "room_id",
                            self.room_id
                        )

                        self.root.after(
                            0,
                            self.update_player_number
                        )

                    # =============================
                    # ゲーム開始
                    # =============================
                    elif message_type == "game_start":

                        self.player_number = (
                            data["player"]
                        )

                        self.my_turn = (
                            data["your_turn"]
                        )

                        self.phase = (
                            data["phase"]
                        )

                        # 再戦時もリセット
                        self.found_count = 0

                        self.waiting_for_server = False

                        self.awaiting_guess_result = False
                        self.showing_guess_result = False

                        self.pending_turn_change = None
                        self.pending_game_over = None

                        self.last_guess_text = None
                        self.last_guess_result = None

                        self.my_hand = []

                        for card_text in data[
                            "hand"
                        ]:

                            card = self.text_to_card(
                                card_text
                            )

                            if card is not None:

                                self.my_hand.append(
                                    card
                                )

                        self.root.after(
                            0,
                            self.show_game_start_screen
                        )

                    # =============================
                    # 質問結果
                    # =============================
                    elif message_type == "question_result":

                        question = data[
                            "question"
                        ]

                        answer = data[
                            "answer"
                        ]

                        self.root.after(
                            0,
                            self.show_question_result,
                            question,
                            answer
                        )

                    # =============================
                    # フェーズ変更
                    # =============================
                    elif message_type == "phase_changed":

                        self.phase = data[
                            "phase"
                        ]

                    # =============================
                    # 予想結果
                    # =============================
                    elif message_type == "guess_result":

                        is_correct = data[
                            "correct"
                        ]

                        found_count = data[
                            "found_count"
                        ]

                        self.root.after(
                            0,
                            self.show_guess_result,
                            is_correct,
                            found_count
                        )

                    # =============================
                    # ターン変更
                    # =============================
                    elif message_type == "turn_changed":

                        your_turn = data[
                            "your_turn"
                        ]

                        phase = data[
                            "phase"
                        ]

                        self.root.after(
                            0,
                            self.handle_turn_changed,
                            your_turn,
                            phase
                        )

                    # =============================
                    # ゲーム終了
                    # =============================
                    elif message_type == "game_over":

                        winner = data[
                            "winner"
                        ]

                        player1_hand = data[
                            "player1_hand"
                        ]

                        player2_hand = data[
                            "player2_hand"
                        ]

                        self.root.after(
                            0,
                            self.handle_game_over,
                            winner,
                            player1_hand,
                            player2_hand
                        )

                    # =============================
                    # 再戦待ち
                    # =============================
                    elif message_type == "rematch_waiting":

                        self.root.after(
                            0,
                            self.show_rematch_waiting_screen
                        )

                    # =============================
                    # 相手切断
                    # =============================
                    elif message_type == "opponent_disconnected":

                        self.root.after(
                            0,
                            self.handle_opponent_disconnected
                        )

                    # =============================
                    # 相手終了
                    # =============================
                    elif message_type == "opponent_left":

                        self.root.after(
                            0,
                            self.show_connection_error,
                            "相手がゲームを終了しました。"
                        )

                    # =============================
                    # エラー
                    # =============================
                    elif message_type == "error":

                        self.waiting_for_server = False

                        error_message = data.get(
                            "message",
                            "エラーが発生しました。"
                        )

                        self.root.after(
                            0,
                            self.show_server_error,
                            error_message
                        )

        except ConnectionClosed:

            self.websocket = None

            self.root.after(
                0,
                self.show_connection_error,
                "サーバーとの接続が終了しました。"
            )

    # =========================================================
    # Player番号
    # =========================================================
    def update_player_number(self):

        self.player_label.config(
            text=(
                f"Room {self.room_id} / "
                f"Player {self.player_number}"
            )
        )

        self.message_label.config(
            text="相手の接続を待っています..."
        )

    # =========================================================
    # サーバーエラー
    # =========================================================
    def show_server_error(
        self,
        message
    ):

        self.message_label.config(
            text=f"エラー：{message}"
        )

    # =========================================================
    # 相手切断
    # =========================================================
    def handle_opponent_disconnected(self):

        # 対戦状態を初期化して、
        # 同じルームで新しい相手を待つ
        self.my_turn = False
        self.phase = "waiting"

        self.my_hand = []
        self.found_count = 0

        self.selected_question = None
        self.number_question_type = None
        self.last_question_answer = None

        self.last_guess_text = None
        self.last_guess_result = None

        self.awaiting_guess_result = False
        self.showing_guess_result = False

        self.pending_turn_change = None
        self.pending_game_over = None

        self.waiting_for_server = False

        self.clear_content_frame()

        self.player_label.config(
            text=(
                f"Room {self.room_id} / "
                f"Player {self.player_number}"
            )
        )

        self.message_label.config(
            text="相手が切断しました"
        )

        room_label = tk.Label(
            self.content_frame,
            text=f"ルームID：{self.room_id}",
            font=("Arial", 28, "bold")
        )

        room_label.pack(
            pady=(30, 15)
        )

        info_label = tk.Label(
            self.content_frame,
            text=(
                "相手が切断しました。\n\n"
                "あなたの接続はそのままです。\n"
                "同じルームIDで新しい相手を\n"
                "待っています..."
            ),
            font=("Arial", 18),
            justify="center"
        )

        info_label.pack(
            pady=20
        )

    # =========================================================
    # 接続終了
    # =========================================================
    def show_connection_error(
        self,
        message
    ):

        self.clear_content_frame()

        self.player_label.config(
            text="接続終了"
        )

        self.message_label.config(
            text=message
        )

        error_label = tk.Label(
            self.content_frame,
            text=message,
            font=("Arial", 16),
            justify="center"
        )

        error_label.pack(
            pady=50
        )

    # =========================================================
    # content_frameを空にする
    # =========================================================
    def clear_content_frame(self):

        for widget in (
            self.content_frame
            .winfo_children()
        ):

            widget.destroy()


# =============================================================
# 実行
# =============================================================
def main():

    root = tk.Tk()

    app = OnlineGameGUI(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()