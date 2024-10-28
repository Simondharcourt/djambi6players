// Classe gérant la communication WebSocket
import { GameState } from './GameState';

export class WebSocketClient {
    private ws: WebSocket;
    private gameState: GameState;

    constructor(gameState: GameState) {
        this.gameState = gameState;
        this.ws = new WebSocket('wss://djambi6players-105ba3b611ff.herokuapp.com');
    }

    public connect(): void {
        this.ws.onopen = this.onOpen.bind(this);
        this.ws.onerror = this.onError.bind(this);
        this.ws.onmessage = this.onMessage.bind(this);
        this.ws.onclose = this.onClose.bind(this);
    }

    private onOpen(): void {
        console.log('Connecté au serveur WebSocket');
    }

    private onError(error: Event): void {
        console.error('Erreur WebSocket:', error);
        this.gameState.initializeDefaultState();
    }

    private onMessage(event: MessageEvent): void {
        console.log("Message reçu du serveur:", event.data);
        const data = JSON.parse(event.data);
        // Gérer les différents types de messages
    }

    private onClose(): void {
        console.log('Déconnecté du serveur WebSocket');
    }

    // Méthodes pour envoyer des messages au serveur...
}
