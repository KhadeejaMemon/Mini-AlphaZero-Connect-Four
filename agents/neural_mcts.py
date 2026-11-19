import math
import numpy as np
import torch

from neural_network.model import AlphaZeroCNN
from game.utils import drop_piece, wins_at


class NeuralMCTSNode:

    def __init__(
        self, board, player, prior=1.0,
        parent=None, move=None, terminal_value=None
    ):
        self.board = board
        self.player = player              # jis ki baari hai
        self.prior = prior
        self.parent = parent
        self.move = move

        # Is node ki value, node ke player ke nazariye se (terminal ho to)
        self.terminal_value = terminal_value

        self.children = {}
        self.visits = 0
        self.value_sum = 0.0

    def get_value(self):
        if self.visits == 0:
            return 0.0
        return self.value_sum / self.visits


class NeuralMCTSAI:

    def __init__(
        self,
        model_path="results/models/connect4_model.pth",
        simulations=100,
        c_puct=1.5,
        model=None,
        add_noise=False,
        dirichlet_alpha=1.0,
        noise_eps=0.25,
        temperature=0.0
    ):

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        if model is None:
            self.model = AlphaZeroCNN().to(self.device)
            checkpoint = torch.load(
                model_path,
                map_location=self.device,
                weights_only=True
            )
            self.model.load_state_dict(checkpoint)
        else:
            self.model = model.to(self.device)

        self.model.eval()

        self.simulations = simulations
        self.c_puct = c_puct
        self.add_noise = add_noise
        self.dirichlet_alpha = dirichlet_alpha
        self.noise_eps = noise_eps
        self.temperature = temperature

    # ---------- Network ----------

    def predict(self, board, player):

        state = torch.tensor(
            board * player, dtype=torch.float32
        ).unsqueeze(0).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits, value = self.model(state)

        policy = torch.softmax(logits[0], dim=0).cpu().numpy()
        return policy, float(value.item())

    # ---------- Search ----------

    def search(self, game, add_noise=False):

        root = NeuralMCTSNode(
            game.board.copy(),
            game.current_player
        )

        self.expand(root)

        if add_noise:
            self.add_dirichlet_noise(root)

        for _ in range(self.simulations):

            node = root

            # Selection
            while node.children:
                node = self.select_child(node)

            # Evaluation / Expansion
            if node.terminal_value is not None:
                value = node.terminal_value
            else:
                value = self.expand(node)

            # Backpropagation
            while node is not None:
                node.visits += 1
                node.value_sum += value
                value = -value
                node = node.parent

        return root

    def search_policy(self, game, temperature=0.0, add_noise=False):
        """(move, visit-count policy) return karta hai."""

        if not game.get_valid_moves():
            return None, None

        root = self.search(game, add_noise)

        visits = np.zeros(7, dtype=np.float64)
        for move, child in root.children.items():
            visits[move] = child.visits

        policy = visits / visits.sum()

        if temperature <= 1e-6:
            move = int(np.argmax(visits))
        else:
            scaled = visits ** (1.0 / temperature)
            scaled /= scaled.sum()
            move = int(np.random.choice(7, p=scaled))

        return move, policy

    def get_move(self, game):

        move, _ = self.search_policy(
            game,
            temperature=self.temperature,
            add_noise=self.add_noise
        )
        return move

    def add_dirichlet_noise(self, root):

        moves = list(root.children.keys())

        if not moves:
            return

        noise = np.random.dirichlet(
            [self.dirichlet_alpha] * len(moves)
        )

        for move, n in zip(moves, noise):
            child = root.children[move]
            child.prior = (
                (1 - self.noise_eps) * child.prior
                + self.noise_eps * float(n)
            )

    def select_child(self, node):

        best_score = float("-inf")
        best_child = None

        for child in node.children.values():

            q_value = -child.get_value()

            exploration = (
                self.c_puct
                * child.prior
                * math.sqrt(node.visits + 1)
                / (1 + child.visits)
            )

            score = q_value + exploration

            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def expand(self, node):
        """Node expand karta hai aur network ki value return karta hai."""

        valid_moves = self.get_valid_moves(node.board)

        policy, value = self.predict(node.board, node.player)

        probabilities = np.array(
            [policy[m] for m in valid_moves], dtype=np.float64
        )

        total = probabilities.sum()

        if total <= 0:
            probabilities = np.ones(len(valid_moves)) / len(valid_moves)
        else:
            probabilities /= total

        for move, probability in zip(valid_moves, probabilities):

            new_board = node.board.copy()
            row = drop_piece(new_board, move, node.player)

            terminal = None
            if wins_at(new_board, row, move, node.player):
                terminal = -1.0       # child ka player haar chuka hai
            elif not (new_board[0] == 0).any():
                terminal = 0.0

            node.children[move] = NeuralMCTSNode(
                new_board,
                -node.player,
                prior=float(probability),
                parent=node,
                move=move,
                terminal_value=terminal
            )

        return value

    def get_valid_moves(self, board):
        return [c for c in range(7) if board[0][c] == 0]