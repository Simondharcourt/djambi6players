import asyncio
import json
from aiohttp import web
import os
from board import Board

class DjambiServer:
    def __init__(self):
        self.board = Board(0)  # Initialiser le plateau
        self.players = {}
        self.current_player_index = 0

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        player_id = len(self.players)
        self.players[player_id] = ws

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data['type'] == 'move':
                        # Traiter le mouvement
                        # Mettre à jour le plateau
                        # Envoyer la mise à jour à tous les joueurs
                        await self.broadcast(json.dumps({
                            'type': 'update',
                            'board': self.board.to_json(),
                            'current_player': self.current_player_index
                        }))
        finally:
            del self.players[player_id]

        return ws

    async def broadcast(self, message):
        for ws in self.players.values():
            await ws.send_str(message)

server = DjambiServer()

async def websocket_handler(request):
    return await server.handle_websocket(request)

app = web.Application()
app.router.add_get('/ws', websocket_handler)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, port=port)
