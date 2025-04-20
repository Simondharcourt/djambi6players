import gymnasium as gym
import numpy as np
from .djambi_env import DjambiEnv
from .dqn_model import DQNAgent
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
import random
import pygame
import argparse

def train(
    env: DjambiEnv, agent: DQNAgent, num_episodes: int = 1000, save_path: str = "models"
):
    """
    Entraîne l'agent DQN sur l'environnement Djambi.
    """
    # Créer le dossier de sauvegarde
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Statistiques
    rewards = []
    epsilons = []
    wins = 0

    # Barre de progression
    pbar = tqdm(range(num_episodes))

    for episode in pbar:
        # Réinitialiser l'environnement
        state, _ = env.reset()
        episode_reward = 0
        done = False

        while not done:
            # Vérifier si l'entraînement est en pause
            while env.paused:
                env.render()
                pygame.time.delay(100)  # Réduire la charge CPU pendant la pause

            # Sélectionner une action
            if random.random() < agent.eps:
                # Exploration: choisir une action valide aléatoire
                action = env.sample_action()
            else:
                # Exploitation: utiliser le modèle
                action = agent.select_action(state)

            # Exécuter l'action
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            # Stocker l'expérience
            agent.memory.push(state, action, reward, next_state, done)

            # Optimiser le modèle
            agent.optimize_model()

            # Mettre à jour l'état et la récompense
            state = next_state
            episode_reward += reward

            # Si un joueur a gagné
            if reward == 1.0:
                wins += 1

        # Mettre à jour les statistiques
        rewards.append(episode_reward)
        epsilons.append(agent.eps)

        # Mettre à jour la barre de progression
        pbar.set_description(
            f"Episode {episode+1}/{num_episodes} - Reward: {episode_reward:.2f} - Epsilon: {agent.eps:.2f} - Wins: {wins}"
        )

        # Sauvegarder le modèle tous les 100 épisodes
        if (episode + 1) % 100 == 0:
            agent.save(os.path.join(save_path, f"dqn_episode_{episode+1}.pt"))

    # Afficher les statistiques
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    plt.plot(rewards)
    plt.title("Récompenses par épisode")
    plt.xlabel("Épisode")
    plt.ylabel("Récompense")

    plt.subplot(1, 2, 2)
    plt.plot(epsilons)
    plt.title("Epsilon par épisode")
    plt.xlabel("Épisode")
    plt.ylabel("Epsilon")

    plt.tight_layout()
    plt.savefig(os.path.join(save_path, "training_stats.png"))
    plt.close()

    return rewards, epsilons, wins


# Ajout de la fonction pour traiter les arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Choisissez les paramètres du jeu.")
    parser.add_argument(
        "--nb_player_mode",
        type=int,
        choices=[3, 4, 6],
        default=3,
        help="Nombre de joueurs (3, 4 ou 6)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    # Créer l'environnement
    env = DjambiEnv(nb_players=args.nb_player_mode, render_mode="human")  # Set to "human" to see the game

    # Définir la forme de l'état et le nombre d'actions
    board_shape = env.observation_space["board"].shape
    state_shape = (1, board_shape[0], board_shape[1])  # Ajouter la dimension du channel
    n_actions = np.prod(env.action_space.nvec)

    print(f"Board shape: {board_shape}")
    print(f"State shape: {state_shape}")
    print(f"Number of actions: {n_actions}")

    # Créer l'agent
    agent = DQNAgent(state_shape, n_actions)

    # Entraîner l'agent
    rewards, epsilons, wins = train(env, agent, num_episodes=1000)

    print(f"\nEntraînement terminé !")
    print(f"Nombre total de victoires : {wins}")
    print(f"Récompense moyenne : {np.mean(rewards):.2f}")
    print(f"Récompense maximale : {np.max(rewards):.2f}")

    # Fermer l'environnement
    env.close()
