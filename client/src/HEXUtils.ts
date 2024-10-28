// Classe utilitaire pour les calculs liés aux hexagones
export class HEXUtils {
    // Constantes
    private static readonly BOARD_SIZE = 7;
    private static readonly HEX_RADIUS = 35;
    static readonly PIECE_RADIUS = 25;
    static readonly SIZE_IMAGE = 50;
    private static readonly VERTICAL_OFFSET = 100;
    static readonly WINDOW_WIDTH = window.innerWidth;
    static readonly WINDOW_HEIGHT = window.innerHeight;

    // Méthodes pour convertir les coordonnées, vérifier les positions, etc.

    public static hexToPixel(q: number, r: number, clientAssignedIndex: number): [number, number] {
        const x = this.HEX_RADIUS * 3 / 2 * q;
        const y = this.HEX_RADIUS * Math.sqrt(3) * (r + q / 2);

        // Appliquer la rotation de pi/3
        const angle = -Math.PI / 3 * (clientAssignedIndex + 2);
        const rotatedX = x * Math.cos(angle) - y * Math.sin(angle);
        const rotatedY = x * Math.sin(angle) + y * Math.cos(angle);

        return [
            rotatedX + this.WINDOW_WIDTH / 2,
            rotatedY + this.WINDOW_HEIGHT / 2 - this.VERTICAL_OFFSET
        ];
    }

    public static pixelToHex(x: number, y: number, clientAssignedIndex: number): [number, number] {
        x -= this.WINDOW_WIDTH / 2;
        y -= (this.WINDOW_HEIGHT / 2 - this.VERTICAL_OFFSET);
        
        const angle = Math.PI / 3 * (clientAssignedIndex + 2);
        const unrotatedX = x * Math.cos(angle) - y * Math.sin(angle);
        const unrotatedY = x * Math.sin(angle) + y * Math.cos(angle);
        
        const q = (2/3) * unrotatedX / this.HEX_RADIUS;
        const r = (-1/3) * unrotatedX / this.HEX_RADIUS + Math.sqrt(3)/3 * unrotatedY / this.HEX_RADIUS;

        return [Math.round(q), Math.round(r)];
    }

    public static isWithinBoard(q: number, r: number): boolean {
        const s = -q - r;
        return Math.abs(q) < this.BOARD_SIZE && 
               Math.abs(r) < this.BOARD_SIZE && 
               Math.abs(s) < this.BOARD_SIZE;
    }

    public static getHexCorners(x: number, y: number): [number, number][] {
        const corners: [number, number][] = [];
        for (let i = 0; i < 6; i++) {
            const angle = 2 * Math.PI / 6 * i;
            corners.push([
                x + this.HEX_RADIUS * Math.cos(angle),
                y + this.HEX_RADIUS * Math.sin(angle)
            ]);
        }
        return corners;
    }

    public static drawHexagon(ctx: CanvasRenderingContext2D, x: number, y: number): void {
        const corners = this.getHexCorners(x, y);
        ctx.strokeStyle = 'white';
        ctx.beginPath();
        ctx.moveTo(corners[0][0], corners[0][1]);
        for (let i = 1; i < corners.length; i++) {
            ctx.lineTo(corners[i][0], corners[i][1]);
        }
        ctx.closePath();
        ctx.stroke();
    }
}
