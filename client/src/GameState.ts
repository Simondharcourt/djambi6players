// Classe représentant l'état actuel du jeu
import { Piece } from './Piece';

export class GameState {
    public pieces: Piece[] = [];
    public players: any[] = [];
    public currentPlayerIndex: number = 0;
    // Autres propriétés...

    constructor() {
        this.initializeDefaultState();
    }

    private initializeDefaultState(): void {
        const startPositions = [
        // Pièces violettes (en bas à gauche)
        [-5, -1, 'purple', 'assassin'], [-4, -2, 'purple', 'militant'], [-6, 0, 'purple', 'chief'],
        [-4, -1, 'purple', 'militant'], [-5, 0, 'purple', 'diplomat'], [-4, 0, 'purple', 'necromobile'],
        [-5, 1, 'purple', 'militant'], [-6, 1, 'purple', 'reporter'], [-6, 2, 'purple', 'militant'],
        
        // Pièces bleues (en haut)
        [0, -6, 'blue', 'chief'], [1, -6, 'blue', 'reporter'], [2, -6, 'blue', 'militant'],
        [0, -5, 'blue', 'diplomat'], [-1, -4, 'blue', 'militant'], [-2, -4, 'blue', 'militant'],
        [0, -4, 'blue', 'necromobile'], [1, -5, 'blue', 'militant'], [-1, -5, 'blue', 'assassin'],
        
        // Pièces rouges (en bas à droite)
        [6, -4, 'red', 'militant'], [6, -5, 'red', 'assassin'], [6, -6, 'red', 'chief'],
        [5, -6, 'red', 'reporter'], [4, -6, 'red', 'militant'], [5, -5, 'red', 'diplomat'],
        [4, -4, 'red', 'necromobile'], [4, -5, 'red', 'militant'], [5, -4, 'red', 'militant'],

        // Pièces roses (en haut à droite)
        [6, -2, 'pink', 'militant'], [5, -1, 'pink', 'militant'], [6, -1, 'pink', 'assassin'], [4, 2, 'pink', 'militant'],
        [5, 0, 'pink', 'diplomat'], [4, 0, 'pink', 'necromobile'], [6, 0, 'pink', 'chief'],
        [5, 1, 'pink', 'reporter'], [4, 1, 'pink', 'militant'],

        // Pièces jaunes (en bas)
        [0, 5, 'yellow', 'diplomat'], [-1, 5, 'yellow', 'militant'], [-2, 6, 'yellow', 'militant'],
        [-1, 6, 'yellow', 'assassin'], [1, 5, 'yellow', 'reporter'], [0, 6, 'yellow', 'chief'],
        [0, 4, 'yellow', 'necromobile'], [2, 4, 'yellow', 'militant'], [1, 4, 'yellow', 'militant'],
        
        // Pièces vertes (en haut à gauche)
        [-5, 6, 'green', 'assassin'], [-4, 6, 'green', 'militant'], [-6, 6, 'green', 'chief'],
        [-6, 5, 'green', 'reporter'], [-6, 4, 'green', 'militant'], [-5, 5, 'green', 'diplomat'],
        [-4, 5, 'green', 'militant'], [-5, 4, 'green', 'militant'], [-4, 4, 'green', 'necromobile'],
    ];

        this.pieces = startPositions.map(([q, r, color, pieceClass]) => 
            new Piece(q, r, color, pieceClass)
        );

        this.players = [
            {color: 'purple'},
            {color: 'blue'},
            {color: 'red'},
            {color: 'pink'},
            {color: 'yellow'},
            {color: 'green'}
        ];

        this.currentPlayerIndex = 0;
    }

    public getPieceAt(q: number, r: number): Piece | undefined {
        return this.pieces.find(p => p.q === q && p.r === r);
    }
}
