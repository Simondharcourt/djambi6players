// Classe responsable du dessin du plateau et des pièces
import { GameState } from './GameState';
import { Piece } from './Piece';
import { PieceImages } from './PieceImages';
import { HEXUtils } from './HEXUtils';

import { 
    BOARD_SIZE, 
} from './constants';

export class GameBoard {
    private ctx: CanvasRenderingContext2D;
    private gameState: GameState;
    private pieceImages: PieceImages;
    private selectedPiece: Piece | null = null;
    private possibleMoves: Array<[number, number]> = [];
    private availableCells: Array<[number, number]> = [];

    constructor(ctx: CanvasRenderingContext2D, gameState: GameState) {
        this.ctx = ctx;
        this.gameState = gameState;
        this.pieceImages = new PieceImages(this.draw.bind(this));
    }

    public draw(): void {
        this.drawBoard();
        this.drawPieces();
        this.drawSelectedPieceHalo();
        this.drawPossibleMoves();
        this.drawAvailableCells();
        this.drawPlayerTurn();
    }

    private drawBoard(): void {
        this.ctx.fillStyle = 'black';
        this.ctx.fillRect(0, 0, HEXUtils.WINDOW_WIDTH, HEXUtils.WINDOW_HEIGHT);

        // Dessiner les hexagones du plateau
        for (let q = -BOARD_SIZE + 1; q < BOARD_SIZE; q++) {
            for (let r = -BOARD_SIZE + 1; r < BOARD_SIZE; r++) {
                if (HEXUtils.isWithinBoard(q, r)) {
                    const [x, y] = HEXUtils.hexToPixel(q, r);
                    this.drawHexagon(x, y);
                    // Case centrale
                    if (q === 0 && r === 0) {
                        this.fillHexagon(x, y, 'white');
                    }
                }
            }
        }
    }

    private drawHexagon(x: number, y: number): void {
        const corners = HEXUtils.getHexCorners(x, y);
        this.ctx.strokeStyle = 'white';
        this.ctx.beginPath();
        this.ctx.moveTo(corners[0][0], corners[0][1]);
        for (let i = 1; i < corners.length; i++) {
            this.ctx.lineTo(corners[i][0], corners[i][1]);
        }
        this.ctx.closePath();
        this.ctx.stroke();
    }

    private fillHexagon(x: number, y: number, color: string): void {
        const corners = HEXUtils.getHexCorners(x, y);
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.moveTo(corners[0][0], corners[0][1]);
        for (let i = 1; i < corners.length; i++) {
            this.ctx.lineTo(corners[i][0], corners[i][1]);
        }
        this.ctx.closePath();
        this.ctx.fill();
    }

    private drawPieces(): void {
        if (this.gameState && this.gameState.pieces) {
            this.gameState.pieces.forEach(piece => {
                const [x, y] = HEXUtils.hexToPixel(piece.q, piece.r);
                
                // Déterminer la couleur de la pièce
                let pieceColor = `rgb(${piece.color[0]}, ${piece.color[1]}, ${piece.color[2]})`;
                let pieceName = this.gameState.NAMES[pieceColor];
                
                if (piece.is_dead) {
                    pieceColor = 'rgb(100, 100, 100)';
                } else if (Array.isArray(piece.color) && !this.gameState.available_colors.includes(pieceName)) {
                    console.log("pieceName", pieceName);
                } else {
                    pieceColor = 'rgb(255, 255, 255)';
                }

                // Dessiner le cercle de la pièce
                this.ctx.fillStyle = pieceColor;
                this.ctx.beginPath();
                this.ctx.arc(x, y, this.gameState.PIECE_RADIUS, 0, 2 * Math.PI);
                this.ctx.fill();

                // Dessiner l'image de la pièce
                if (this.pieceImages.areAllLoaded()) {
                    if (!piece.is_dead) {
                        const img = this.pieceImages.getImage(piece.piece_class);
                        this.ctx.drawImage(
                            img, 
                            x - this.gameState.SIZE_IMAGE / 2, 
                            y - this.gameState.SIZE_IMAGE / 2, 
                            this.gameState.SIZE_IMAGE, 
                            this.gameState.SIZE_IMAGE
                        );
                    }
                }
            });
        }
    }

    private drawSelectedPieceHalo(): void {
        if (this.selectedPiece) {
            const [x, y] = HEXUtils.hexToPixel(this.selectedPiece.q, this.selectedPiece.r);
            this.ctx.strokeStyle = 'yellow';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(x, y, this.gameState.PIECE_RADIUS + 5, 0, 2 * Math.PI);
            this.ctx.stroke();
        }
    }

    private drawPossibleMoves(): void {
        if (this.selectedPiece && this.possibleMoves.length > 0) {
            this.ctx.fillStyle = 'rgba(125, 125, 125, 0.9)';
            for (const [q, r] of this.possibleMoves) {
                const [x, y] = HEXUtils.hexToPixel(q, r);
                this.ctx.beginPath();
                this.ctx.arc(x, y, 10, 0, 2 * Math.PI);
                this.ctx.fill();
            }
        }
    }

    private drawAvailableCells(): void {
        this.ctx.fillStyle = 'rgba(125, 125, 125, 0.9)';
        for (const [q, r] of this.availableCells) {
            const [x, y] = HEXUtils.hexToPixel(q, r);
            this.ctx.beginPath();
            this.ctx.arc(x, y, 10, 0, 2 * Math.PI);
            this.ctx.fill();
        }
    }

    private drawPlayerTurn(): void {
        // Dessiner le tour du joueur
    }

    public handleClick(x: number, y: number): void {
        // Gérer le clic sur le plateau
    }
}
