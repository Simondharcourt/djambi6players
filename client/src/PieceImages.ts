// Classe pour charger et gérer les images des pièces
export class PieceImages {
    private images: { [key: string]: HTMLImageElement } = {};
    private imagesLoaded: number = 0;
    private totalImages: number;
    private onAllImagesLoaded: () => void;

    constructor(onAllImagesLoaded: () => void) {
        this.onAllImagesLoaded = onAllImagesLoaded;
        const pieceClasses = ['assassin', 'chief', 'diplomat', 'militant', 'necromobile', 'reporter'];
        this.totalImages = pieceClasses.length;
        pieceClasses.forEach(cl => this.loadImage(cl));
    }

    private loadImage(cl: string): void {
        const img = new Image();
        img.src = `assets/${cl}.svg`;
        img.onload = this.onImageLoad.bind(this);
        img.onerror = () => console.error(`Erreur de chargement de l'image ${cl}`);
        this.images[cl] = img;
    }

    private onImageLoad(): void {
        this.imagesLoaded++;
        if (this.imagesLoaded === this.totalImages) {
            this.onAllImagesLoaded();
        }
    }

    public getImage(pieceClass: string): HTMLImageElement | undefined {
        return this.images[pieceClass];
    }
}
