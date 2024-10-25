import asyncio
import json
import websockets
from board import Board, COLORS

class DjambiServer:
    def __init__(self):
        self.board = Board(0)  # Initialiser le plateau de jeu
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
            # Envoyer la couleur assignée au client
            await websocket.send(json.dumps({"type": "color_assignment", "color": color, "index": index_color}))
        else:
            await websocket.send(json.dumps({"type": "error", "message": "La partie est pleine"}))
            await websocket.close()

    async def unregister(self, websocket):
        if websocket in self.clients:
            color = self.clients.pop(websocket)
            self.available_colors.append(color)

    async def send_board_state(self, websocket):
        state_json = self.board.send_state()
        state = json.loads(state_json)  # Convertir la chaîne JSON en dictionnaire
        state['type'] = 'state'
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
                        piece = self.board.get_piece_at(piece_data['q'], piece_data['r'])
                        
                        print("Piece", piece_data['q'], piece_data['r'], "to", move_to['q'], move_to['r'])
                        
                        print(self.board.players[self.board.current_player_index].color)
                        
                        if piece and piece.color == piece_data['color'] and piece.piece_class == piece_data['piece_class']:
                            # Vérifier si c'est le tour du joueur
                            if piece.color == self.board.players[self.board.current_player_index].color:
                                moved = self.board.move_piece(piece, move_to['q'], move_to['r'])
                                if moved:
                                    print("Moved piece", piece_data['q'], piece_data['r'], "to", move_to['q'], move_to['r'])
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
            print(f"Connexion fermée : {websocket.remote_address}")
            await self.unregister(websocket)

start_server = websockets.serve(DjambiServer().handler, '0.0.0.0', 8765)

print("Serveur lancé sur le port 8765")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
