import asyncio
import websockets
import pygame
import json
from board import Board

class DjambiClient:
    def __init__(self):
        self.board = None
        self.current_player_index = 0
        # Initialiser Pygame ici

    async def connect(self):
        self.websocket = await websockets.connect("wss://djambi6players.herokuapp.com/ws")
        asyncio.create_task(self.receive_messages())

    async def receive_messages(self):
        async for message in self.websocket:
            data = json.loads(message)
            if data['type'] == 'update':
                self.board = Board.from_json(data['board'])
                self.current_player_index = data['current_player']
                # Mettre à jour l'affichage Pygame

    async def send_move(self, move):
        await self.websocket.send(json.dumps({
            'type': 'move',
            'move': move
        }))

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.connect())
        # Boucle principale Pygame ici

client = DjambiClient()
client.run()
