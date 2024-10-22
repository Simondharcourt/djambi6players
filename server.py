import asyncio
import json
import websockets
from board import Board

class DjambiServer:
    def __init__(self):
        self.board = Board(0)  # Initialiser le plateau de jeu
        self.clients = set()
        self.current_player_index = 0
        self.lock = asyncio.Lock()

    async def register(self, websocket):
        self.clients.add(websocket)
        await self.send_board_state(websocket)

    async def unregister(self, websocket):
        self.clients.remove(websocket)

    async def send_board_state(self, websocket):
        state = self.board.to_json()
        state['type'] = 'state'
        await websocket.send(json.dumps(state))

    async def broadcast(self, message):
        websockets.broadcast(self.clients, message)

    async def handler(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'move':
                    async with self.lock:
                        piece_data = data['piece']
                        move_to = data['move_to']
                        piece = self.board.get_piece_at(piece_data['q'], piece_data['r'])

                        if piece and piece.color == piece_data['color'] and piece.piece_class == piece_data['piece_class']:
                            # Vérifier si c'est le tour du joueur
                            if piece.color == self.board.players[self.board.current_player_index].color:
                                moved = self.board.move_piece(piece, move_to['q'], move_to['r'])
                                if moved:
                                    self.current_player_index = (self.current_player_index + 1) % len(self.board.players)
                                    self.board.save_state(self.current_player_index)
                                    # Envoyer le nouvel état à tous les clients
                                    state = self.board.to_json()
                                    state['type'] = 'state'
                                    await self.broadcast(json.dumps(state))
                                else:
                                    # Mouvement invalide
                                    error = {'type': 'error', 'message': 'Mouvement invalide'}
                                    await websocket.send(json.dumps(error))
                            else:
                                # Pas le tour du joueur
                                error = {'type': 'error', 'message': 'Ce n\'est pas votre tour'}
                                await websocket.send(json.dumps(error))
                        else:
                            # Pièce non trouvée ou données incorrectes
                            error = {'type': 'error', 'message': 'Pièce invalide'}
                            await websocket.send(json.dumps(error))
        finally:
            await self.unregister(websocket)

start_server = websockets.serve(DjambiServer().handler, '0.0.0.0', 8765)

print("Serveur lancé sur le port 8765")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()