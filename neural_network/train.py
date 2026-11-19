import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from neural_network.model import AlphaZeroCNN


class ConnectFourDataset(Dataset):

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]


def train_model(
    model=None,
    data=None,
    data_path="results/self_play_data.pt",
    epochs=10,
    batch_size=64,
    lr=0.001,
    save_path="results/models/connect4_model.pth",
    verbose=True
):

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    if data is None:
        data = torch.load(
            data_path, map_location="cpu", weights_only=True
        )

    if model is None:
        model = AlphaZeroCNN()

    model = model.to(device)

    loader = DataLoader(
        ConnectFourDataset(data),
        batch_size=batch_size,
        shuffle=True
    )

    optimizer = torch.optim.Adam(
        model.parameters(), lr=lr, weight_decay=1e-4
    )

    average_loss = 0.0

    for epoch in range(epochs):

        model.train()
        total_loss = 0.0

        for states, policies, values in loader:

            states = states.to(device)
            policies = policies.to(device)
            values = values.to(device)

            predicted_policy, predicted_value = model(states)

            # Soft target: MCTS visit distribution par cross-entropy
            log_probs = F.log_softmax(predicted_policy, dim=1)
            policy_loss = -(policies * log_probs).sum(dim=1).mean()

            value_loss = F.mse_loss(predicted_value, values)

            loss = policy_loss + value_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        average_loss = total_loss / len(loader)

        if verbose:
            print(
                f"  Epoch [{epoch + 1}/{epochs}] "
                f"Loss: {average_loss:.4f}"
            )

    model.eval()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        torch.save(model.state_dict(), save_path)

    return model, average_loss


if __name__ == "__main__":
    train_model(epochs=20)
    print("Training Completed!")