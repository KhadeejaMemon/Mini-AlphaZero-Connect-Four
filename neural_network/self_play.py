import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import numpy as np
import torch

from game.connect_four import ConnectFour
from agents.neural_mcts import NeuralMCTSAI
from neural_network.model import AlphaZeroCNN


def generate_self_play_data(
    model,
    num_games=20,
    simulations=50,
    temperature_moves=8,
    augment=True,
    save_path=None
):

    agent = NeuralMCTSAI(
        model=model,
        simulations=simulations,
        add_noise=True
    )

    training_data = []

    for game_number in range(num_games):

        game = ConnectFour()
        history = []
        move_count = 0

        while not game.game_over:

            player = game.current_player

            # Shuru ki moves mein exploration, baad mein greedy
            temperature = 1.0 if move_count < temperature_moves else 0.0

            move, policy = agent.search_policy(
                game,
                temperature=temperature,
                add_noise=True
            )

            state = (game.board * player).astype(np.float32)

            history.append(
                (state, policy.astype(np.float32), player)
            )

            game.make_move(move)
            move_count += 1

        winner = game.winner

        for state, policy, player in history:

            value = 0.0 if winner == 0 else float(winner * player)

            samples = [(state, policy)]

            if augment:
                # Board ko left-right flip karna (data double)
                samples.append(
                    (state[:, ::-1].copy(), policy[::-1].copy())
                )

            for s, p in samples:
                training_data.append((
                    torch.from_numpy(s).unsqueeze(0),
                    torch.from_numpy(p),
                    torch.tensor([value], dtype=torch.float32)
                ))

        print(
            f"  Self-play game {game_number + 1}/{num_games} | "
            f"winner: {winner} | moves: {len(history)}"
        )

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        torch.save(training_data, save_path)

    return training_data


if __name__ == "__main__":

    model = AlphaZeroCNN()

    data = generate_self_play_data(
        model,
        num_games=5,
        simulations=50,
        save_path="results/self_play_data.pt"
    )

    print("Total samples:", len(data))