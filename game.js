// Variables du jeu
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');


const INACTIVITY_TIMEOUT = 600000; // 10 minutes en millisecondes
let inactivityTimer = null;

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
    'grey': 'rgb(100, 100, 100)',
    'white': 'rgb(255, 255, 255)',
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

// Ajouter ces constantes pour les descriptions des pièces
const PIECE_DESCRIPTIONS = {
    'assassin': "L'Assassin peut traverser les pièces alliées et capturer une pièce ennemie. Sa victime sera placée là où se troauvait l'assassin.",
    'chief': "Le Chef est la pièce maîtresse. Si elle est capturée, vous perdez la partie. Si elle arrive au centre, vous prenez le pouvoir et rejouez après chacun de vos adversaires.",
    'diplomat': "Le Diplomate peut déplacer des pièces vivantes sans les tuer.",
    'militant': "Le Militant peut se déplacer de 2 cases dans les directions adjacentes et 1 case dans les directions diagonales. Il peut placer ses victimes où bon lui semble.",
    'necromobile': "Le Nécromobile peut déplacer les pièces mortes. Vous pouvez ainsi vous protéger ou gêner un adversaire.",
    'reporter': "Le Reporter élimine toutes les pièces ennemies autour de lui après s'être déplacé."
};

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
let informationBox = null;
let possibleMoves = [];
let availableCells = []; // Ajoutez cette variable globale

let animationInProgress = false;
let animationPiece = null;
let startPos = null;
let endPos = null;
let animationProgress = 0;

// Déterminer l'URL du WebSocket en fonction de l'environnement
let wsUrl;
if (window.location.hostname.includes('github.io')) {
    wsUrl = 'wss://desolate-gorge-87361-ab45c9693901.herokuapp.com';
} else {
    wsUrl = 'ws://localhost:8765';
}

const ws = new WebSocket(wsUrl);

// Ajouter une variable globale pour suivre l'état de connexion
let isLoggedIn = false;
let currentUsername = null;

// Modifier la fonction startGame
function startGame(playerCount) {
    if (!isLoggedIn) {
        alert('Vous devez être connecté pour jouer. Veuillez vous connecter ou créer un compte.');
        return;
    }

    document.getElementById('mainMenu').style.display = 'none';
    document.querySelector('.game-container').style.display = 'flex';
    
    resetInactivityTimer();

    ws.send(JSON.stringify({
        type: 'start_game',
        nb_players: playerCount,
        username: currentUsername
    }));
}

function startAIGame(mode) {
    // Implémenter l'affichage des paramètres
    alert('Partie contre IA à venir');
}


function showSubmenu(menuId) {
    // Cache le menu principal
    document.getElementById('mainMenuContainer').style.display = 'none';
    // Affiche le sous-menu sélectionné
    document.getElementById(menuId).style.display = 'flex';
}

function showMainMenu() {
    // Cache tous les sous-menus
    const submenus = document.querySelectorAll('.submenu');
    submenus.forEach(menu => menu.style.display = 'none');
    // Affiche le menu principal
    document.getElementById('mainMenuContainer').style.display = 'flex';
}

function showSettings() {
    // Implémenter l'affichage des paramètres
    alert('Page des paramètres à venir');
}

function showRules() {
    window.open('rules/Djambi_rules.pdf', '_blank');
}


function resetInactivityTimer() {
    // Annuler le timer existant s'il y en a un
    if (inactivityTimer) {
        clearTimeout(inactivityTimer);
    }
    
    // Démarrer un nouveau timer
    inactivityTimer = setTimeout(() => {
        if (isLoggedIn && gameState) {
            alert('Vous avez été déconnecté pour inactivité');
            backToMenu();
        }
    }, INACTIVITY_TIMEOUT);
}


function stopInactivityTimer() {
    if (inactivityTimer) {
        clearTimeout(inactivityTimer);
        inactivityTimer = null;
    }
}

function backToMenu() {
    document.getElementById('mainMenu').style.display = 'block';
    document.querySelector('.game-container').style.display = 'none';
    stopInactivityTimer();
    ws.send(JSON.stringify({
        type: 'quit_game'
    }));
}


function undoMove() {
    if (!gameState || !isLoggedIn || !clientAssignedIndices.includes(gameState.current_player_index - 1)) return;

    ws.send(JSON.stringify({
        type: 'undo'
    }));
    
    resetSelection();
    draw();
}

function redoMove() {
    if (!gameState || !isLoggedIn || !clientAssignedIndices.includes(gameState.current_player_index)) return;
    
    ws.send(JSON.stringify({
        type: 'redo'
    }));

    resetSelection();
    draw();
}

function updateUndoRedoButtons() {
    const undoButton = document.getElementById('undoButton');
    const redoButton = document.getElementById('redoButton');

    // Vérifier si on peut annuler
    if (clientAssignedIndices.includes(gameState.current_player_index - 1)) {
        enableButton(undoButton);
    } else {
        disableButton(undoButton);
    }

    // Vérifier si on peut refaire
    if (clientAssignedIndices.includes(gameState.current_player_index)) {
        enableButton(redoButton);
    } else {
        disableButton(redoButton);
    }
}

function disableButton(button) {
    button.disabled = true;
    button.style.backgroundColor = '#666'; // Gris plus foncé
    button.style.cursor = 'not-allowed';
}

function enableButton(button) {
    button.disabled = false;
    button.style.backgroundColor = '#333'; // Couleur normale
    button.style.cursor = 'pointer';
}


document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('backToMenu').addEventListener('click', backToMenu);
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('undoButton').addEventListener('click', undoMove);
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('redoButton').addEventListener('click', redoMove);
});

ws.onopen = function() {
    console.log('Connecté au serveur WebSocket');
};

ws.onerror = function(error) {
    console.error('Erreur WebSocket:', error);
    initializeDefaultState();
};

// Variable globale pour stocker la couleur assignée
let clientAssignedColor = "white"; // Couleur par défaut
let clientAssignedIndex = 0;
let clientAssignedColors = ["white"]; // Couleur par défaut


ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'loginResponse') {
        if (data.error === 'userAlreadyConnected') {
            alert('Cet utilisateur est déjà connecté sur une autre session');
            return;
        }
    }
    if (data.type === 'color_assignment') {
        console.log("data", data)
        if (data.nb_players === 6) {
            clientAssignedColors = [data.color]
            clientAssignedColor = data.color; // Stocker la couleur assignée
            clientAssignedIndex = data.index;
            console.log("clientAssignedColors", clientAssignedColors)
            clientAssignedIndices = [data.index]
        } else if (data.nb_players === 2 || data.nb_players === 3) {
            console.log("data", data)
            console.log("colors", data.colors)
            clientAssignedIndices = data.indices
            clientAssignedColors = data.colors; // Stocker la couleur assignée
            clientAssignedIndex = data.indices[1];
        }
        console.log("Couleur assignée:", clientAssignedColors);
        console.log("Index assigné:", clientAssignedIndex);
        draw();
    } else if (data.type === 'state') {
        if (data.last_move) {
            startAnimation(data.last_move.piece.q, data.last_move.piece.r, data.last_move.move_to.q, data.last_move.move_to.r);
        }
        console.log("last move", data.last_move)
        console.log("current_player_color", data.current_player_color)
        gameState = data;
        console.log("Nouvel état du jeu:", gameState);
        draw();
    } else if (data.type === 'error') {
        alert(data.message);
    } else if (data.type === 'auth_response') {
        if (data.success) {
            isLoggedIn = true;
            currentUsername = data.username;
            alert(data.message);
            updateUIAfterAuth(data.username);
        } else {
            isLoggedIn = false;
            currentUsername = null;
            alert(data.message);
        }
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
            let pieceColor = piece.color;
            if (piece.is_dead) {
                pieceColor = 'grey'; // Gris pour les pièces mortes
            } else if (!gameState.available_colors.includes(piece.color)) {
                pieceColor = piece.color;
            } else {
                pieceColor = 'white';
            }
            // Dessiner le cercle de la pièce
            ctx.fillStyle = COLORS[pieceColor];
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



canvas.addEventListener('click', handleCanvasClick);


canvas.addEventListener('mousemove', () => {
    if (gameState && isLoggedIn) {
        resetInactivityTimer();
    }
});

function handleCanvasClick(event) {
    if (!gameState) return;
    resetInactivityTimer();

    const [q, r] = getClickedHexCoordinates(event);

    if (selectedPiece) {
        handleSelectedPieceClick(q, r);
    } else {
        selectPiece(q, r);
        availableCells = [];
    }
    
    draw();
}

function getClickedHexCoordinates(event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    return pixelToHex(x, y);
}

function handleSelectedPieceClick(q, r) {
    console.log("targetedPiece", targetedPiece)

    if (targetedPiece && isAvailableCell(q, r)) {
        handleCapturedPiecePlacement(q, r);
        resetSelection();
        return;
    } else if (!targetedPiece && isClickOnSelectedPiece(q, r)) {
        resetSelection();
        return;
    } else if (!targetedPiece && isPossibleMove(q, r)) {
        handleMoveAttempt(q, r);
        return;
    }
    selectPiece(q, r);
    availableCells = [];
}

function isClickOnSelectedPiece(q, r) {
    return selectedPiece.q === q && 
           selectedPiece.r === r && 
           !targetedPiece;
}

function isPossibleMove(q, r) {
    return possibleMoves.some(move => move[0] === q && move[1] === r);
}

function isAvailableCell(q, r) {
    return availableCells.some(cell => cell[0] === q && cell[1] === r);
}

function resetSelection() {
    selectedPiece = null;
    targetedPiece = null;
    possibleMoves = [];
    availableCells = [];
}

function handleMoveAttempt(q, r) {
    const targetPiece = getPieceAt(q, r);

    if (targetPiece && selectedPiece.piece_class !== 'assassin') {
        // Cas spcial: capture d'une pièce (sauf pour l'assassin)
        targetedPiece = targetPiece;
        availableCells = findAvailableCells();
        availableCells.push([selectedPiece.q, selectedPiece.r]);
    } else {
        // Déplacement normal
        sendMove(selectedPiece, q, r, null, null);
        resetSelection();
    }
    possibleMoves = [];
}

function handleCapturedPiecePlacement(q, r) {
    sendMove(selectedPiece, targetedPiece.q, targetedPiece.r, q, r);
    resetSelection();
}

function selectPiece(q, r) {
    if (gameState) {
        const piece = gameState.pieces.find(p => p.q === q && p.r === r && !p.is_dead);
        if (piece) {
            updatePieceInfo(piece); // Ajouter cette ligne
            console.log("gameState.current_player_color", gameState.current_player_color)
            console.log("piece.color", piece.color)
            console.log("clientAssignedColors", clientAssignedColors)
            if (areColorsEqual(gameState.current_player_color, piece.color) && 
                clientAssignedColors.includes(piece.color)) {
                selectedPiece = piece;
                possibleMoves = calculatePossibleMoves(piece);
                draw();
            }
        } else {
            hidePieceInfo();
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
        const clientColorText = `Votre couleur:`;
        ctx.fillStyle = 'white';
        ctx.fillText(clientColorText, 20, 60);

        // Dessiner un cercle de la couleur du client
        clientAssignedColors.forEach((color, index) => {
            ctx.beginPath();
            ctx.arc(187 + index * 40, 55, 15, 0, 2 * Math.PI);
            ctx.fillStyle = COLORS[color];
            ctx.fill();
            ctx.lineWidth = 0;
            ctx.stroke();
        });
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
    drawPlayerScores();
    updateUndoRedoButtons(); // Ajouter cette ligne


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
        const arrowLength2 = 430;
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

        const arrowLength3 = 15;


        const angle3 = angle + (Math.PI / 6);
        const arrowX3 = arrowX + arrowLength3 * Math.cos(angle3);
        const arrowY3 = arrowY + arrowLength3 * Math.sin(angle3);

        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(arrowX3, arrowY3);
        ctx.stroke();

        const angle4 = angle - (Math.PI / 6);
        const arrowX4 = arrowX + arrowLength3 * Math.cos(angle4);
        const arrowY4 = arrowY + arrowLength3 * Math.sin(angle4);

        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(arrowX4, arrowY4);
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
    animationProgress += 0.05;
    draw();
    
    // Calculer la position actuelle
    const currentX = startPos[0] + (endPos[0] - startPos[0]) * animationProgress;
    const currentY = startPos[1] + (endPos[1] - startPos[1]) * animationProgress;
    
    // Dessiner la pièce en mouvement
    if (animationPiece) {
        // Dessiner le cercle de la pièce
        ctx.fillStyle = COLORS[animationPiece.color];
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

// Ajouter ces nouvelles fonctions
function updatePieceInfo(piece) {
    console.log("piece", piece)
    console.log("informationBox", informationBox)
    if (informationBox === piece) {
        hidePieceInfo();
        return;
    }
    const pieceInfo = document.getElementById('pieceInfo');
    const pieceImage = document.getElementById('pieceImage');
    const pieceClass = document.getElementById('pieceClass');
    const pieceColor = document.getElementById('pieceColor');
    const pieceDescription = document.getElementById('pieceDescription');
    informationBox = piece;
    pieceInfo.style.display = 'block';
    pieceImage.src = `assets/${piece.piece_class}.svg`;
    pieceClass.textContent = `Type: ${piece.piece_class}`;
    pieceColor.textContent = `Couleur: ${piece.color}`;
    pieceDescription.textContent = PIECE_DESCRIPTIONS[piece.piece_class];
}

function hidePieceInfo() {
    const pieceInfo = document.getElementById('pieceInfo');
    pieceInfo.style.display = 'none';
    informationBox = null;
}
function drawPlayerScores() {
    if (!gameState || !gameState.players) return;

    const startX = 20;
    const startY = 300;
    const jetonRadius = 15;
    const spacing = 10;
    const scoreSpacing = 10;
    const nameSpacing = 60; // Espacement pour le nom

    ctx.font = '20px Arial';
    
    gameState.players.forEach((player, index) => {
        // Position du jeton
        const y = startY + index * (jetonRadius * 2 + spacing);
        
        // Dessiner le jeton
        ctx.beginPath();
        ctx.arc(startX, y, jetonRadius, 0, 2 * Math.PI);
        ctx.fillStyle = COLORS[player.color];
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Dessiner le score
        ctx.fillStyle = 'white';
        ctx.textAlign = 'left';
        ctx.fillText(player.relative_score.toString(), startX + jetonRadius + scoreSpacing, y + jetonRadius/2);

        // Dessiner le nom du joueur
        const playerName = (player.name || "").slice(0, 3);
        ctx.fillText(playerName, startX + jetonRadius + nameSpacing, y + jetonRadius/2);
    });
}

function createAccount() {
    const username = prompt('Entrez votre nom d\'utilisateur :');
    if (!username) return;

    const password = prompt('Entrez votre mot de passe :');
    
    if (!username || !password) {
        alert('Le nom d\'utilisateur et le mot de passe sont requis');
        return;
    }

    // Envoyer les informations au serveur
    ws.send(JSON.stringify({
        type: 'create_account',
        username: username,
        password: password
    }));
}

function login() {
    const username = prompt('Entrez votre nom d\'utilisateur :');
    if (!username) return;

    const password = prompt('Entrez votre mot de passe :');
    
    if (!username || !password) {
        alert('Le nom d\'utilisateur et le mot de passe sont requis');
        return;
    }


    // Envoyer les informations au serveur
    ws.send(JSON.stringify({
        type: 'login',
        username: username,
        password: password
    }));
}

function updateUIAfterAuth(username) {
    isLoggedIn = true;
    currentUsername = username;
    
    // Cacher le bouton Compte
    const accountButton = document.getElementById('accountButton');
    if (accountButton) {
        accountButton.style.display = 'none';
    }
    
    const loginButton = document.querySelector('button[onclick="login()"]');
    const createAccountButton = document.querySelector('button[onclick="createAccount()"]');
    
    if (loginButton && createAccountButton) {
        loginButton.style.display = 'none';
        createAccountButton.style.display = 'none';
        
        const menuContainer = document.querySelector('.menu-container');
        const logoutButton = document.createElement('button');
        logoutButton.className = 'menu-button';
        logoutButton.textContent = `Déconnexion (${username})`;
        logoutButton.onclick = logout;
        menuContainer.appendChild(logoutButton);
    }

    // Retourner au menu principal
    showMainMenu();
}

function logout() {
    isLoggedIn = false;
    currentUsername = null;
    
    ws.send(JSON.stringify({
        type: 'logout'
    }));
    
    location.reload();
}

