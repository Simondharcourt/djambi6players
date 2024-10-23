// Variables du jeu
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const BOARD_SIZE = 7;
const HEX_RADIUS = 35;
const WINDOW_WIDTH = canvas.width;
const WINDOW_HEIGHT = canvas.height;
const PIECE_RADIUS = 25;
const SIZE_IMAGE = 50;
const VERTICAL_OFFSET = 100;
const COLORS = {
    'purple': 'rgb(128, 0, 128)',
    'blue': 'rgb(0, 0, 255)',
    'red': 'rgb(255, 0, 0)',
    'pink': 'rgb(255, 105, 180)',
    'yellow': 'rgb(255, 255, 0)',
    'green': 'rgb(0, 255, 0)',
};
const NAMES = {
    'rgb(128, 0, 128)': 'Violet',
    'rgb(0, 0, 255)': 'Bleu',
    'rgb(255, 0, 0)': 'Rouge',
    'rgb(255, 105, 180)': 'Rose',
    'rgb(255, 255, 0)': 'Jaune',
    'rgb(0, 255, 0)': 'Vert',
    'rgb(100, 100, 100)': 'Mort',
};
const ADJACENT_DIRECTIONS = [
    [1, 0], [-1, 0], [0, 1], [0, -1], [1, -1], [-1, 1],
];
const DIAG_DIRECTIONS = [
    [2, -1], [1, -2], [-1, -1], [-2, 1], [-1, 2], [1, 1]
];
const ALL_DIRECTIONS = ADJACENT_DIRECTIONS.concat(DIAG_DIRECTIONS);

// Chargement des images des pièces
const pieceImages = {};
const pieceClasses = ['assassin', 'chief', 'diplomat', 'militant', 'necromobile', 'reporter'];
let imagesLoaded = 0;
let allImagesLoaded = false;
pieceClasses.forEach(cl => {
    const img = new Image();
    img.src = `assets/${cl}.svg`;
    img.onload = () => {
        console.log(`Image ${cl} chargée`);
        imagesLoaded++;
        if (imagesLoaded === pieceClasses.length) {
            console.log('Toutes les images sont chargées');
            allImagesLoaded = true;
            draw(); // Redessinez une fois que toutes les images sont chargées
        }
    };
    img.onerror = () => console.error(`Erreur de chargement de l'image ${cl}`);
    pieceImages[cl] = img;
});

// Variables de jeu
let gameState = null;
let selectedPiece = null;
let possibleMoves = [];

// Ajouter le WebSocket
const ws = new WebSocket('ws://localhost:8765');  // Remplacez par l'URL de votre serveur

ws.onopen = function() {
    console.log('Connecté au serveur WebSocket');
    // Demander l'état initial
    ws.send(JSON.stringify({type: 'get_initial_state'}));
};

ws.onerror = function(error) {
    console.error('Erreur WebSocket:', error);
    initializeDefaultState();
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'state') {
        // Mettre à jour l'état du jeu
        gameState = data;
        draw();
    } else if (data.type === 'error') {
        alert(data.message);
    }
};

ws.onclose = function() {
    console.log('Déconnecté du serveur WebSocket');
};

// Fonction pour convertir les coordonnées hexagonales en pixels
function hexToPixel(q, r) {
    const x = HEX_RADIUS * 3 / 2 * q;
    const y = HEX_RADIUS * Math.sqrt(3) * (r + q / 2);
    return [
        x + WINDOW_WIDTH / 2,
        y + WINDOW_HEIGHT / 2 - VERTICAL_OFFSET
    ];
}

// Fonction pour dessiner le plateau
function drawBoard() {
    // Remplir tout le canvas en noir
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT);

    // Dessiner les hexagones du plateau
    for (let q = -BOARD_SIZE + 1; q < BOARD_SIZE; q++) {
        for (let r = -BOARD_SIZE + 1; r < BOARD_SIZE; r++) {
            if (isWithinBoard(q, r)) {
                const [x, y] = hexToPixel(q, r);
                drawHexagon(x, y);
                // Case centrale
                if (q === 0 && r === 0) {
                    fillHexagon(x, y, 'white');
                }
            }
        }
    }
}

// Fonction pour dessiner un hexagone
function drawHexagon(x, y) {
    const corners = getHexCorners(x, y);
    ctx.strokeStyle = 'white';
    ctx.beginPath();
    ctx.moveTo(corners[0][0], corners[0][1]);
    for (let i = 1; i < corners.length; i++) {
        ctx.lineTo(corners[i][0], corners[i][1]);
    }
    ctx.closePath();
    ctx.stroke();
}

// Fonction pour remplir un hexagone
function fillHexagon(x, y, color) {
    const corners = getHexCorners(x, y);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(corners[0][0], corners[0][1]);
    for (let i = 1; i < corners.length; i++) {
        ctx.lineTo(corners[i][0], corners[i][1]);
    }
    ctx.closePath();
    ctx.fill();
}

// Fonction pour obtenir les coins d'un hexagone
function getHexCorners(x, y) {
    const corners = [];
    for (let i = 0; i < 6; i++) {
        const angleRad = Math.PI / 180 * (60 * i);
        const cornerX = x + HEX_RADIUS * Math.cos(angleRad);
        const cornerY = y + HEX_RADIUS * Math.sin(angleRad);
        corners.push([cornerX, cornerY]);
    }
    return corners;
}

// Fonction pour vérifier si une case est dans le plateau
function isWithinBoard(q, r) {
    const s = -q - r;
    return Math.abs(q) < BOARD_SIZE && Math.abs(r) < BOARD_SIZE && Math.abs(s) < BOARD_SIZE;
}

// Fonction pour dessiner les pièces
function drawPieces() {
    if (gameState && gameState.pieces) {
        gameState.pieces.forEach(piece => {
            const [x, y] = hexToPixel(piece.q, piece.r);
            // Déterminer la couleur à utiliser
            let pieceColor;
            if (piece.is_dead) {
                pieceColor = 'rgb(100, 100, 100)'; // Gris pour les pièces mortes
            } else if (Array.isArray(piece.color)) {
                pieceColor = `rgb(${piece.color[0]}, ${piece.color[1]}, ${piece.color[2]})`;
            } else {
                pieceColor = COLORS[piece.color] || piece.color;
            }
            // Dessiner le cercle de la pièce
            ctx.fillStyle = pieceColor;
            ctx.beginPath();
            ctx.arc(x, y, PIECE_RADIUS, 0, 2 * Math.PI);
            ctx.fill();
            // Dessiner l'image de la pièce
            const img = pieceImages[piece.piece_class];
            if (allImagesLoaded) {
                ctx.drawImage(img, x - SIZE_IMAGE / 2, y - SIZE_IMAGE / 2, SIZE_IMAGE, SIZE_IMAGE);
            }
        });
    }
}

// Fonction pour convertir les coordonnées pixel en coordonnées hexagonales
function pixelToHex(x, y) {
    x = (x - WINDOW_WIDTH / 2) / (HEX_RADIUS * 3 / 2);
    y = (y - (WINDOW_HEIGHT / 2 - VERTICAL_OFFSET)) / (HEX_RADIUS * Math.sqrt(3));
    const q = x;
    const r = y - x / 2;
    return [Math.round(q), Math.round(r)];
}

// Gestion des événements de la souris
canvas.addEventListener('click', (event) => {
    if (gameState) {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const [q, r] = pixelToHex(x, y);

        if (selectedPiece) {
            sendMove(selectedPiece, q, r);
            selectedPiece = null;
            possibleMoves = [];
        } else {
            selectPiece(q, r);
        }
    }
});

// Fonction pour sélectionner une pièce
function selectPiece(q, r) {
    if (gameState) {
        const piece = gameState.pieces.find(p => p.q === q && p.r === r && !p.is_dead && p.color === getCurrentPlayerColor());
        if (piece) {
            selectedPiece = piece;
            // Optionnel : obtenir les mouvements possibles
            // getPossibleMoves(piece);
        }
    }
}

// Fonction pour obtenir la couleur du joueur actuel
function getCurrentPlayerColor() {
    if (gameState && gameState.players) {
        const playerIndex = gameState.current_player_index;
        return gameState.players[playerIndex].color;
    }
    return null;
}

// Fonction pour envoyer un mouvement au serveur
function sendMove(piece, new_q, new_r) {
    const action = {
        'type': 'move',
        'piece': {
            'q': piece.q,
            'r': piece.r,
            'piece_class': piece.piece_class,
            'color': piece.color
        },
        'move_to': {
            'q': new_q,
            'r': new_r
        }
    };

    ws.send(JSON.stringify(action));
}

// Fonction pour dessiner l'indicateur de tour du joueur
function drawPlayerTurn() {
    if (gameState && gameState.players) {
        const playerColor = getCurrentPlayerColor();
        const colorName = NAMES[playerColor];

        // Configurer le texte
        ctx.font = '24px Arial';
        ctx.fillStyle = 'white';
        const text = `Tour du joueur : ${colorName}`;
        ctx.fillText(text, 20, 30);

        // Dessiner un cercle de la couleur du joueur
        ctx.beginPath();
        ctx.arc(200, 25, 15, 0, 2 * Math.PI);
        ctx.fillStyle = playerColor;
        ctx.fill();
    }
}

// Fonction principale de dessin
function draw() {
    console.log('Fonction draw appelée');
    console.log('État du jeu :', gameState);
    drawBoard();
    if (gameState && gameState.pieces) {
        console.log('Nombre de pièces :', gameState.pieces.length);
        drawPieces();
    } else {
        console.log('Aucune pièce à dessiner');
    }
    if (selectedPiece) {
        // Optionnel : dessiner les mouvements possibles
        // drawPossibleMoves();
    }
    drawPlayerTurn(); // Ajouter cette ligne
}
// Fonction pour initialiser un état par défaut
function initializeDefaultState() {
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

    gameState = {
        pieces: startPositions.map(([q, r, color, piece_class]) => ({
            q, r, color: COLORS[color], piece_class, is_dead: false
        })),
        players: [
            {color: COLORS.purple},
            {color: COLORS.blue},
            {color: COLORS.red},
            {color: COLORS.pink},
            {color: COLORS.yellow},
            {color: COLORS.green}
        ],
        current_player_index: 0
    };

    console.log('État initial du jeu créé avec', gameState.pieces.length, 'pièces');
    draw();
}

// Appeler draw() immédiatement pour dessiner au moins le plateau
draw();
