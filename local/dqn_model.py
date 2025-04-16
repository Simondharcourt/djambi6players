import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random
from typing import Tuple, Dict, List
import torch.nn.functional as F

class DQN(nn.Module):
    def __init__(self, input_shape: Tuple[int, int, int], n_actions: int):
        super(DQN, self).__init__()
        
        # Couches convolutives pour le plateau
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)  # 1 channel d'entrée
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        
        # Couches fully connected
        conv_out_size = self._get_conv_out(input_shape)
        self.fc1 = nn.Linear(conv_out_size + 4, 512)  # +4 pour le statut des joueurs et le joueur actuel
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, n_actions)
        
    def _get_conv_out(self, shape):
        o = self.conv1(torch.zeros(1, 1, *shape[1:]))  # Ajouter la dimension du channel
        o = self.conv2(o)
        o = self.conv3(o)
        return int(np.prod(o.size()))
    
    def forward(self, x: Dict[str, torch.Tensor]) -> torch.Tensor:
        # Traiter le plateau
        board = x["board"].float()
        batch_size = board.size(0)
        
        # Ajouter la dimension du channel
        board = board.unsqueeze(1)  # [batch_size, 1, height, width]
        
        # Passer à travers les couches convolutives
        conv_out = F.relu(self.conv1(board))
        conv_out = F.relu(self.conv2(conv_out))
        conv_out = F.relu(self.conv3(conv_out))
        conv_out = conv_out.view(batch_size, -1)  # [batch_size, conv_features]
        
        # Concaténer avec les autres informations
        player_status = x["player_status"].float().view(batch_size, -1)  # [batch_size, 3]
        current_player = x["current_player"].float().view(batch_size, -1)  # [batch_size, 1]
        combined = torch.cat([conv_out, player_status, current_player], dim=1)
        
        # Passer à travers les couches fully connected
        x = F.relu(self.fc1(combined))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state: Dict[str, np.ndarray], action: np.ndarray, reward: float, 
             next_state: Dict[str, np.ndarray], done: bool):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple[Dict[str, torch.Tensor], torch.Tensor, torch.Tensor, 
                                              Dict[str, torch.Tensor], torch.Tensor]:
        state, action, reward, next_state, done = zip(*random.sample(self.buffer, batch_size))
        
        # Convertir en tenseurs PyTorch
        state = {
            "board": torch.FloatTensor(np.array([s["board"] for s in state])),
            "player_status": torch.FloatTensor(np.array([s["player_status"] for s in state])),
            "current_player": torch.FloatTensor(np.array([s["current_player"] for s in state]))
        }
        
        next_state = {
            "board": torch.FloatTensor(np.array([s["board"] for s in next_state])),
            "player_status": torch.FloatTensor(np.array([s["player_status"] for s in next_state])),
            "current_player": torch.FloatTensor(np.array([s["current_player"] for s in next_state]))
        }
        
        action = torch.LongTensor(np.array(action))
        reward = torch.FloatTensor(reward)
        done = torch.FloatTensor(done)
        
        return state, action, reward, next_state, done
    
    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    def __init__(self, state_shape: Tuple[int, int, int], n_actions: int, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.n_actions = n_actions
        
        # Créer les réseaux
        self.policy_net = DQN(state_shape, n_actions).to(device)
        self.target_net = DQN(state_shape, n_actions).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Optimiseur
        self.optimizer = optim.Adam(self.policy_net.parameters())
        
        # Buffer de replay
        self.memory = ReplayBuffer(100000)
        
        # Hyperparamètres
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
            # Action aléatoire
            board_size = state["board"].shape[0]
            return np.array([
                random.randint(0, board_size-1),  # piece_q
                random.randint(0, board_size-1),  # piece_r
                random.randint(0, board_size-1),  # move_q
                random.randint(0, board_size-1)   # move_r
            ])
        
        with torch.no_grad():
            # Convertir l'état en tenseur
            state_tensor = {
                "board": torch.FloatTensor(state["board"]).unsqueeze(0).to(self.device),
                "player_status": torch.FloatTensor(state["player_status"]).unsqueeze(0).to(self.device),
                "current_player": torch.FloatTensor([state["current_player"]]).unsqueeze(0).to(self.device)
            }
            
            # Sélectionner l'action avec la plus haute valeur Q
            q_values = self.policy_net(state_tensor)
            action_idx = q_values.max(1)[1].cpu().numpy()[0]
            
            # Convertir l'index en coordonnées
            board_size = state["board"].shape[0]
            piece_q = action_idx // (board_size ** 3)
            action_idx = action_idx % (board_size ** 3)
            piece_r = action_idx // (board_size ** 2)
            action_idx = action_idx % (board_size ** 2)
            move_q = action_idx // board_size
            move_r = action_idx % board_size
            
            return np.array([piece_q, piece_r, move_q, move_r])
    
    def optimize_model(self):
        if len(self.memory) < self.batch_size:
            return
        
        # Échantillonner un batch
        state, action, reward, next_state, done = self.memory.sample(self.batch_size)
        
        # Convertir les actions en indices uniques
        board_size = state["board"].shape[1]
        action_indices = (action[:, 0] * (board_size ** 3) + 
                        action[:, 1] * (board_size ** 2) + 
                        action[:, 2] * board_size + 
                        action[:, 3])
        
        # Calculer Q(s_t, a)
        state_action_values = self.policy_net(state).gather(1, action_indices.unsqueeze(1))
        
        # Calculer V(s_{t+1})
        with torch.no_grad():
            next_state_values = self.target_net(next_state).max(1)[0]
            expected_state_action_values = reward + (1 - done) * self.gamma * next_state_values
        
        # Calculer la loss
        loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))
        
        # Optimiser
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimizer.step()
        
        # Mettre à jour le réseau cible
        if self.steps_done % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def save(self, path: str):
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'eps': self.eps,
            'steps_done': self.steps_done
        }, path)
    
    def load(self, path: str):
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.eps = checkpoint['eps']
        self.steps_done = checkpoint['steps_done'] 