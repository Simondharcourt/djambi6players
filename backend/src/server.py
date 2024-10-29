import asyncio
import json
import websockets
import os
from board import Board, COLORS

class DjambiServer:
    def __init__(self):
        self.board = Board(0)  # Initialiser le plateau de jeu
        self.board.rl = True
        self.clients = {}  # Dictionnaire pour stocker les clients avec leur couleur
        self.current_player_index = 0
        self.lock = asyncio.Lock()
        self.available_colors = list(COLORS.keys())
        self.waiting_clients = []  # Nouvelle liste pour les clients en attente

    async def register(self, websocket):
        # Au lieu d'attribuer directement une couleur, on met le client en attente
        self.waiting_clients.append(websocket)
        await websocket.send(json.dumps({"type": "waiting", "message": "En attente de démarrage de partie"}))

    async def start_game(self, websocket, nb_players):
        if websocket in self.waiting_clients:
            if nb_players == 2 and len(self.available_colors) >= 3:
                player_colors = [self.available_colors.pop(0) for _ in range(3)]
                self.clients[websocket] = player_colors
                color_indices = [list(COLORS.keys()).index(color) for color in player_colors]
                await self.send_board_state(websocket)
                print("player_colors", player_colors)
                await websocket.send(json.dumps({
                    "type": "color_assignment",
                    "colors": player_colors,
                    "indices": color_indices,
                    "index": color_indices[1],
                    "nb_players": 2,
                }))
                state = self.board.send_state()
                state['type'] = 'state'
                state['available_colors'] = self.available_colors
                await self.broadcast(json.dumps(state))
            
            elif nb_players == 6 and self.available_colors:
                self.waiting_clients.remove(websocket)
                color = self.available_colors.pop(0)
                self.clients[websocket] = [color]
                index_color = list(COLORS.keys()).index(color)
                await self.send_board_state(websocket)
                await websocket.send(json.dumps({
                    "type": "color_assignment",
                    "color": color,
                    "index": index_color,
                    "colors": [color],
                    "indices": [index_color],
                    "nb_players": 6
                }))
                state = self.board.send_state()
                state['type'] = 'state'
                state['available_colors'] = self.available_colors
                await self.broadcast(json.dumps(state))
                
            else:
                await websocket.send(json.dumps({"type": "error", "message": "La partie est pleine"}))

    async def unregister(self, websocket):
        if websocket in self.clients:
            colors = self.clients.pop(websocket)
            self.available_colors = colors + self.available_colors
            state = self.board.send_state()
            state['type'] = 'state'
            state['available_colors'] = self.available_colors
            await self.broadcast(json.dumps(state))
            if len(self.available_colors) == 6:
                self.board = Board(0)  # Réinitialiser le plateau de jeu
                self.board.rl = True
                self.current_player_index = 0
                self.available_colors = list(COLORS.keys())
                await self.broadcast(json.dumps({"type": "game_reset", "message": "Le jeu a été réinitialisé"}))

    async def send_board_state(self, websocket):
        print(f"Sending state to specific client: {websocket.remote_address}")
        state = self.board.send_state()
        state['type'] = 'state'
        state['available_colors'] = self.available_colors
        state_json = json.dumps(state)
        await websocket.send(state_json)

    async def broadcast(self, message):
        print(f"Broadcasting message: {message[:100]}...")
        websockets.broadcast(self.clients, message)

    async def handler(self, websocket, path):
        print(f"Nouvelle connexion établie : {websocket.remote_address}")
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"Message reçu du client : {data}")
                if data['type'] == 'start_game':
                    await self.start_game(websocket, data['nb_players'])
                elif data['type'] == 'quit_game':
                    await self.quit_game(websocket)
                elif data['type'] == 'request_state':
                    await self.send_board_state(websocket)
                elif data['type'] == 'move':
                    async with self.lock:
                        piece_data = data['piece']
                        move_to = data['move_to']
                        captured_piece_to = data.get('captured_piece_to', None)
                        # Utiliser la fonction handle_client_move pour gérer le mouvement
                        success = self.board.handle_client_move(
                            piece_data['color'],
                            (piece_data['q'], piece_data['r']),
                            (move_to['q'], move_to['r']),
                            (captured_piece_to['q'], captured_piece_to['r']) if captured_piece_to else None
                        )
                        if success:
                            print("Mouvement réussi")
                            state = self.board.send_state()
                            state['type'] = 'state'
                            state['available_colors'] = self.available_colors
                            state['last_move'] = data
                            await self.broadcast(json.dumps(state))
                        else:
                            # Mouvement invalide
                            error = {'type': 'error', 'message': 'Mouvement invalide'}
                            await websocket.send(json.dumps(error))
                elif data['type'] == 'undo':
                    print("Commande undo reçue")
                    async with self.lock:
                        success = self.board.undo()
                        print(f"Undo effectué : {success}")
                        state = self.board.send_state()
                        state['type'] = 'state'
                        state['available_colors'] = self.available_colors
                        await self.broadcast(json.dumps(state))
                        print("Nouvel état envoyé après undo")
                elif data['type'] == 'redo':
                    print("Commande redo reçue")
                    async with self.lock:
                        success = self.board.redo()
                        print(f"Redo effectué : {success}")
                        state = self.board.send_state()
                        state['type'] = 'state'
                        state['available_colors'] = self.available_colors
                        await self.broadcast(json.dumps(state))
                        print("Nouvel état envoyé après redo")
        finally:
            print(f"Connexion fermée : {websocket.remote_address}")
            await self.unregister(websocket)


    async def quit_game(self, websocket):
        print(f"Client {websocket.remote_address} quitte la partie")
        colors = self.clients.pop(websocket)
        self.waiting_clients.append(websocket)
        self.available_colors = colors + self.available_colors
        state = self.board.send_state()
        state['type'] = 'state'
        state['available_colors'] = self.available_colors
        await self.broadcast(json.dumps(state))
        if len(self.available_colors) == 6:
            self.board = Board(0)  # Réinitialiser le plateau de jeu
            self.board.rl = True
            self.current_player_index = 0
            self.available_colors = list(COLORS.keys())
            await self.broadcast(json.dumps({"type": "game_reset", "message": "Le jeu a été réinitialisé"}))


async def main():
    port = int(os.environ.get('PORT', 8765))
    server = DjambiServer()
    async with websockets.serve(server.handler, '0.0.0.0', port):
        print(f"Serveur lancé sur le port {port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
