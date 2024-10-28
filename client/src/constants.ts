export interface ColorMap {
    [key: string]: string;
}

export interface Direction {
    [index: number]: [number, number];
}

export const BOARD_SIZE = 7;
export const HEX_RADIUS = 35;
export const PIECE_RADIUS = 25;
export const SIZE_IMAGE = 50;
export const VERTICAL_OFFSET = 100;

// Les dimensions de la fenêtre devront être initialisées dynamiquement
// avec le canvas, donc on les déclare comme variables
export let WINDOW_WIDTH: number;
export let WINDOW_HEIGHT: number;

export const COLORS: ColorMap = {
    'purple': 'rgb(128, 0, 128)',
    'blue': 'rgb(0, 0, 255)',
    'red': 'rgb(255, 0, 0)',
    'pink': 'rgb(255, 105, 180)',
    'yellow': 'rgb(255, 255, 0)',
    'green': 'rgb(0, 255, 0)',
} as const;

export const NAMES: ColorMap = {
    'rgb(128, 0, 128)': 'purple',
    'rgb(0, 0, 255)': 'blue',
    'rgb(255, 0, 0)': 'red',
    'rgb(255, 105, 180)': 'pink',
    'rgb(255, 255, 0)': 'yellow',
    'rgb(0, 255, 0)': 'green',
} as const;

export const ADJACENT_DIRECTIONS: [number, number][] = [
    [1, 0], [-1, 0], [0, 1], [0, -1], [1, -1], [-1, 1],
];

export const DIAG_DIRECTIONS: [number, number][] = [
    [2, -1], [1, -2], [-1, -1], [-2, 1], [-1, 2], [1, 1]
];

export const ALL_DIRECTIONS: [number, number][] = [...ADJACENT_DIRECTIONS, ...DIAG_DIRECTIONS];

// Fonction pour initialiser les dimensions de la fenêtre
export function initializeWindowDimensions(canvas: HTMLCanvasElement): void {
    WINDOW_WIDTH = canvas.width;
    WINDOW_HEIGHT = canvas.height;
}
