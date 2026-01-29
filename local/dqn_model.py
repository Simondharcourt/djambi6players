import random
from collections import deque
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class DQN(nn.Module):
    def __init__(self, input_shape: Tuple[int, int, int], n_actions: int):
        super(DQN, self).__init__()

        # Convolutional layers for the board
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)  # 1 input channel
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, padding=1)

        # Fully connected layers
        conv_out_size = self._get_conv_out(input_shape)
        self.fc1 = nn.Linear(
            conv_out_size + 4, 512
        )  # +4 for player status and current player
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, n_actions)

    def _get_conv_out(self, shape):
        o = self.conv1(torch.zeros(1, 1, *shape[1:]))  # Add the channel dimension
        o = self.conv2(o)
        o = self.conv3(o)
        return int(np.prod(o.size()))

    def forward(self, x: Dict[str, torch.Tensor]) -> torch.Tensor:
        # Process the board
        board = x["board"].float()
        batch_size = board.size(0)

        # Add the channel dimension
        board = board.unsqueeze(1)  # [batch_size, 1, height, width]

        # Pass through the convolutional layers
        conv_out = F.relu(self.conv1(board))
        conv_out = F.relu(self.conv2(conv_out))
        conv_out = F.relu(self.conv3(conv_out))
        conv_out = conv_out.view(batch_size, -1)  # [batch_size, conv_features]

        # Concatenate with other information
        player_status = (
            x["player_status"].float().view(batch_size, -1)
        )  # [batch_size, 3]
        current_player = (
            x["current_player"].float().view(batch_size, -1)
        )  # [batch_size, 1]
        combined = torch.cat([conv_out, player_status, current_player], dim=1)

        # Pass through the fully connected layers
        out = F.relu(self.fc1(combined))
        out = F.relu(self.fc2(out))
        result: torch.Tensor = self.fc3(out)
        return result


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer: deque[
            tuple[Dict[str, np.ndarray], np.ndarray, float, Dict[str, np.ndarray], bool]
        ] = deque(maxlen=capacity)

    def push(
        self,
        state: Dict[str, np.ndarray],
        action: np.ndarray,
        reward: float,
        next_state: Dict[str, np.ndarray],
        done: bool,
    ):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(
        self, batch_size: int
    ) -> Tuple[
        Dict[str, torch.Tensor],
        torch.Tensor,
        torch.Tensor,
        Dict[str, torch.Tensor],
        torch.Tensor,
    ]:
        samples = random.sample(self.buffer, batch_size)
        state_list, action_list, reward_list, next_state_list, done_list = zip(*samples)

        # Convertir en tenseurs PyTorch
        state_dict: Dict[str, torch.Tensor] = {
            "board": torch.FloatTensor(np.array([s["board"] for s in state_list])),
            "player_status": torch.FloatTensor(
                np.array([s["player_status"] for s in state_list])
            ),
            "current_player": torch.FloatTensor(
                np.array([s["current_player"] for s in state_list])
            ),
        }

        next_state_dict: Dict[str, torch.Tensor] = {
            "board": torch.FloatTensor(np.array([s["board"] for s in next_state_list])),
            "player_status": torch.FloatTensor(
                np.array([s["player_status"] for s in next_state_list])
            ),
            "current_player": torch.FloatTensor(
                np.array([s["current_player"] for s in next_state_list])
            ),
        }

        action_tensor = torch.LongTensor(np.array(action_list))
        reward_tensor = torch.FloatTensor(reward_list)
        done_tensor = torch.FloatTensor(done_list)

        return state_dict, action_tensor, reward_tensor, next_state_dict, done_tensor

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    def __init__(
        self,
        state_shape: Tuple[int, int, int],
        n_actions: int,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.device = device
        self.n_actions = n_actions

        # Create the networks
        self.policy_net = DQN(state_shape, n_actions).to(device)
        self.target_net = DQN(state_shape, n_actions).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters())

        # Replay buffer
        self.memory = ReplayBuffer(100000)

        # Hyperparameters
        self.batch_size = 64
        self.gamma = 0.99
        self.eps_start = 1.0
        self.eps_end = 0.01
        self.eps_decay = 0.995
        self.eps = self.eps_start
        self.target_update = 10
        self.steps_done = 0

    def select_action(self, state: Dict[str, np.ndarray]) -> np.ndarray:
        self.steps_done += 1
        self.eps = max(self.eps_end, self.eps * self.eps_decay)

        if random.random() < self.eps:
            # Random action
            board_size = state["board"].shape[0]
            return np.array(
                [
                    random.randint(0, board_size - 1),  # piece_q
                    random.randint(0, board_size - 1),  # piece_r
                    random.randint(0, board_size - 1),  # move_q
                    random.randint(0, board_size - 1),  # move_r
                ]
            )

        with torch.no_grad():
            # Convert the state to tensor
            state_tensor = {
                "board": torch.FloatTensor(state["board"]).unsqueeze(0).to(self.device),
                "player_status": torch.FloatTensor(state["player_status"])
                .unsqueeze(0)
                .to(self.device),
                "current_player": torch.FloatTensor([state["current_player"]])
                .unsqueeze(0)
                .to(self.device),
            }

            # Select the action with the highest Q value
            q_values = self.policy_net(state_tensor)
            action_idx = q_values.max(1)[1].cpu().numpy()[0]

            # Convert the index to coordinates
            board_size = state["board"].shape[0]
            piece_q = action_idx // (board_size**3)
            action_idx = action_idx % (board_size**3)
            piece_r = action_idx // (board_size**2)
            action_idx = action_idx % (board_size**2)
            move_q = action_idx // board_size
            move_r = action_idx % board_size

            return np.array([piece_q, piece_r, move_q, move_r])

    def optimize_model(self):
        if len(self.memory) < self.batch_size:
            return

        # Sample a batch
        state, action, reward, next_state, done = self.memory.sample(self.batch_size)

        # Convert actions to unique indices
        board_size = state["board"].shape[1]
        action_indices = (
            action[:, 0] * (board_size**3)
            + action[:, 1] * (board_size**2)
            + action[:, 2] * board_size
            + action[:, 3]
        )

        # Calculate Q(s_t, a)
        state_action_values = self.policy_net(state).gather(
            1, action_indices.unsqueeze(1)
        )

        # Calculate V(s_{t+1})
        with torch.no_grad():
            next_state_values = self.target_net(next_state).max(1)[0]
            expected_state_action_values = (
                reward + (1 - done) * self.gamma * next_state_values
            )

        # Calculate the loss
        loss = F.smooth_l1_loss(
            state_action_values, expected_state_action_values.unsqueeze(1)
        )

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimizer.step()

        # Update the target network
        if self.steps_done % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, path: str):
        torch.save(
            {
                "policy_net_state_dict": self.policy_net.state_dict(),
                "target_net_state_dict": self.target_net.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "eps": self.eps,
                "steps_done": self.steps_done,
            },
            path,
        )

    def load(self, path: str):
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint["policy_net_state_dict"])
        self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.eps = checkpoint["eps"]
        self.steps_done = checkpoint["steps_done"]
