import os
import sys
import csv

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import time
import torch

from game.arena import play_match
from agents.random_ai import RandomAI
from agents.mcts import MCTSAI
from agents.neural_mcts import NeuralMCTSAI
from neural_network.model import AlphaZeroCNN

from self_play import generate_self_play_data
from train import train_model


def evaluate(model, eval_sims, eval_pairs):

    agent = NeuralMCTSAI(model=model, simulations=eval_sims)

    vs_random = play_match(agent, RandomAI(), num_pairs=eval_pairs)
    vs_mcts = play_match(
        agent, MCTSAI(simulations=eval_sims), num_pairs=eval_pairs
    )

    random_rate = vs_random["a_wins"] / vs_random["games"] * 100
    mcts_rate = vs_mcts["a_wins"] / vs_mcts["games"] * 100

    return round(random_rate, 1), round(mcts_rate, 1)


def run_training(
    iterations=10,
    games_per_iter=20,
    simulations=50,
    epochs=10,
    buffer_size=20000,
    eval_pairs=5,
    eval_sims=50
):

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print("Device:", device)

    os.makedirs("results/models", exist_ok=True)

    model = AlphaZeroCNN().to(device)
    buffer = []

    log_path = "results/training_progress.csv"

    with open(log_path, "w", newline="") as f:
        csv.writer(f).writerow([
            "Iteration", "Loss", "Samples",
            "Win Rate vs Random", "Win Rate vs MCTS", "Time"
        ])

    rows = []

    # Iteration 0: untrained network ka baseline
    print("\n=== Iteration 0 (untrained) ===")
    r_rate, m_rate = evaluate(model, eval_sims, eval_pairs)
    print(f"vs Random: {r_rate}% | vs MCTS: {m_rate}%")
    rows.append([0, 0, 0, r_rate, m_rate, 0])

    for it in range(1, iterations + 1):

        start = time.time()
        print(f"\n=== Iteration {it}/{iterations} ===")

        print("Self-play...")
        new_data = generate_self_play_data(
            model, games_per_iter, simulations
        )

        buffer.extend(new_data)
        buffer = buffer[-buffer_size:]

        print(f"Training on {len(buffer)} samples...")
        model, loss = train_model(
            model=model,
            data=buffer,
            epochs=epochs,
            save_path=f"results/models/model_iter_{it}.pth"
        )

        torch.save(
            model.state_dict(), "results/models/connect4_model.pth"
        )

        print("Evaluating...")
        r_rate, m_rate = evaluate(model, eval_sims, eval_pairs)

        elapsed = round(time.time() - start, 1)

        print(
            f"Loss: {loss:.4f} | vs Random: {r_rate}% | "
            f"vs MCTS: {m_rate}% | Time: {elapsed}s"
        )

        rows.append([it, round(loss, 4), len(buffer), r_rate, m_rate, elapsed])

        # Har iteration ke baad CSV save
        with open(log_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Iteration", "Loss", "Samples",
                "Win Rate vs Random", "Win Rate vs MCTS", "Time"
            ])
            writer.writerows(rows)

    print("\nTraining finished. Final model: results/models/connect4_model.pth")


if __name__ == "__main__":

    # Pehle test ke liye: iterations=2, games_per_iter=2, eval_pairs=1
    run_training(
        iterations=10,
        games_per_iter=20,
        simulations=50,
        epochs=10,
        eval_pairs=5,
        eval_sims=50
    )