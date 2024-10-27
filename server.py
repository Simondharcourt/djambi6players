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

    async def register(self, websocket):
        if self.available_colors:
            color = self.available_colors.pop(0)
            self.clients[websocket] = color
            index_color = list(COLORS.keys()).index(color)
            await self.send_board_state(websocket)
            await websocket.send(json.dumps({"type": "color_assignment", "color": color, "index": index_color}))
            state = self.board.to_json()
            state['type'] = 'state'
            state['available_colors'] = self.available_colors
            await self.broadcast(json.dumps(state))
        else:
            await websocket.send(json.dumps({"type": "error", "message": "La partie est pleine"}))
            await websocket.close()

    async def unregister(self, websocket):
        if websocket in self.clients:
            color = self.clients.pop(websocket)
            self.available_colors = [color] + self.available_colors
            if len(self.available_colors) == 6:
                self.board = Board(0)  # Réinitialiser le plateau de jeu
                self.board.rl = True
                self.current_player_index = 0
                self.available_colors = list(COLORS.keys())
                await self.broadcast(json.dumps({"type": "game_reset", "message": "Le jeu a été réinitialisé"}))

    async def send_board_state(self, websocket):
        state_json = self.board.send_state()
        state = json.loads(state_json)  # Convertir la chaîne JSON en dictionnaire
        state['type'] = 'state'
        state['available_colors'] = self.available_colors
        state_json = json.dumps(state)  # Reconvertir le dictionnaire en chaîne JSON
        print("Sending state:", state_json)  # Ajoutez cette ligne pour le débogage
        await websocket.send(state_json)  # Envoyer l'état au client

    async def broadcast(self, message):
        websockets.broadcast(self.clients, message)

    async def handler(self, websocket, path):
        print(f"Nouvelle connexion établie : {websocket.remote_address}")
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"Message reçu du client : {data}")
                if data['type'] == 'move':
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
                            state = self.board.to_json()
                            state['type'] = 'state'
                            state['available_colors'] = self.available_colors
                            await self.broadcast(json.dumps(state))
                        else:
                            # Mouvement invalide
                            error = {'type': 'error', 'message': 'Mouvement invalide'}
                            await websocket.send(json.dumps(error))
        finally:
            print(f"Connexion fermée : {websocket.remote_address}")
            await self.unregister(websocket)

async def main():
    port = int(os.environ.get('PORT', 8765))
    async with websockets.serve(DjambiServer().handler, '0.0.0.0', port):
        print(f"Serveur lancé sur le port {port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
