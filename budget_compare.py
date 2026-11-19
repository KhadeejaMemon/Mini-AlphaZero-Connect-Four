import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import csv

from game.arena import play_match
from agents.mcts import MCTSAI
from agents.neural_mcts import NeuralMCTSAI


BUDGETS = [25, 50, 100, 200]
PAIRS = 10   # har budget par 20 games


def run_comparison():

    neural = NeuralMCTSAI(simulations=BUDGETS[0])
    plain = MCTSAI(simulations=BUDGETS[0])

    os.makedirs("results", exist_ok=True)

    rows = []

    for sims in BUDGETS:

        neural.simulations = sims
        plain.simulations = sims

        print(f"\nSimulations = {sims}")

        m = play_match(neural, plain, num_pairs=PAIRS)

        neural_rate = m["a_wins"] / m["games"] * 100
        plain_rate = m["b_wins"] / m["games"] * 100

        neural_time = m["a_time"] / m["a_moves"]
        plain_time = m["b_time"] / m["b_moves"]

        print(
            f"Neural: {m['a_wins']} | Plain: {m['b_wins']} | "
            f"Draws: {m['draws']}"
        )

        rows.append([
            sims, m["a_wins"], m["b_wins"], m["draws"],
            round(neural_rate, 1), round(plain_rate, 1),
            round(neural_time, 4), round(plain_time, 4)
        ])

    with open("results/budget_comparison.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Simulations", "Neural Wins", "Plain Wins", "Draws",
            "Neural Win Rate", "Plain Win Rate",
            "Neural Avg Time", "Plain Avg Time"
        ])
        writer.writerows(rows)

    print("\nSaved: results/budget_comparison.csv")


if __name__ == "__main__":
    run_comparison()