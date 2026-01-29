# Djambi Reinforcement Learning

Ce projet vise à développer un agent de reinforcement learning capable de jouer au jeu Djambi à 6 joueurs. L'objectif est d'entraîner un agent qui peut éliminer les autres joueurs et gagner la partie.

## Approches Proposées

### 1. Deep Q-Network (DQN)

**Architecture proposée :**
- **État du jeu :**
  - Encodage du plateau (6x6)
  - Position des pièces de chaque joueur
  - État des pièces (vivantes/mortes)
  - Joueur actuel
  - Historique des derniers mouvements

- **Réseau de neurones :**
  - Couches convolutives pour traiter le plateau
  - Couches fully connected pour la prise de décision
  - Double DQN pour plus de stabilité
  - Prioritized Experience Replay

- **Fonction de récompense :**
  - +1.0 pour éliminer un joueur
  - -1.0 pour être éliminé
  - +0.1 pour des mouvements stratégiques
  - -0.1 pour des mouvements risqués

### 2. Policy Gradient Methods (PPO)

**Avantages :**
- Meilleure gestion des actions continues
- Plus stable pour les environnements complexes
- Peut apprendre des stratégies plus sophistiquées

**Architecture :**
- Actor-Critic avec deux réseaux
- PPO pour la stabilité de l'entraînement
- GAE (Generalized Advantage Estimation)

### 3. Monte Carlo Tree Search (MCTS) + Deep Learning

**Approche hybride :**
- MCTS pour l'exploration
- Réseau de neurones pour l'évaluation des positions
- AlphaZero-like implementation

## Implémentation

### Prérequis
- Python 3.8+
- PyTorch
- Gymnasium
- NumPy
- Matplotlib (pour la visualisation)

### Structure du Projet
```
local/
├── env.py              # Environnement du jeu
├── models/             # Modèles de RL
│   ├── dqn.py
│   ├── ppo.py
│   └── mcts.py
├── utils/              # Utilitaires
│   ├── replay_buffer.py
│   └── visualization.py
└── train.py           # Script d'entraînement
```

### Entraînement

1. **Phase 1 : Apprentissage de base**
   - Entraînement contre des agents aléatoires
   - Focus sur les règles de base
   - Durée : ~100,000 épisodes

2. **Phase 2 : Apprentissage avancé**
   - Entraînement contre des versions précédentes
   - Focus sur la stratégie
   - Durée : ~500,000 épisodes

3. **Phase 3 : Fine-tuning**
   - Entraînement contre des humains
   - Optimisation des stratégies
   - Durée : Variable

### Métriques d'Évaluation
- Taux de victoire
- Nombre moyen de tours par partie
- Taux de survie
- Efficacité des attaques

## Prochaines Étapes

1. [ ] Implémentation de l'environnement de base
2. [ ] Développement du DQN
3. [ ] Entraînement initial
4. [ ] Évaluation et optimisation
5. [ ] Implémentation des méthodes avancées

## Références

- [Deep Q-Learning with Double Q-Learning](https://arxiv.org/abs/1509.06461)
- [Proximal Policy Optimization](https://arxiv.org/abs/1707.06347)
- [Mastering Chess and Shogi by Self-Play](https://arxiv.org/abs/1712.01815)
