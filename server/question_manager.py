class QuestionManager:

    # =========================
    # まだ当てられていないカード
    # =========================

    def get_remaining_cards(
        self,
        hand,
        found_cards
    ):

        remaining_cards = []

        for card in hand:

            if card not in found_cards:

                remaining_cards.append(
                    card
                )

        return remaining_cards


    # =========================
    # 偶数
    # =========================

    def ask_even(
        self,
        hand,
        found_cards
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                continue

            value = card.get_value()

            if value % 2 == 0:
                return True

        return False


    # =========================
    # 奇数
    # =========================

    def ask_odd(
        self,
        hand,
        found_cards
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                continue

            value = card.get_value()

            if value % 2 == 1:
                return True

        return False


    # =========================
    # 絵札
    # =========================

    def ask_face(
        self,
        hand,
        found_cards
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_face():
                return True

        return False


    # =========================
    # 指定ランク
    # =========================

    def ask_rank(
        self,
        hand,
        found_cards,
        question_rank
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                continue

            if card.rank == question_rank:
                return True

        return False


    # =========================
    # 指定した数字以上
    # =========================

    def ask_more_than(
        self,
        hand,
        found_cards,
        number
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                continue

            if card.get_value() >= number:
                return True

        return False


    # =========================
    # 指定した数字以下
    # =========================

    def ask_less_than(
        self,
        hand,
        found_cards,
        number
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                continue

            if card.get_value() <= number:
                return True

        return False


    # =========================
    # スート
    # =========================

    def ask_suit(
        self,
        hand,
        found_cards,
        question_suit
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                continue

            if card.suit == question_suit:
                return True

        return False


    # =========================
    # JOKER
    # =========================

    def ask_joker(
        self,
        hand,
        found_cards
    ):

        cards = self.get_remaining_cards(
            hand,
            found_cards
        )

        for card in cards:

            if card.is_joker():
                return True

        return False