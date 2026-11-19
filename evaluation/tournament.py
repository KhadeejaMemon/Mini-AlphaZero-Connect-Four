import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import itertools
import csv

from game.arena import play_match

from agents.random_ai import RandomAI
from agents.minimax import MinimaxAI
from agents.alpha_beta import AlphaBetaAI
from agents.mcts import MCTSAI
from agents.neural_mcts import NeuralMCTSAI


def create_agents():

    return {
        "Random AI": RandomAI(),
        "Minimax": MinimaxAI(depth=3),
        "Alpha-Beta": AlphaBetaAI(depth=3),
        "Standard MCTS": MCTSAI(simulations=100),
        "Neural MCTS": NeuralMCTSAI(simulations=100)
    }


def run_tournament(pairs_per_matchup=10):
    """Har matchup mein 2 * pairs_per_matchup games (dono taraf se)."""

    agents = create_agents()

    results = {
        name: {
            "wins": 0, "losses": 0, "draws": 0, "games": 0,
            "total_time": 0.0, "total_moves": 0
        }
        for name in agents
    }

    for name_one, name_two in itertools.combinations(agents.keys(), 2):

        print(f"\n{name_one} vs {name_two}")

        m = play_match(
            agents[name_one], agents[name_two],
            num_pairs=pairs_per_matchup
        )

        a, b = results[name_one], results[name_two]

        a["wins"] += m["a_wins"]
        a["losses"] += m["b_wins"]
        b["wins"] += m["b_wins"]
        b["losses"] += m["a_wins"]
        a["draws"] += m["draws"]
        b["draws"] += m["draws"]
        a["games"] += m["games"]
        b["games"] += m["games"]

        a["total_time"] += m["a_time"]
        a["total_moves"] += m["a_moves"]
        b["total_time"] += m["b_time"]
        b["total_moves"] += m["b_moves"]

        print(
            f"  {name_one}: {m['a_wins']} | "
            f"{name_two}: {m['b_wins']} | Draws: {m['draws']}"
        )

    print("\n========== TOURNAMENT RESULTS ==========")

    for name, data in results.items():

        win_rate = (
            data["wins"] / data["games"] * 100 if data["games"] else 0
        )
        avg_time = (
            data["total_time"] / data["total_moves"]
            if data["total_moves"] else 0
        )

        data["win_rate"] = round(win_rate, 2)
        data["average_decision_time"] = round(avg_time, 4)

        print(f"\n{name}")
        print("Wins:", data["wins"])
        print("Losses:", data["losses"])
        print("Draws:", data["draws"])
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Average Decision Time: {avg_time:.4f} seconds")

    os.makedirs("results", exist_ok=True)

    with open("results/tournament_results.csv", "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "AI", "Wins", "Losses", "Draws", "Games",
            "Win Rate", "Average Decision Time"
        ])

        for name, data in results.items():
            writer.writerow([
                name, data["wins"], data["losses"], data["draws"],
                data["games"], data["win_rate"],
                data["average_decision_time"]
            ])

    print("\nResults saved in results/tournament_results.csv")


if __name__ == "__main__":
    run_tournament(pairs_per_matchup=10)