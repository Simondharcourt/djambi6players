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
    'rgb(128, 0, 128)': 'purple',
    'rgb(0, 0, 255)': 'blue',
    'rgb(255, 0, 0)': 'red',
    'rgb(255, 105, 180)': 'pink',
    'rgb(255, 255, 0)': 'yellow',
    'rgb(0, 255, 0)': 'green',
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
    img.src = `public/assets/${cl}.svg`;
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

let animationInProgress = false;
let animationPiece = null;
let startPos = null;
let endPos = null;
let animationProgress = 0;

// Ajouter le WebSocket
// const ws = new WebSocket('wss://djambi6players-105ba3b611ff.herokuapp.com');  // Remplacez par l'URL de votre serveur
// const ws = new WebSocket('ws://localhost:8765'); // to test on local
const ws = new WebSocket('wss://desolate-gorge-87361-ab45c9693901.herokuapp.com');  // Remplacez par l'URL de votre serveur


ws.onopen = function() {
    console.log('Connecté au serveur WebSocket');
    // Aucune requête supplémentaire n'est nécessaire ici, le serveur enverra la couleur automatiquement
};

ws.onerror = function(error) {
    console.error('Erreur WebSocket:', error);
    initializeDefaultState();
};

// Variable globale pour stocker la couleur assignée
let clientAssignedColor = "white"; // Couleur par défaut
let clientAssignedIndex = 0;

ws.onmessage = function(event) {
    console.log("Message reçu du serveur:", event.data);
    const data = JSON.parse(event.data);
    if (data.type === 'color_assignment') {
        // Assigner la couleur reçue à une variable ou un état
        clientAssignedColor = data.color; // Stocker la couleur assignée
        clientAssignedIndex = data.index;
        console.log("Couleur assignée:", clientAssignedColor);
        console.log("Index assigné:", clientAssignedIndex);
        draw();
    } else if (data.type === 'state') {
        if (data.last_move) {
            startAnimation(data.last_move.piece.q, data.last_move.piece.r, data.last_move.move_to.q, data.last_move.move_to.r);
        }
        console.log("last move", data.last_move)
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

function drawBoard() {
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
    drawPlayerTurnArrow();
    drawPlayerTurn()
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
            if (animationInProgress && animationPiece && 
                animationPiece.q === piece.q && 
                animationPiece.r === piece.r) {
                return;
            }
            const [x, y] = hexToPixel(piece.q, piece.r);
            // Déterminer la couleur à utiliser
            let pieceColor = COLORS[piece.color];
            if (piece.is_dead) {
                pieceColor = 'rgb(100, 100, 100)'; // Gris pour les pièces mortes
            } else if (!gameState.available_colors.includes(piece.color)) {
                console.log("piececolor", piece.color)
            } else {
                pieceColor = 'rgb(255, 255, 255)';
            }
            // Dessiner le cercle de la pièce
            ctx.fillStyle = pieceColor;
            ctx.beginPath();
            ctx.arc(x, y, PIECE_RADIUS, 0, 2 * Math.PI);
            ctx.fill();
            // Dessiner l'image de la pièce
            if (allImagesLoaded) {
                if (!piece.is_dead) {
                    const img = pieceImages[piece.piece_class];
                    ctx.drawImage(img, x - SIZE_IMAGE / 2, y - SIZE_IMAGE / 2, SIZE_IMAGE, SIZE_IMAGE);
                } else {
                    const img = pieceImages['necromobile'];
                }
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


// Fonction pour convertir les coordonnées hexagonales en pixels
function hexToPixel(q, r) {
    const x = HEX_RADIUS * 3 / 2 * q;
    const y = HEX_RADIUS * Math.sqrt(3) * (r + q / 2);

    // Appliquer la rotation de pi/3
    const angle = -Math.PI / 3 * (clientAssignedIndex+2);
    const rotatedX = x * Math.cos(angle) - y * Math.sin(angle);
    const rotatedY = x * Math.sin(angle) + y * Math.cos(angle);

    return [
        rotatedX + WINDOW_WIDTH / 2,
        rotatedY + WINDOW_HEIGHT / 2 - VERTICAL_OFFSET
    ];
}

// Fonction pour convertir les coordonnées pixel en coordonnées hexagonales
function pixelToHex(x, y) {
    x -= WINDOW_WIDTH / 2;
    y -= (WINDOW_HEIGHT / 2 - VERTICAL_OFFSET);
    const angle = Math.PI / 3 * (clientAssignedIndex + 2);
    const unrotatedX = x * Math.cos(angle) - y * Math.sin(angle);
    const unrotatedY = x * Math.sin(angle) + y * Math.cos(angle);
    const q = (2/3) * unrotatedX / HEX_RADIUS;
    const r = (-1/3) * unrotatedX / HEX_RADIUS + Math.sqrt(3)/3 * unrotatedY / HEX_RADIUS;

    return [Math.round(q), Math.round(r)];
}
// Gestion des événements de la souris
canvas.addEventListener('click', (event) => {
    hidePieceInfo(); // Ajouter cette ligne
    if (gameState) {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const [q, r] = pixelToHex(x, y);

        if (selectedPiece) {
            if ((selectedPiece.q === q && selectedPiece.r === r) && !targetedPiece) {
                selectedPiece = null;
                possibleMoves = [];
                availableCells = [];
            } else if (possibleMoves.some(move => move[0] === q && move[1] === r)) {
                const targetPiece = getPieceAt(q, r);
                if (targetPiece && selectedPiece.piece_class !== 'assassin') {
                    targetedPiece = getPieceAt(q, r);
                    availableCells = findAvailableCells();
                    availableCells.push([selectedPiece.q, selectedPiece.r]);
                } else {
                    console.log(selectedPiece, q, r, null, null);
                    sendMove(selectedPiece, q, r, null, null);
                    availableCells = [];
                    selectedPiece = null;
                }
                possibleMoves = [];
            } else if (availableCells.some(cell => cell[0] === q && cell[1] === r)) {
                console.log(selectedPiece, targetedPiece.q, targetedPiece.r, q, r);
                sendMove(selectedPiece, targetedPiece.q, targetedPiece.r, q, r);
                selectedPiece = null;
                possibleMoves = [];
                availableCells = [];
            } else {
                selectPiece(q, r);
                availableCells = [];
            }
        } else {
            selectPiece(q, r);
            availableCells = [];
        }
        draw();
    }
});

function selectPiece(q, r) {
    if (gameState) {
        const piece = gameState.pieces.find(p => p.q === q && p.r === r && !p.is_dead);
        if (piece) {
            const clientPlayerColor = getClientPlayerColor();
            updatePieceInfo(piece); // Ajouter cette ligne
            if (areColorsEqual(gameState.current_player_color, clientPlayerColor) && 
                areColorsEqual(piece.color, clientPlayerColor)) {
                selectedPiece = piece;
                possibleMoves = calculatePossibleMoves(piece);
                draw();
            }
        }
    }
}

function calculatePossibleMoves(piece) {
    if (piece.is_dead) {
        return [];
    }
    const possibleMoves = [];
    if (piece.piece_class === 'militant') {
        for (const [dq, dr] of ADJACENT_DIRECTIONS) {
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
                    break;
                }
            }
        }
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
function getClientPlayerColor() {
    return clientAssignedColor; // Retourner la couleur assignée
}

// Fonction pour envoyer un mouvement au serveur
function sendMove(piece, new_q, new_r, captured_q, captured_r) {
    const action = {
        'type': 'move',
        'fromPlayer': gameState.current_player_index,
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

function drawPlayerTurn() {
    if (gameState && gameState.current_player_index !== undefined) {
        let playerColor = Object.keys(COLORS)[gameState.current_player_index];
        console.log("playerColor", playerColor);
        console.log("players_colors_order", gameState.players_colors_order);
        console.log("current_player_color", gameState.current_player_color);

        ctx.font = '24px Arial';
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 2;
        const text = `Tour du joueur:`;
        ctx.fillText(text, 20, 30);
        // Dessiner un cercle de la couleur du joueur
        ctx.beginPath();
        ctx.arc(202, 22, 15, 0, 2 * Math.PI);
        ctx.fillStyle = gameState.current_player_color;
        ctx.fill();
        ctx.stroke();
        // Ajouter l'affichage de la couleur du client
        const clientColor = getClientPlayerColor();
        const clientColorText = `Votre couleur:`;
        ctx.fillStyle = 'white';
        ctx.fillText(clientColorText, 20, 60);

        // Dessiner un cercle de la couleur du client
        ctx.beginPath();
        ctx.arc(187, 55, 15, 0, 2 * Math.PI);
        ctx.fillStyle = clientColor;
        ctx.fill();
        ctx.lineWidth = 0;
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

function getPieceAt(q, r) {
    return gameState.pieces.find(p => p.q === q && p.r === r);
}
draw();

function areColorsEqual(color1, color2) {
    const normalizeColor = (color) => {
        if (Array.isArray(color)) {
            return `rgb(${color.join(', ')})`;
        }
        if (typeof color === 'string' && color.startsWith('rgb')) {
            // Extraire les valeurs numériques de la chaîne RGB
            const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
            if (match) {
                return `rgb(${match[1]}, ${match[2]}, ${match[3]})`;
            }
        }
        return color;
    };
    const normalizedColor1 = normalizeColor(color1);
    const normalizedColor2 = normalizeColor(color2);
    return normalizedColor1 === normalizedColor2;
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

// Fonction pour dessiner une flèche indiquant le tour du joueur
function drawPlayerTurnArrow() {
    if (gameState && gameState.current_player_index !== undefined) {
        const angle = (Math.PI / 3) * (gameState.current_player_index + 1.5 - clientAssignedIndex);
        const arrowLength = 400; // Longueur de la flèche
        const arrowLength2 = 450;
        const centerX = WINDOW_WIDTH / 2;
        const centerY = WINDOW_HEIGHT / 2 - VERTICAL_OFFSET;

        const arrowX = centerX + arrowLength * Math.cos(angle);
        const arrowY = centerY + arrowLength * Math.sin(angle);
        const arrowX2 = centerX + arrowLength2 * Math.cos(angle);
        const arrowY2 = centerY + arrowLength2 * Math.sin(angle);

        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(arrowX2, arrowY2);
        ctx.stroke();
    }
}



function startAnimation(fromQ, fromR, toQ, toR) {
    animationInProgress = true;
    animationProgress = 0;
    startPos = hexToPixel(fromQ, fromR);
    endPos = hexToPixel(toQ, toR);
    
    // Trouver la pièce à animer
    animationPiece = gameState.pieces.find(p => p.q === fromQ && p.r === fromR);
    animationPiece.q = toQ;
    animationPiece.r = toR; 
    console.log("animationPiece", animationPiece);
    // Démarrer la boucle d'animation
    requestAnimationFrame(animate);
}

function animate(timestamp) {
    if (!animationInProgress) return;

    // Incrémenter la progression (ajuster la vitesse en modifiant le 0.05)
    animationProgress += 0.05;

    // Dessiner le frame actuel
    draw();
    
    // Calculer la position actuelle
    const currentX = startPos[0] + (endPos[0] - startPos[0]) * animationProgress;
    const currentY = startPos[1] + (endPos[1] - startPos[1]) * animationProgress;
    
    // Dessiner la pièce en mouvement
    if (animationPiece) {
        // Dessiner le cercle de la pièce
        ctx.fillStyle = COLORS;
        ctx.beginPath();
        ctx.arc(currentX, currentY, PIECE_RADIUS, 0, 2 * Math.PI);
        ctx.fill();
        
        // Dessiner l'image de la pièce
        if (allImagesLoaded) {
            const img = pieceImages[animationPiece.piece_class];
            ctx.drawImage(img, currentX - SIZE_IMAGE/2, currentY - SIZE_IMAGE/2, SIZE_IMAGE, SIZE_IMAGE);
        }
    }

    // Continuer l'animation si pas terminée
    if (animationProgress < 1) {
        requestAnimationFrame(animate);
    } else {
        // Terminer l'animation
        animationInProgress = false;
        animationPiece = null;
        draw();
    }
}

// Ajouter ces constantes pour les descriptions des pièces
const PIECE_DESCRIPTIONS = {
    'assassin': "L'Assassin peut traverser les pièces alliées et capturer une pièce ennemie. Sa victime sera placée là où se troauvait l'assassin.",
    'chief': "Le Chef est la pièce maîtresse. Si elle est capturée, vous perdez la partie. Si elle arrive au centre, vous prenez le pouvoir et rejouez après chacun de vos adversaires.",
    'diplomat': "Le Diplomate peut déplacer des pièces vivantes sans les tuer.",
    'militant': "Le Militant peut se déplacer de 2 cases dans les directions adjacentes et 1 case dans les directions diagonales. Il peut placer ses victimes où bon lui semble.",
    'necromobile': "Le Nécromobile peut déplacer les pièces mortes. Vous pouvez ainsi vous protéger ou gêner un adversaire.",
    'reporter': "Le Reporter élimine toutes les pièces ennemies autour de lui après s'être déplacé."
};

// Ajouter ces nouvelles fonctions
function updatePieceInfo(piece) {
    const pieceInfo = document.getElementById('pieceInfo');
    const pieceImage = document.getElementById('pieceImage');
    const pieceClass = document.getElementById('pieceClass');
    const pieceColor = document.getElementById('pieceColor');
    const pieceDescription = document.getElementById('pieceDescription');

    pieceInfo.style.display = 'block';
    pieceImage.src = `public/assets/${piece.piece_class}.svg`;
    pieceClass.textContent = `Type: ${piece.piece_class}`;
    pieceColor.textContent = `Couleur: ${piece.color}`;
    pieceDescription.textContent = PIECE_DESCRIPTIONS[piece.piece_class];
}

function hidePieceInfo() {
    const pieceInfo = document.getElementById('pieceInfo');
    pieceInfo.style.display = 'none';
}
