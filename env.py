import numpy as np
import random
from collections import deque
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Input, Reshape, Multiply
from tensorflow.keras.optimizers import Adam
from board import Board, BOARD_SIZE, ORDER_PLAYERS
from gym import spaces


def get_legal_actions_mask(self):
    mask = np.zeros((len(self.board.pieces), BOARD_SIZE * 2 - 1, BOARD_SIZE * 2 - 1, BOARD_SIZE * 2, BOARD_SIZE * 2), dtype=np.int8)
    for piece_index, piece in enumerate(self.board.pieces):
        if piece.color == self.current_player.color and not piece.is_dead:
            legal_moves = piece.all_possible_moves(self.board)
            for new_q, new_r in legal_moves:
                mask[piece_index, new_q + BOARD_SIZE - 1, new_r + BOARD_SIZE - 1, :, :] = 1
                # Si le mouvement implique de tuer une pièce, ajoutez les positions légales pour la pièce tuée
                target_piece = self.board.get_piece_at(new_q, new_r)
                if target_piece and target_piece.color != piece.color:
                    unoccupied_cells = self.board.get_unoccupied_cells()
                    for killed_q, killed_r in unoccupied_cells:
                        mask[piece_index, new_q + BOARD_SIZE - 1, new_r + BOARD_SIZE - 1, killed_q + BOARD_SIZE, killed_r + BOARD_SIZE] = 1
                else:
                    # Si aucune pièce n'est tuée, permettez seulement l'action "pas de déplacement de pièce tuée"
                    mask[piece_index, new_q + BOARD_SIZE - 1, new_r + BOARD_SIZE - 1, BOARD_SIZE - 1, BOARD_SIZE - 1] = 1
    
    return mask

class DjambiEnv:
    def __init__(self):
        self.current_player_index = 0
        self.board = Board(self.current_player_index)
        self.board.rl = True

    def reset(self):
        self.current_player_index = 0
        self.board = Board(self.current_player_index)
        self.board.rl = True
        return self.get_state()

    def get_state(self):
        state = np.zeros((BOARD_SIZE*2-1, BOARD_SIZE*2-1, 7), dtype=np.int8)
        piece_types = ['militant', 'assassin', 'chief', 'diplomat', 'necromobile', 'reporter']
        for piece in self.board.pieces:
            x, y = piece.q + BOARD_SIZE - 1, piece.r + BOARD_SIZE - 1
            color_index = ORDER_PLAYERS.index(piece.color)
            piece_type_index = piece_types.index(piece.piece_class) + 1  # +1 pour réserver 0 aux cases vides
            state[x, y, color_index] = piece_type_index
            if piece.is_dead:
                state[x, y, 6] = 1  # Marquer les pièces mortes dans le 7e canal
        return state

    def step(self, action):
        # legal_actions_mask = self.get_legal_actions_mask()
        # if legal_actions_mask[tuple(action)] == 0:
        #     # L'action est illégale, appliquez une pénalité et ne changez pas l'état du jeu
        #     return self.get_state(), -10, False, {"illegal_move": True, "undo": True}

        # Sauvegardez l'état actuel avant d'exécuter l'action
        previous_state = self.board.copy()
        previous_player_index = self.current_player_index
        
        # Exécuter l'action
        piece, new_position, killed_piece_position = self.decode_action(action)
        if not piece.move(new_position[0], new_position[1], self.board, killed_piece_position):
            return self.get_state(), -10, False, {"illegal_move": True, "undo": True}
        else:
            self.board.next_player() # handle possible chief surrounding.
            # Exécuter l'action et retourner new_state, reward, done, info
            new_state = self.get_state()
            reward = self.calculate_reward()
            done = len(self.board.players) == 1
            
            info = {
                "illegal_move": False,
                "undo": False,
                "previous_state": previous_state,
                "previous_player_index": previous_player_index
            }
            return new_state, reward, done, info

    # Ajoutez une nouvelle méthode pour annuler le dernier mouvement
    def undo_last_move(self, previous_state, previous_player_index):
        self.board = previous_state
        self.current_player_index = previous_player_index

    def decode_action(self, action):
        piece_index, new_q, new_r, killed_piece_q, killed_piece_r = action
        
        piece = self.board.pieces[piece_index]
        new_position = (new_q, new_r)
        killed_piece_position = (killed_piece_q, killed_piece_r) if killed_piece_q != -1 and killed_piece_r != -1 else None
        
        return piece, new_position, killed_piece_position


    def calculate_reward(self):
        # Calculez la récompense basée sur l'état du jeu
        # Par exemple, +1 pour tuer une pièce ennemie, +10 pour tuer un chef, etc.
        pass

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0   # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        state_input = Input(shape=self.state_size)
        legal_actions_mask = Input(shape=self.action_size)
        
        model = Sequential()
        model.add(Dense(24, input_shape=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        
        output = Dense(np.prod(self.action_size))(x)
        output = Reshape(self.action_size)(output)
        masked_output = Multiply()([output, legal_actions_mask])
        
        model = Model(inputs=[state_input, legal_actions_mask], outputs=masked_output)
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model
        

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        legal_actions_mask = self.env.get_legal_actions_mask()
        if np.random.rand() <= self.epsilon:
            # Choisissez une action aléatoire parmi les actions légales
            legal_actions = np.argwhere(legal_actions_mask.flatten() == 1)
            return legal_actions[np.random.randint(len(legal_actions))].reshape(-1)
        
        act_values = self.model.predict(state)
        act_values[legal_actions_mask == 0] = -np.inf  # Masquer les actions illégales
        return np.unravel_index(np.argmax(act_values), act_values.shape)

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# Entraînement
env = DjambiEnv()
state_size = (BOARD_SIZE*2-1, BOARD_SIZE*2-1, 7)

# Définition de l'espace d'action
action_space = spaces.MultiDiscrete([
    len(env.board.pieces),  # Nombre de pièces
    BOARD_SIZE * 2 - 1,     # Plage de q
    BOARD_SIZE * 2 - 1,     # Plage de r
    BOARD_SIZE * 2,         # Plage de q pour la pièce tuée (inclut -1 pour "pas de pièce tuée")
    BOARD_SIZE * 2          # Plage de r pour la pièce tuée (inclut -1 pour "pas de pièce tuée")
])

agent = DQNAgent(state_size, action_space)

episodes = 1000
for e in range(episodes):
    state = env.reset()
    for time in range(500):  # max 500 moves per game
        action = agent.act(state)
        next_state, reward, done, info = env.step(action)
        
        if info["illegal_move"]:
            # Si le mouvement était illégal, annulez-le et faites rejouer le même joueur
            env.undo_last_move(info["previous_state"], info["previous_player_index"])
            continue
        
        agent.remember(state, action, reward, next_state, done)
        state = next_state
        if done:
            print(f"episode: {e}/{episodes}, score: {time}")
            break
    if len(agent.memory) > 32:
        agent.replay(32)