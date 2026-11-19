import math
import random

from game.utils import drop_piece, wins_at


class MCTSNode:

    def __init__(self, board, player, parent=None, move=None, terminal=None):

        self.board = board
        self.player = player          # jis ki baari hai
        self.parent = parent
        self.move = move

        self.player_just_moved = (
            -player if parent is not None else None
        )

        # None = game jaari, 0 = draw, 1/-1 = winner
        self.terminal = terminal

        self.children = []
        self.visits = 0
        self.wins = 0

        if terminal is None:
            self.untried_moves = [
                col for col in range(7) if board[0][col] == 0
            ]
        else:
            self.untried_moves = []


class MCTSAI:

    def __init__(self, simulations=100):
        self.simulations = simulations

    def get_move(self, game):

        valid_moves = game.get_valid_moves()

        if not valid_moves:
            return None

        root = MCTSNode(game.board.copy(), game.current_player)

        for _ in range(self.simulations):

            node = root

            # Selection
            while not node.untried_moves and node.children:
                node = self.select_child(node)

            # Expansion
            if node.untried_moves:

                move = random.choice(node.untried_moves)
                node.untried_moves.remove(move)

                new_board = node.board.copy()
                row = drop_piece(new_board, move, node.player)

                terminal = None
                if wins_at(new_board, row, move, node.player):
                    terminal = node.player
                elif not (new_board[0] == 0).any():
                    terminal = 0

                child = MCTSNode(
                    new_board, -node.player, node, move, terminal
                )
                node.children.append(child)
                node = child

            # Simulation
            if node.terminal is not None:
                winner = node.terminal
            else:
                winner = self.simulate(node.board, node.player)

            # Backpropagation
            while node is not None:

                node.visits += 1

                if node.player_just_moved is not None:
                    if winner == node.player_just_moved:
                        node.wins += 1
                    elif winner == 0:
                        node.wins += 0.5

                node = node.parent

        if not root.children:
            return None

        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move

    def select_child(self, node):

        return max(
            node.children,
            key=lambda child:
            (child.wins / child.visits)
            + math.sqrt(2 * math.log(node.visits) / child.visits)
        )

    def simulate(self, board, player):

        board = board.copy()

        while True:

            valid_moves = [c for c in range(7) if board[0][c] == 0]

            if not valid_moves:
                return 0

            move = random.choice(valid_moves)
            row = drop_piece(board, move, player)

            if wins_at(board, row, move, player):
                return player

            player = -player