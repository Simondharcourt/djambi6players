import asyncio
import json
import websockets
import os
from .board import Board
from .database import Database
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DjambiServer:
    def __init__(self):
        self.board = Board(6, 0)  # Initialiser le plateau de jeu
        self.board.rl = True
        self.clients = {}  # Dictionnaire pour stocker les clients avec leur couleur
        self.current_player_index = 0
        self.lock = asyncio.Lock()
        self.available_colors = list(self.board.colors.keys())
        self.waiting_clients = []  # Nouvelle liste pour les clients en attente
        self.db = Database()  # Initialisation de la base de données
        self.authenticated_users = {}  # websocket -> username
        self.connected_usernames = set()  # Pour suivre les noms d'utilisateur connectés

    async def register(self, websocket):
        # Au lieu d'attribuer directement une couleur, on met le client en attente
        self.waiting_clients.append(websocket)
        await websocket.send(
            json.dumps(
                {"type": "waiting", "message": "En attente de démarrage de partie"}
            )
        )

    async def start_game(self, websocket, nb_players):
        if websocket not in self.waiting_clients:
            return

        if (
            (nb_players == 2 and len(self.available_colors) < 3)
            or (nb_players == 3 and len(self.available_colors) < 2)
            or (nb_players == 6 and not self.available_colors)
        ):
            await websocket.send(
                json.dumps({"type": "error", "message": "La partie est pleine"})
            )
            return

        # Préparer les couleurs et indices
        if nb_players == 2:
            colors = [self.available_colors.pop(0) for _ in range(3)]
            player_index = 1  # Pour le joueur 2

        elif nb_players == 3:
            colors = [self.available_colors.pop(0) for _ in range(2)]
            player_index = 1  # Pour le joueur 2

        else:  # nb_players == 6
            self.waiting_clients.remove(websocket)
            colors = [self.available_colors.pop(0)]
            player_index = list(self.board.colors.keys()).index(colors[0])

        # Enregistrer le client
        self.clients[websocket] = colors

        # Préparer la réponse pour le client
        color_indices = [
            list(self.board.colors.keys()).index(color) for color in colors
        ]

        # Envoyer l'état initial
        await self.send_board_state(websocket)

        # Envoyer l'attribution des couleurs
        await websocket.send(
            json.dumps(
                {
                    "type": "color_assignment",
                    "colors": colors,
                    "indices": color_indices,
                    "index": player_index,
                    "nb_players": nb_players,
                    **({"color": colors[0]} if nb_players == 6 else {}),
                }
            )
        )

        # Mettre à jour l'état pour tous les clients
        await self._prepare_and_send_state()

    async def unregister(self, websocket):
        if websocket in self.clients:
            colors = self.clients.pop(websocket)
            self.available_colors = colors + self.available_colors

            await self._prepare_and_send_state()

            if len(self.available_colors) == 6:
                self._reset_game()
                await self.broadcast(
                    json.dumps(
                        {"type": "game_reset", "message": "Le jeu a été réinitialisé"}
                    )
                )

    async def _prepare_and_send_state(
        self, include_last_move=None, specific_client=None
    ):
        """Méthode utilitaire pour préparer et envoyer l'état du jeu"""
        state = self.board.send_state()
        state["type"] = "state"
        state["available_colors"] = self.available_colors

        if include_last_move:
            state["last_move"] = include_last_move

        for websocket in self.clients:
            for color in self.clients[websocket]:
                for player in state["players"]:
                    if player["color"] == color:
                        player["name"] = self.authenticated_users[websocket]

        # Envoyer soit à un client spécifique, soit à tous
        if specific_client:
            await specific_client.send(json.dumps(state))
        else:
            await self.broadcast(json.dumps(state))

    def _reset_game(self):
        """Réinitialise l'état du jeu"""
        self.board = Board(0)
        self.board.rl = True
        self.current_player_index = 0
        self.available_colors = list(self.board.colors.keys())

    async def send_board_state(self, websocket):
        logging.info(f"Sending state to specific client: {websocket.remote_address}")
        await self._prepare_and_send_state(specific_client=websocket)

    async def broadcast(self, message):
        logging.info(f"Broadcasting message: {message[:100]}...")
        websockets.broadcast(self.clients, message)

    async def handle_authentication(self, websocket, data):
        """Gère les requêtes d'authentification"""
        message_type = data["type"]
        if "username" in data:
            username = data["username"]
        if "password" in data:
            password = data["password"]

        if message_type == "create_account":
            success = self.db.create_user(username, password)
            if success:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "auth_response",
                            "success": True,
                            "message": "Compte créé avec succès",
                        }
                    )
                )
            else:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "auth_response",
                            "success": False,
                            "message": "Nom d'utilisateur déjà pris",
                        }
                    )
                )

        elif message_type == "login":
            # Vérifier si l'utilisateur est déjà connecté
            if username in self.connected_usernames:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "auth_response",
                            "success": False,
                            "message": "Cet utilisateur est déjà connecté sur une autre session",
                        }
                    )
                )
                return

            if self.db.verify_user(username, password):
                self.authenticated_users[websocket] = username
                self.connected_usernames.add(
                    username
                )  # Ajouter à la liste des connectés
                stats = self.db.get_user_stats(username)
                await websocket.send(
                    json.dumps(
                        {
                            "type": "auth_response",
                            "success": True,
                            "message": "Connexion réussie",
                            "username": username,
                            "stats": {"games_played": stats[0], "games_won": stats[1]},
                        }
                    )
                )
            else:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "auth_response",
                            "success": False,
                            "message": "Identifiants incorrects",
                        }
                    )
                )

        elif message_type == "logout":
            if websocket in self.authenticated_users:
                username = self.authenticated_users[websocket]
                self.connected_usernames.remove(
                    username
                )  # Retirer de la liste des connectés
                del self.authenticated_users[websocket]
                await websocket.send(
                    json.dumps(
                        {
                            "type": "auth_response",
                            "success": True,
                            "message": "Déconnexion réussie",
                        }
                    )
                )

    async def handler(self, websocket, path):
        logging.info(f"Nouvelle connexion établie : {websocket.remote_address}")
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                logging.info(f"Message reçu du client : {data}")

                # Gérer l'authentification
                if data["type"] in ["create_account", "login", "logout"]:
                    await self.handle_authentication(websocket, data)
                    continue

                if data["type"] == "start_game":
                    await self.start_game(websocket, data["nb_players"])
                elif data["type"] == "quit_game":
                    await self.quit_game(websocket)
                elif data["type"] == "request_state":
                    await self.send_board_state(websocket)
                elif data["type"] == "move":
                    async with self.lock:
                        piece_data = data["piece"]
                        move_to = data["move_to"]
                        captured_piece_to = data.get("captured_piece_to", None)

                        success = self.board.handle_client_move(
                            piece_data["color"],
                            (piece_data["q"], piece_data["r"]),
                            (move_to["q"], move_to["r"]),
                            (captured_piece_to["q"], captured_piece_to["r"])
                            if captured_piece_to
                            else None,
                        )

                        if success:
                            logging.info("Mouvement réussi")
                            await self._prepare_and_send_state(data)
                        else:
                            await websocket.send(
                                json.dumps(
                                    {"type": "error", "message": "Mouvement invalide"}
                                )
                            )
                elif data["type"] in ["undo", "redo"]:
                    logging.info(f"Commande {data['type']} reçue")
                    async with self.lock:
                        new_index = (
                            self.board.undo()
                            if data["type"] == "undo"
                            else self.board.redo()
                        )
                        if new_index is not None:
                            self.board.current_player_index = new_index
                        logging.info(f"{data['type']} effectué : {success}")
                        await self._prepare_and_send_state()
        finally:
            logging.info(f"Connexion fermée : {websocket.remote_address}")
            if websocket in self.authenticated_users:
                username = self.authenticated_users[websocket]
                self.connected_usernames.remove(
                    username
                )  # Nettoyer lors de la déconnexion
                del self.authenticated_users[websocket]
            await self.unregister(websocket)

    async def quit_game(self, websocket):
        logging.info(f"Client {websocket.remote_address} quitte la partie")

        # Gérer les couleurs du joueur qui quitte
        colors = self.clients.pop(websocket)
        self.waiting_clients.append(websocket)
        self.available_colors = colors + self.available_colors

        # Envoyer l'état mis à jour
        await self._prepare_and_send_state()

        # Réinitialiser le jeu si tous les joueurs sont partis
        if len(self.available_colors) == 6:
            self._reset_game()
            await self.broadcast(
                json.dumps(
                    {"type": "game_reset", "message": "Le jeu a été réinitialisé"}
                )
            )

    async def update_game_stats(self, winner_websocket):
        if winner_websocket in self.authenticated_users:
            username = self.authenticated_users[winner_websocket]
            self.db.update_stats(username, won=True)


async def main():
    port = int(os.environ.get("PORT", 8765))
    server = DjambiServer()
    async with websockets.serve(server.handler, "0.0.0.0", port):
        logging.info(f"Serveur lancé sur le port {port}")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
