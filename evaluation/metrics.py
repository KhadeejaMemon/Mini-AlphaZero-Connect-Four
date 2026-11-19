import os
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("results/graphs", exist_ok=True)


def save(name):
    plt.tight_layout()
    plt.savefig(f"results/graphs/{name}.png")
    plt.show()


# ---------- Tournament graphs ----------
if os.path.exists("results/tournament_results.csv"):

    data = pd.read_csv("results/tournament_results.csv")

    plt.figure(figsize=(10, 6))
    plt.bar(data["AI"], data["Win Rate"])
    plt.title("AI Algorithms - Win Rate Comparison")
    plt.xlabel("AI Algorithms")
    plt.ylabel("Win Rate (%)")
    plt.xticks(rotation=20)
    plt.ylim(0, 100)
    save("win_rate")

    plt.figure(figsize=(10, 6))
    plt.bar(data["AI"], data["Average Decision Time"])
    plt.title("AI Algorithms - Average Decision Time")
    plt.xlabel("AI Algorithms")
    plt.ylabel("Time (seconds)")
    plt.xticks(rotation=20)
    save("decision_time")


# ---------- Learning progress ----------
if os.path.exists("results/training_progress.csv"):

    prog = pd.read_csv("results/training_progress.csv")

    plt.figure(figsize=(10, 6))
    plt.plot(prog["Iteration"], prog["Win Rate vs Random"],
             marker="o", label="vs Random AI")
    plt.plot(prog["Iteration"], prog["Win Rate vs MCTS"],
             marker="s", label="vs Standard MCTS")
    plt.title("Learning Progress Across Training Iterations")
    plt.xlabel("Training Iteration")
    plt.ylabel("Win Rate (%)")
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(alpha=0.3)
    save("learning_progress")

    plt.figure(figsize=(10, 6))
    plt.plot(prog["Iteration"][1:], prog["Loss"][1:], marker="o")
    plt.title("Training Loss Across Iterations")
    plt.xlabel("Training Iteration")
    plt.ylabel("Loss")
    plt.grid(alpha=0.3)
    save("training_loss")


# ---------- Simulation budget comparison ----------
if os.path.exists("results/budget_comparison.csv"):

    b = pd.read_csv("results/budget_comparison.csv")

    plt.figure(figsize=(10, 6))
    plt.plot(b["Simulations"], b["Neural Win Rate"],
             marker="o", label="Neural MCTS")
    plt.plot(b["Simulations"], b["Plain Win Rate"],
             marker="s", label="Standard MCTS")
    plt.title("Neural MCTS vs Standard MCTS (Equal Simulations)")
    plt.xlabel("Simulations per Move")
    plt.ylabel("Win Rate (%)")
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(alpha=0.3)
    save("budget_comparison")

print("Graphs saved in results/graphs/")