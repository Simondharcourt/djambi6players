// Classe représentant une pièce du jeu
export class Piece {
    constructor(
        public q: number,
        public r: number,
        public color: string,
        public pieceClass: string,
        public isDead: boolean = false
    ) {}

    // Méthodes liées à la pièce...
}
