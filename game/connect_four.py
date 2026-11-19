
import numpy as np


class ConnectFour:

    ROWS = 6
    COLS = 7
    CONNECT = 4

    def __init__(self):
        self.board = np.zeros(
            (self.ROWS, self.COLS),
            dtype=int
        )
        self.current_player = 1
        self.game_over = False
        self.winner = None

    def get_valid_moves(self):
        return [
            col for col in range(self.COLS)
            if self.board[0][col] == 0
        ]

    def make_move(self, col):

        if self.game_over:
            return False

        if col not in self.get_valid_moves():
            return False

        for row in range(self.ROWS - 1, -1, -1):

            if self.board[row][col] == 0:

                self.board[row][col] = self.current_player

                if self.check_winner(
                    row, col, self.current_player
                ):
                    self.game_over = True
                    self.winner = self.current_player

                elif not self.get_valid_moves():
                    self.game_over = True
                    self.winner = 0

                else:
                    self.current_player *= -1

                return True

        return False

    def check_winner(self, row, col, player):

        directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1)
        ]

        for dr, dc in directions:

            count = 1

            for direction in [1, -1]:

                r = row + dr * direction
                c = col + dc * direction

                while (
                    0 <= r < self.ROWS
                    and 0 <= c < self.COLS
                    and self.board[r][c] == player
                ):
                    count += 1
                    r += dr * direction
                    c += dc * direction

            if count >= self.CONNECT:
                return True

        return False

    def reset(self):

        self.board = np.zeros(
            (self.ROWS, self.COLS),
            dtype=int
        )

        self.current_player = 1
        self.game_over = False
        self.winner = None

    def display(self):

        print(self.board)
        print("0 1 2 3 4 5 6")
