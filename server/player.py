class Player:

    def __init__(self, name):

        # プレイヤー名
        self.name = name

        # 自分の手札
        self.hand = []

        # 自分が当てた相手のカード
        self.found_cards = []


    # =========================
    # 手札にカードを追加
    # =========================

    def add_card(self, card):

        self.hand.append(card)


    # =========================
    # 正解カードを追加
    # =========================

    def add_found_card(self, card):

        # 同じカードを
        # 2回追加しない
        if card not in self.found_cards:

            self.found_cards.append(
                card
            )


    # =========================
    # 勝利判定
    # =========================

    def is_winner(self):

        return (
            len(self.found_cards) >= 3
        )