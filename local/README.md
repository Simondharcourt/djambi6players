# Djambi Reinforcement Learning

This project aims to develop a reinforcement learning agent capable of playing the 6-player Djambi game. The goal is to train an agent that can eliminate other players and win the game.

## Proposed Approaches

### 1. Deep Q-Network (DQN)

**Proposed Architecture:**
- **Game State:**
  - Board encoding (6x6)
  - Position of each player's pieces
  - Piece status (alive/dead)
  - Current player
  - Recent move history

- **Neural Network:**
  - Convolutional layers to process the board
  - Fully connected layers for decision making
  - Double DQN for improved stability
  - Prioritized Experience Replay

- **Reward Function:**
  - +1.0 for eliminating a player
  - -1.0 for being eliminated
  - +0.1 for strategic moves
  - -0.1 for risky moves

### 2. Policy Gradient Methods (PPO)

**Advantages:**
- Better handling of continuous actions
- More stable for complex environments
- Can learn more sophisticated strategies

**Architecture:**
- Actor-Critic with two networks
- PPO for training stability
- GAE (Generalized Advantage Estimation)

### 3. Monte Carlo Tree Search (MCTS) + Deep Learning

**Hybrid Approach:**
- MCTS for exploration
- Neural network for position evaluation
- AlphaZero-like implementation

## Implementation

### Prerequisites
- Python 3.11+
- PyTorch
- Gymnasium
- NumPy
- Matplotlib (for visualization)
- uv (for package management)

### Project Structure
```
local/
├── djambi_env.py       # Game environment
├── dqn_model.py        # DQN model implementation
├── train.py            # Training script
└── README.md           # This file
```

### Training

To train the agent:
```bash
# With rendering (visual feedback)
uv run python local/train.py --nb_player_mode 3 --render true

# Without rendering (faster training)
uv run python local/train.py --nb_player_mode 3 --render false
```

**Training Phases:**

1. **Phase 1: Basic Learning**
   - Training against random agents
   - Focus on basic rules
   - Duration: ~100,000 episodes

2. **Phase 2: Advanced Learning**
   - Training against previous versions
   - Focus on strategy
   - Duration: ~500,000 episodes

3. **Phase 3: Fine-tuning**
   - Training against humans
   - Strategy optimization
   - Duration: Variable

### Evaluation Metrics
- Win rate
- Average number of turns per game
- Survival rate
- Attack efficiency

## Next Steps

1. [ ] Implement base environment ✅
2. [ ] Develop DQN ✅
3. [ ] Initial training
4. [ ] Evaluation and optimization
5. [ ] Implement advanced methods

## References

- [Deep Q-Learning with Double Q-Learning](https://arxiv.org/abs/1509.06461)
- [Proximal Policy Optimization](https://arxiv.org/abs/1707.06347)
- [Mastering Chess and Shogi by Self-Play](https://arxiv.org/abs/1712.01815)
