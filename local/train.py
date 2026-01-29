import argparse
import os
import random

import gymnasium as gym
import matplotlib.pyplot as plt
import numpy as np
import pygame
from tqdm import tqdm

from .djambi_env import DjambiEnv
from .dqn_model import DQNAgent


def train(
    env: DjambiEnv, agent: DQNAgent, num_episodes: int = 1000, save_path: str = "models"
):
    """
    Trains the DQN agent on the Djambi environment.
    """
    # Create the save directory
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Statistics
    rewards = []
    epsilons = []
    wins = 0

    # Progress bar
    pbar = tqdm(range(num_episodes))

    for episode in pbar:
        # Reset the environment
        state, _ = env.reset()
        episode_reward = 0.0
        done = False

        while not done:
            # Check if training is paused
            while env.paused:
                env.render()
                pygame.time.delay(100)  # Reduce CPU load during pause

            # Select an action
            if random.random() < agent.eps:
                # Exploration: choose a random valid action
                action = env.sample_action()
            else:
                # Exploitation: use the model
                action = agent.select_action(state)

            # Execute the action
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            # Store the experience
            agent.memory.push(state, action, reward, next_state, done)

            # Optimize the model
            agent.optimize_model()

            # Update the state and reward
            state = next_state
            episode_reward += reward

            # If a player has won
            if reward == 1.0:
                wins += 1

        # Update the statistics
        rewards.append(episode_reward)
        epsilons.append(agent.eps)

        # Update the progress bar
        pbar.set_description(
            f"Episode {episode+1}/{num_episodes} - Reward: {episode_reward:.2f} - Epsilon: {agent.eps:.2f} - Wins: {wins}"
        )

        # Save the model every 100 episodes
        if (episode + 1) % 100 == 0:
            agent.save(os.path.join(save_path, f"dqn_episode_{episode+1}.pt"))

    # Display the statistics
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    plt.plot(rewards)
    plt.title("Rewards per episode")
    plt.xlabel("Episode")
    plt.ylabel("Reward")

    plt.subplot(1, 2, 2)
    plt.plot(epsilons)
    plt.title("Epsilon per episode")
    plt.xlabel("Episode")
    plt.ylabel("Epsilon")

    plt.tight_layout()
    plt.savefig(os.path.join(save_path, "training_stats.png"))
    plt.close()

    return rewards, epsilons, wins


# Add function to process arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Choose game parameters.")
    parser.add_argument(
        "--nb_player_mode",
        type=int,
        choices=[3, 4, 6],
        default=3,
        help="Number of players (3, 4 or 6)",
    )
    parser.add_argument(
        "--render",
        type=bool,
        default=False,
        help="Render mode (human or none)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    # Create the environment
    env = DjambiEnv(
        nb_players=args.nb_player_mode, render=args.render
    )  # Set to "human" to see the game

    # Define the state shape and number of actions
    board_shape = env.observation_space["board"].shape
    state_shape = (1, board_shape[0], board_shape[1])  # Add the channel dimension
    n_actions = int(np.prod(env.action_space.nvec))

    print(f"Board shape: {board_shape}")
    print(f"State shape: {state_shape}")
    print(f"Number of actions: {n_actions}")

    # Create the agent
    agent = DQNAgent(state_shape, n_actions)

    # Train the agent
    rewards, epsilons, wins = train(env, agent, num_episodes=1000)

    print(f"\nTraining complete!")
    print(f"Total number of wins: {wins}")
    print(f"Average reward: {np.mean(rewards):.2f}")
    print(f"Maximum reward: {np.max(rewards):.2f}")

    # Fermer l'environnement
    env.close()
