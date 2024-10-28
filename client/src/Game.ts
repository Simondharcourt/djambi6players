// Classe principale du jeu
import { GameBoard } from './GameBoard';
import { GameState } from './GameState';
import { WebSocketClient } from './WebSocketClient';

class Game {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private gameState: GameState;
    private gameBoard: GameBoard;
    private webSocketClient: WebSocketClient;

    constructor() {
        this.canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
        this.ctx = this.canvas.getContext('2d')!;
        this.gameState = new GameState();
        this.gameBoard = new GameBoard(this.ctx, this.gameState);
        this.webSocketClient = new WebSocketClient(this.gameState);

        this.initialize();
    }

    private initialize(): void {
        this.canvas.addEventListener('click', this.onCanvasClick.bind(this));
        this.webSocketClient.connect();
        this.render();
    }

    private onCanvasClick(event: MouseEvent): void {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        this.gameBoard.handleClick(x, y);
    }

    private render(): void {
        requestAnimationFrame(this.render.bind(this));
        this.gameBoard.draw();
    }
}

new Game();
