
import math


class MinimaxAI:

    def __init__(self, depth=3):
        self.depth = depth

    def get_move(self, game):

        valid_moves = game.get_valid_moves()

        if not valid_moves:
            return None

        best_score = -math.inf
        best_move = valid_moves[0]

        for col in valid_moves:

            temp = game.board.copy()
            row = self.get_next_open_row(temp, col)

            temp[row][col] = game.current_player

            score = self.minimax(
                temp,
                self.depth - 1,
                False,
                game.current_player
            )

            if score > best_score:
                best_score = score
                best_move = col

        return best_move

    def get_next_open_row(self, board, col):

        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row

    def minimax(self, board, depth, maximizing, player):

        valid_moves = [
            col for col in range(7)
            if board[0][col] == 0
        ]

        if self.check_winner(board, player):
            return 100000 + depth

        if self.check_winner(board, -player):
            return -100000 - depth

        if depth == 0 or not valid_moves:
            return self.evaluate_board(board, player)

        if maximizing:

            value = -math.inf

            for col in valid_moves:

                row = self.get_next_open_row(board, col)
                new_board = board.copy()
                new_board[row][col] = player

                value = max(
                    value,
                    self.minimax(
                        new_board, depth - 1, False, player
                    )
                )

            return value

        else:

            value = math.inf

            for col in valid_moves:

                row = self.get_next_open_row(board, col)
                new_board = board.copy()
                new_board[row][col] = -player

                value = min(
                    value,
                    self.minimax(
                        new_board, depth - 1, True, player
                    )
                )

            return value

    def check_winner(self, board, player):

        for row in range(6):
            for col in range(7):

                if board[row][col] != player:
                    continue

                directions = [
                    (0, 1), (1, 0),
                    (1, 1), (1, -1)
                ]

                for dr, dc in directions:

                    count = 0

                    for i in range(4):

                        r = row + dr * i
                        c = col + dc * i

                        if (
                            0 <= r < 6
                            and 0 <= c < 7
                            and board[r][c] == player
                        ):
                            count += 1

                    if count == 4:
                        return True

        return False

    def evaluate_board(self, board, player):

        score = 0

        # Center column preference
        score += sum(
            1 for row in range(6)
            if board[row][3] == player
        ) * 3

        # Evaluate groups of four
        for row in range(6):
            for col in range(7):

                directions = [
                    (0, 1), (1, 0),
                    (1, 1), (1, -1)
                ]

                for dr, dc in directions:

                    cells = []

                    for i in range(4):

                        r = row + dr * i
                        c = col + dc * i

                        if 0 <= r < 6 and 0 <= c < 7:
                            cells.append(board[r][c])

                    if len(cells) == 4:

                        own = cells.count(player)
                        opponent = cells.count(-player)

                        if opponent == 0:
                            score += [0, 1, 10, 50, 100][own]

                        if own == 0:
                            score -= [0, 1, 10, 50, 100][opponent]

        return score
