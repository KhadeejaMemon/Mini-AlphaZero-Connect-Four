"""Exports the trained PyTorch model to a JSON file that the browser version can read.

Run from the project root (the folder that contains results/):
    python export_weights.py
Output: web/weights.json
"""
import json
import os
import torch

MODEL_PATH = "results/models/connect4_model.pth"
OUT_PATH = os.path.join("web", "weights.json")

state = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
data = {k: [round(float(x), 5) for x in v.flatten().tolist()] for k, v in state.items()}

os.makedirs("web", exist_ok=True)
with open(OUT_PATH, "w") as f:
    json.dump(data, f, separators=(",", ":"))

print("saved", OUT_PATH, "-", round(os.path.getsize(OUT_PATH) / 1e6, 2), "MB,",
      sum(len(v) for v in data.values()), "parameters")
