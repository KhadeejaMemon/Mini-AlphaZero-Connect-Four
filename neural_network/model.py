import torch
import torch.nn as nn
import torch.nn.functional as F


class AlphaZeroCNN(nn.Module):

    def __init__(self):

        super(AlphaZeroCNN, self).__init__()

        # Shared CNN layers
        self.conv1 = nn.Conv2d(
            1, 64, kernel_size=3, padding=1
        )

        self.conv2 = nn.Conv2d(
            64, 128, kernel_size=3, padding=1
        )

        self.conv3 = nn.Conv2d(
            128, 128, kernel_size=3, padding=1
        )

        # Policy Head
        self.policy_conv = nn.Conv2d(
            128, 32, kernel_size=1
        )

        self.policy_fc = nn.Linear(
            32 * 6 * 7, 7
        )

        # Value Head
        self.value_conv = nn.Conv2d(
            128, 32, kernel_size=1
        )

        self.value_fc1 = nn.Linear(
            32 * 6 * 7, 128
        )

        self.value_fc2 = nn.Linear(
            128, 1
        )

    def forward(self, x):

        # Shared layers
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))

        # Policy Head
        policy = F.relu(self.policy_conv(x))
        policy = policy.view(policy.size(0), -1)
        policy = self.policy_fc(policy)

        # Value Head
        value = F.relu(self.value_conv(x))
        value = value.view(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value