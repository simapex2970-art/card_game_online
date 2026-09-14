import random
import os

from card import Card
from player import Player
from question_manager import QuestionManager


class Game:

    def __init__(self):

        # =========================
        # 基本データ
        # =========================

        self.suits = [
            "スペード",
            "ハート",
            "ダイヤ",
            "クラブ"
        ]

        self.ranks = [
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

        # =========================
        # プレイヤー
        # =========================

        self.player1 = Player(
            "プレイヤー1"
        )

        self.player2 = Player(
            "プレイヤー2"
        )

        # =========================
        # 質問管理
        # =========================

        self.question_manager = (
            QuestionManager()
        )

        # =========================
        # デッキ
        # =========================

        self.deck = []

        self.create_deck()
        self.deal_cards()


    # =========================
    # 画面クリア
    # =========================

    def clear_screen(self):

        # Windows
        if os.name == "nt":

            command = "cls"

        # macOS / Linux
        else:

            command = "clear"

        result = os.system(
            command
        )

        # 画面クリアが使えない環境
        if result != 0:

            print(
                "\n" * 50
            )


    # =========================
    # デッキ作成
    # =========================

    def create_deck(self):

        self.deck = []

        for suit in self.suits:

            for rank in self.ranks:

                card = Card(
                    suit,
                    rank
                )

                self.deck.append(
                    card
                )

        # JOKERを1枚追加
        self.deck.append(
            Card("JOKER")
        )

        random.shuffle(
            self.deck
        )


    # =========================
    # カード配布
    # =========================

    def deal_cards(self):

        for _ in range(3):

            self.player1.add_card(
                self.deck.pop()
            )

            self.player2.add_card(
                self.deck.pop()
            )


    # =========================
    # スート入力の整理
    # =========================

    def normalize_suit(
        self,
        text
    ):

        text = (
            text
            .strip()
            .lower()
        )

        suit_names = {
            "スペード": "スペード",
            "spade": "スペード",
            "s": "スペード",

            "ハート": "ハート",
            "heart": "ハート",
            "h": "ハート",

            "ダイヤ": "ダイヤ",
            "ダイヤモンド": "ダイヤ",
            "diamond": "ダイヤ",
            "d": "ダイヤ",

            "クラブ": "クラブ",
            "club": "クラブ",
            "c": "クラブ",

            "joker": "JOKER",
            "ジョーカー": "JOKER"
        }

        return suit_names.get(
            text
        )


    # =========================
    # ランク入力
    # =========================

    def input_rank(self):

        while True:

            rank = input(
                "数字"
                "（A・2～10・J・Q・K）: "
            )

            rank = (
                rank
                .strip()
                .upper()
            )

            if rank in self.ranks:

                return rank

            print()
            print(
                "入力が正しくありません。"
            )
            print(
                "A・2～10・J・Q・K"
                "から選んでください。"
            )


    # =========================
    # 数字入力
    # =========================

    def input_number(self):

        while True:

            value = input(
                "数字（1～13）: "
            ).strip()

            try:

                number = int(
                    value
                )

            except ValueError:

                print()
                print(
                    "整数を入力してください。"
                )

                continue

            if 1 <= number <= 13:

                return number

            print()
            print(
                "1～13の数字を"
                "入力してください。"
            )


    # =========================
    # 手札表示
    # =========================

    def show_hand(
        self,
        player
    ):

        print()
        print(
            "========== あなたの手札 =========="
        )

        for card in player.hand:

            print(
                card
            )

        print(
            "================================"
        )


    # =========================
    # 質問メニュー
    # =========================

    def ask_question(
        self,
        player,
        opponent
    ):

        while True:

            print()
            print(
                "========== 質問メニュー =========="
            )

            print()
            print("【数字系】")
            print(" 1. 偶数はある？")
            print(" 2. 奇数はある？")
            print(" 3. 絵札はある？")
            print(" 4. 指定した数字はある？")
            print(" 5. 指定した数字以上はある？")
            print(" 6. 指定した数字以下はある？")

            print()
            print("【スート系】")
            print(" 7. スペードはある？")
            print(" 8. ハートはある？")
            print(" 9. ダイヤはある？")
            print("10. クラブはある？")

            print()
            print("【特殊】")
            print("11. ジョーカーはある？")

            print()
            print(
                "================================"
            )

            choice = input(
                "質問番号"
                "（1～11）: "
            ).strip()

            # =====================
            # 偶数
            # =====================

            if choice == "1":

                print()
                print(
                    "質問：偶数はある？"
                )

                return (
                    self.question_manager
                    .ask_even(
                        opponent.hand,
                        player.found_cards
                    )
                )

            # =====================
            # 奇数
            # =====================

            if choice == "2":

                print()
                print(
                    "質問：奇数はある？"
                )

                return (
                    self.question_manager
                    .ask_odd(
                        opponent.hand,
                        player.found_cards
                    )
                )

            # =====================
            # 絵札
            # =====================

            if choice == "3":

                print()
                print(
                    "質問：絵札はある？"
                )

                return (
                    self.question_manager
                    .ask_face(
                        opponent.hand,
                        player.found_cards
                    )
                )

            # =====================
            # 指定ランク
            # =====================

            if choice == "4":

                rank = (
                    self.input_rank()
                )

                print()
                print(
                    f"質問：{rank}はある？"
                )

                return (
                    self.question_manager
                    .ask_rank(
                        opponent.hand,
                        player.found_cards,
                        rank
                    )
                )

            # =====================
            # 以上
            # =====================

            if choice == "5":

                number = (
                    self.input_number()
                )

                print()
                print(
                    f"質問：{number}以上のカードはある？"
                )

                return (
                    self.question_manager
                    .ask_more_than(
                        opponent.hand,
                        player.found_cards,
                        number
                    )
                )

            # =====================
            # 以下
            # =====================

            if choice == "6":

                number = (
                    self.input_number()
                )

                print()
                print(
                    f"質問：{number}以下のカードはある？"
                )

                return (
                    self.question_manager
                    .ask_less_than(
                        opponent.hand,
                        player.found_cards,
                        number
                    )
                )

            # =====================
            # スペード
            # =====================

            if choice == "7":

                print()
                print(
                    "質問：スペードはある？"
                )

                return (
                    self.question_manager
                    .ask_suit(
                        opponent.hand,
                        player.found_cards,
                        "スペード"
                    )
                )

            # =====================
            # ハート
            # =====================

            if choice == "8":

                print()
                print(
                    "質問：ハートはある？"
                )

                return (
                    self.question_manager
                    .ask_suit(
                        opponent.hand,
                        player.found_cards,
                        "ハート"
                    )
                )

            # =====================
            # ダイヤ
            # =====================

            if choice == "9":

                print()
                print(
                    "質問：ダイヤはある？"
                )

                return (
                    self.question_manager
                    .ask_suit(
                        opponent.hand,
                        player.found_cards,
                        "ダイヤ"
                    )
                )

            # =====================
            # クラブ
            # =====================

            if choice == "10":

                print()
                print(
                    "質問：クラブはある？"
                )

                return (
                    self.question_manager
                    .ask_suit(
                        opponent.hand,
                        player.found_cards,
                        "クラブ"
                    )
                )

            # =====================
            # JOKER
            # =====================

            if choice == "11":

                print()
                print(
                    "質問：ジョーカーはある？"
                )

                return (
                    self.question_manager
                    .ask_joker(
                        opponent.hand,
                        player.found_cards
                    )
                )

            print()
            print(
                "入力が正しくありません。"
            )
            print(
                "1～11から選んでください。"
            )


    # =========================
    # カード予想入力
    # =========================

    def input_guess(self):

        while True:

            suit = input(
                "マーク"
                "（スペード・ハート・"
                "ダイヤ・クラブ・JOKER）: "
            )

            suit = (
                self.normalize_suit(
                    suit
                )
            )

            if suit is None:

                print()
                print(
                    "入力が正しくありません。"
                )

                continue

            # ---------------------
            # JOKER
            # ---------------------

            if suit == "JOKER":

                return Card(
                    "JOKER"
                )

            # ---------------------
            # 普通のカード
            # ---------------------

            rank = (
                self.input_rank()
            )

            return Card(
                suit,
                rank
            )


    # =========================
    # カード予想判定
    # =========================

    def guess_card(
        self,
        player,
        opponent,
        guess
    ):

        # すでに当てている
        if guess in player.found_cards:

            return False

        # 相手の手札に存在
        if guess in opponent.hand:

            player.add_found_card(
                guess
            )

            return True

        return False


    # =========================
    # 1ターン
    # =========================

    def player_turn(
        self,
        player,
        opponent
    ):

        self.clear_screen()

        print(
            "=============================="
        )
        print(
            f"      {player.name} のターン"
        )
        print(
            "=============================="
        )

        # 自分の手札
        self.show_hand(
            player
        )

        print()

        input(
            "自分の手札を確認したら"
            "Enterキーを押してください。"
        )

        # =====================
        # 質問
        # =====================

        print()
        print(
            "========== 質問 =========="
        )

        question_result = (
            self.ask_question(
                player,
                opponent
            )
        )

        print()

        if question_result:

            print(
                "答え：はい"
            )

        else:

            print(
                "答え：いいえ"
            )

        # =====================
        # カード予想
        # =====================

        print()
        print(
            "========== カード予想 =========="
        )

        print(
            "相手のカードを"
            "1枚予想してください。"
        )

        guess = (
            self.input_guess()
        )

        result = (
            self.guess_card(
                player,
                opponent,
                guess
            )
        )

        print()

        if result:

            print(
                "当たり！"
            )

        else:

            print(
                "ハズレ！"
            )

        print()

        print(
            f"現在 "
            f"{len(player.found_cards)}"
            f" / 3 枚正解"
        )


    # =========================
    # プレイヤー交代
    # =========================

    def change_player(
        self,
        next_player
    ):

        print()

        input(
            f"{next_player.name}に交代します。"
            "Enterキーを押してください。"
        )

        self.clear_screen()


    # =========================
    # 勝者表示
    # =========================

    def show_winner(
        self,
        winner
    ):

        print()
        print(
            "=============================="
        )
        print(
            f"      {winner.name} の勝ち！"
        )
        print(
            "=============================="
        )


    # =========================
    # 最終手札
    # =========================

    def show_final_hands(self):

        print()
        print(
            "========== 最終手札 =========="
        )

        print()
        print(
            f"{self.player1.name}の手札"
        )

        for card in self.player1.hand:

            print(
                card
            )

        print()
        print(
            f"{self.player2.name}の手札"
        )

        for card in self.player2.hand:

            print(
                card
            )

        print()
        print(
            "=============================="
        )


    # =========================
    # ゲーム開始
    # =========================

    def start(self):

        self.clear_screen()

        print(
            "=============================="
        )
        print(
            "      カード推理ゲーム"
        )
        print(
            "=============================="
        )

        print()
        print(
            "相手の3枚のカードを先に"
        )
        print(
            "すべて当てたプレイヤーの勝ちです。"
        )

        print()

        input(
            "Enterキーでゲーム開始"
        )

        # =========================
        # ゲームループ
        # =========================

        while True:

            # -------------------------
            # プレイヤー1
            # -------------------------

            self.player_turn(
                self.player1,
                self.player2
            )

            if (
                self.player1
                .is_winner()
            ):

                self.show_winner(
                    self.player1
                )

                break

            self.change_player(
                self.player2
            )

            # -------------------------
            # プレイヤー2
            # -------------------------

            self.player_turn(
                self.player2,
                self.player1
            )

            if (
                self.player2
                .is_winner()
            ):

                self.show_winner(
                    self.player2
                )

                break

            self.change_player(
                self.player1
            )

        # =========================
        # ゲーム終了
        # =========================

        self.show_final_hands()

        print()
        print(
            "ゲームを終了します。"
        )