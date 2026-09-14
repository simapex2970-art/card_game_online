class Card:

    rank_values = {
        "A": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "J": 11,
        "Q": 12,
        "K": 13
    }

    def __init__(self, suit, rank=None):
        self.suit = suit
        self.rank = rank


    # =========================
    # JOKERかどうか
    # =========================

    def is_joker(self):

        return self.suit == "JOKER"


    # =========================
    # カードの数字を取得
    # =========================

    def get_value(self):

        if self.is_joker():
            return None

        return self.rank_values[
            self.rank
        ]


    # =========================
    # 絵札かどうか
    # =========================

    def is_face(self):

        if self.is_joker():
            return False

        return self.rank in [
            "J",
            "Q",
            "K"
        ]


    # =========================
    # printしたときの表示
    # =========================

    def __str__(self):

        if self.is_joker():
            return "JOKER"

        return (
            f"{self.suit} {self.rank}"
        )


    # =========================
    # カード同士の比較
    # =========================

    def __eq__(self, other):

        if not isinstance(other, Card):
            return False

        return (
            self.suit == other.suit
            and
            self.rank == other.rank
        )


    # =========================
    # setでも使えるようにする
    # =========================

    def __hash__(self):

        return hash(
            (
                self.suit,
                self.rank
            )
        )