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
        imagesLoaded++;
        if (imagesLoaded === pieceClasses.length) {
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
let targetedPiece = null;
let possibleMoves = [];
let availableCells = []; // Ajoutez cette variable globale

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
    console.log("Message reçu du serveur:", data);
    if (data.type === 'state') {
        gameState = data;
        console.log("Nouvel état du jeu:", gameState);
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

function drawPossibleMoves() {
    if (selectedPiece && possibleMoves.length > 0) {
        ctx.fillStyle = 'rgba(125, 125, 125, 0.9)';
        for (const [q, r] of possibleMoves) {
            const [x, y] = hexToPixel(q, r);
            ctx.beginPath();
            ctx.arc(x, y, 10, 0, 2 * Math.PI);
            ctx.fill();
        }
    }
}

function drawAvailableCells() {
    ctx.fillStyle = 'rgba(125, 125, 125, 0.9)'; // Blanc semi-transparent
    for (const [q, r] of availableCells) {
        const [x, y] = hexToPixel(q, r);
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, 2 * Math.PI);
        ctx.fill();
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
            if (selectedPiece.q === q && selectedPiece.r === r) {
                // Si on reclique sur la pièce sélectionnée, on la désélectionne
                selectedPiece = null;
                possibleMoves = [];
                availableCells = []; // Réinitialisez les cellules disponibles
            } else if (possibleMoves.some(move => move[0] === q && move[1] === r)) {
                const targetPiece = getPieceAt(q, r);
                if (targetPiece && selectedPiece.piece_class !== 'assassin') {
                    // La case est occupée, on capture la pièce
                    targetedPiece = getPieceAt(q, r);
                    availableCells = findAvailableCells();
                    availableCells.push([selectedPiece.q, selectedPiece.r]);
                } else {
                    // La case est libre, on déplace simplement la pièce
                    console.log(selectedPiece, q, r, null, null);
                    sendMove(selectedPiece, q, r, null, null);
                    availableCells = []; // Réinitialisez les cellules disponibles
                    selectedPiece = null;
                }
                possibleMoves = [];
            } else if (availableCells.some(cell => cell[0] === q && cell[1] === r)) {
                // Si on clique sur une case disponible après une capture
                console.log(selectedPiece, targetedPiece.q, targetedPiece.r, q, r);
                sendMove(selectedPiece, targetedPiece.q, targetedPiece.r, q, r);
                selectedPiece = null;
                possibleMoves = [];
                availableCells = []; // Réinitialisez les cellules disponibles
            } else {
                // Si on clique ailleurs, on vérifie si on a cliqué sur une autre pièce
                selectPiece(q, r);
                availableCells = [];
            }
        } else {
            // Si aucune pièce n'est sélectionnée, on essaie d'en sélectionner une
            selectPiece(q, r);
            availableCells = [];
        }
        draw(); // Redessiner le plateau après chaque action
    }
});



// Fonction pour sélectionner une pièce
function selectPiece(q, r) {
    if (gameState) {
        const piece = gameState.pieces.find(p => p.q === q && p.r === r && !p.is_dead);
        if (piece) {
            selectedPiece = piece;
            possibleMoves = calculatePossibleMoves(piece);
            draw(); // Redessiner le plateau pour afficher les mouvements possibles
        }
    }
}

function calculatePossibleMoves(piece) {
    if (piece.is_dead) {
        return [];
    }
    const possibleMoves = [];
    if (piece.piece_class === 'militant') {
        console.log("Déplacement spécial pour le militant");
        // Déplacement spécial pour le militant
        for (const [dq, dr] of ADJACENT_DIRECTIONS) {
            // Déplacement de 1 ou 2 cases adjacentes
            for (let step = 1; step <= 2; step++) {
                const newQ = piece.q + dq * step;
                const newR = piece.r + dr * step;
                const occupyingPiece = getPieceAt(newQ, newR);

                if (isValidMove(newQ, newR, piece)) {
                    possibleMoves.push([newQ, newR]);
                }
                if (occupyingPiece) {
                    if (!occupyingPiece.is_dead && !areColorsEqual(occupyingPiece.color, piece.color)) {
                        possibleMoves.push([newQ, newR]);
                        break;
                    }
                }
            }
        }
        // Déplacement d'une case en diagonale
        for (const [dq, dr] of DIAG_DIRECTIONS) {
            const newQ = piece.q + dq;
            const newR = piece.r + dr;
            const occupyingPiece = getPieceAt(newQ, newR);

            if (isValidMove(newQ, newR, piece)) {
                possibleMoves.push([newQ, newR]);
            }
            if (occupyingPiece) {
                if (!occupyingPiece.is_dead && !areColorsEqual(occupyingPiece.color, piece.color)) {
                    possibleMoves.push([newQ, newR]);
                    break;
                }
            }
        }
    } else {
        console.log("Déplacement normal pour les autres pièces");
        // Déplacement normal pour les autres pièces
        for (const [dq, dr] of ALL_DIRECTIONS) {
            let step = 1;
            while (true) {
                const newQ = piece.q + dq * step;
                const newR = piece.r + dr * step;
                
                if (!isWithinBoard(newQ, newR)) {
                    break;
                }

                const occupyingPiece = getPieceAt(newQ, newR);
                if (occupyingPiece) {
                    if (piece.piece_class === 'assassin') {
                        if (!occupyingPiece.is_dead && areColorsEqual(occupyingPiece.color, piece.color)) {
                            // L'assassin peut traverser les pièces alliées
                            step++;
                            continue;
                        } else if (!occupyingPiece.is_dead) {
                            possibleMoves.push([newQ, newR]);
                            break;
                        }
                    } else if (piece.piece_class == 'necromobile') {
                        if (occupyingPiece.is_dead) {
                            possibleMoves.push([newQ, newR]);
                            break;
                        } else {
                            break;
                        }
                    } else if (piece.piece_class == 'diplomat') {
                        if (!occupyingPiece.is_dead) {
                            possibleMoves.push([newQ, newR]);
                            break;
                        } else {
                            break;
                        }
                    } else if (piece.piece_class === 'chief') {
                        if (!occupyingPiece.is_dead && !areColorsEqual(occupyingPiece.color, piece.color)) {
                            possibleMoves.push([newQ, newR]);
                            break;
                        }
                    }
                }

                if (newQ === 0 && newR === 0 && piece.piece_class !== 'chief') {
                    // Si la case centrale est occupée par un mort et que la pièce est un nécromobile
                    const centralPiece = gameState.pieces.find(p => p.q === 0 && p.r === 0);
                    if (centralPiece) {
                        if (piece.piece_class === 'necromobile' && centralPiece.is_dead) {
                            possibleMoves.push([0, 0]);
                        } else if (piece.piece_class == 'militant' || piece.piece_class == 'necromobile' || piece.piece_class == 'assassin' && !centralPiece.is_dead) {
                            possibleMoves.push([0, 0]);
                        }
                    }
                    step++; // Continuer sans ajouter la case centrale
                    continue;
                }
                if (!isValidMove(newQ, newR, piece)) {
                    break;
                }
                // Vérifier si la case est centrale et si la pièce n'est pas un chef
                possibleMoves.push([newQ, newR]);
                step++;
            }
        }
    }
    
    return possibleMoves;
}

function isValidMove(newQ, newR, piece) {
    if (!isWithinBoard(newQ, newR) || isOccupied(newQ, newR)) {
        return false;
    }
    if (newQ === 0 && newR === 0 && piece.piece_class !== 'chief') {
        return false;
    }
    return true;
}

function isOccupied(q, r) {
    return gameState.pieces.some(piece => piece.q === q && piece.r === r);
}


function drawSelectedPieceHalo() {
    if (selectedPiece) {
        const [x, y] = hexToPixel(selectedPiece.q, selectedPiece.r);
        ctx.strokeStyle = 'yellow';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, PIECE_RADIUS + 5, 0, 2 * Math.PI);
        ctx.stroke();
    }
}

// Fonction pour obtenir la couleur du joueur actuel
function getCurrentPlayerColor() {
    console.log("Fonction getCurrentPlayerColor appelée");
    console.log("État du jeu:", gameState);
    if (gameState && gameState.players && gameState.current_player_index !== undefined) {
        const playerIndex = gameState.current_player_index;
        const player = gameState.players[playerIndex];
        if (player && player.color) {
            console.log("Couleur du joueur actuel:", player.color);
            return player.color;
        }
    }
    console.log("Aucune couleur de joueur trouvée, utilisation de la couleur par défaut");
    return "white"; // Couleur par défaut
}

// Fonction pour envoyer un mouvement au serveur
function sendMove(piece, new_q, new_r, captured_q, captured_r) {
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
        },
        'captured_piece_to': {
            'q': captured_q,
            'r': captured_r
        }
    };
    console.log(action);
    ws.send(JSON.stringify(action));
}

// Fonction pour dessiner l'indicateur de tour du joueur
function drawPlayerTurn() {
    if (gameState && gameState.current_player_index !== undefined) {
        let playerColor = "white"; // Couleur par défaut
        let playerText = `Joueur ${gameState.current_player_index + 1}`;

        if (gameState.players && gameState.players[gameState.current_player_index]) {
            const player = gameState.players[gameState.current_player_index];
            if (player.color) {
                playerColor = Array.isArray(player.color) 
                    ? `rgb(${player.color[0]}, ${player.color[1]}, ${player.color[2]})`
                    : player.color;
            }
            if (player.name) {
                playerText = player.name;
            }
        }

        // Configurer le texte
        ctx.font = 'bold 24px Arial';
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 3;
        const text = `Tour du ${playerText}`;
        
        // Dessiner le texte avec un contour pour une meilleure visibilité
        ctx.strokeText(text, 20, 30);
        ctx.fillText(text, 20, 30);

        // Dessiner un cercle de la couleur du joueur
        ctx.beginPath();
        ctx.arc(250, 20, 15, 0, 2 * Math.PI);
        ctx.fillStyle = playerColor;
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
    } else {
        console.log("Données insuffisantes pour afficher le tour du joueur");
    }
}
// Fonction principale de dessin
function draw() {
    drawBoard();
    if (gameState && gameState.pieces) {
        drawPieces();
    }
    drawSelectedPieceHalo();
    drawPossibleMoves();
    drawAvailableCells(); // Ajoutez cette ligne
    drawPlayerTurn();
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

// Fonction auxiliaire pour obtenir une pièce à une position donnée
function getPieceAt(q, r) {
    return gameState.pieces.find(p => p.q === q && p.r === r && !p.is_dead);
}

// Appeler draw() immédiatement pour dessiner au moins le plateau
draw();

function areColorsEqual(color1, color2) {
    if (Array.isArray(color1) && Array.isArray(color2)) {
        return color1.every((val, index) => val === color2[index]);
    } else if (typeof color1 === 'string' && typeof color2 === 'string') {
        return color1 === color2;
    } else if (Array.isArray(color1) && typeof color2 === 'string') {
        return `rgb(${color1.join(',')})` === color2;
    } else if (typeof color1 === 'string' && Array.isArray(color2)) {
        return color1 === `rgb(${color2.join(',')})`;
    }
    return false;
}

// Fonction pour trouver toutes les cellules disponibles sur le plateau
function findAvailableCells() {
    const cellulesDisponibles = [];
    for (let q = -BOARD_SIZE + 1; q < BOARD_SIZE; q++) {
        for (let r = -BOARD_SIZE + 1; r < BOARD_SIZE; r++) {
            // Vérifier si la cellule est dans le plateau
            if (isWithinBoard(q, r)) {
                // Vérifier si la cellule n'est pas occupée par une pièce
                if (!getPieceAt(q, r)) {
                    // Vérifier si ce n'est pas la case centrale (sauf pour le chef)
                    if (q !== 0 || r !== 0) {
                        cellulesDisponibles.push([q, r]);
                    }
                }
            }
        }
    }
    return cellulesDisponibles;
}

