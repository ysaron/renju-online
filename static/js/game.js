const timePanel = document.getElementById("time-panel")
const movesPanel = document.getElementById("moves-panel")
const boardWrapper = document.getElementById("board-wrapper")
const boardBlock = document.getElementById("board")
const xAxis = document.getElementById("x-axis")
const yAxis = document.getElementById("y-axis")
const gamePlayersSection = document.getElementById("game-players-section")
const gameIdBlock = document.getElementById("game-id-block")
const readyBlock = document.getElementById("ready-block")
const gameParticipateMode = document.getElementById("game-participate-mode")
const btnReady = document.getElementById("btn-ready")

let currentBoards = {};

function openGame(game, my_role) {
    console.log("game:", game);
    console.log("me:", my_role);
    hideAllScreens();
    screenGame.style.display = "flex";

    if (!currentBoards[game.id]) {
        currentBoards[game.id] = board;
    }
    buildBoard(game.board);

    renderGameInfo(game);
    showPlayersSection(game);
    renderPlayers(game);
    renderControls(game, my_role);
}

function playerJoined(game, playerName) {
    console.log(`${playerName} joined!`);
    renderPlayers(game);
}

function spectatorJoined(game) {
}

function playerLeft(game, playerName) {
    console.log(`${playerName} left...`);
}

function spectatorLeft(game) {
}

function buildBoard(board) {
    // board: 2D Array 15х15 or 30х30
    clearBoard();
    let cellsArr = [];
    for (let y = 1; y <= board.length; y++) {
        let cellsRow = [];
        for (let x = 1; x <= board[y-1].length; x++) {
            let cell = document.createElement("div");
            cell.classList.add("cell");
            cell.innerHTML = `${x}-${y}`;
            cell.dataset.x = x;
            cell.dataset.y = y;
            cellsRow.push(cell);
        }
        cellsArr.push(cellsRow);
    }
    cellsArr.reverse();

    boardBlock.style.gridTemplateColumns = `repeat(${board.length}, 1fr)`;
    boardBlock.style.gridTemplateRows = `repeat(${board.length}, 1fr)`;

    for (let row of cellsArr) {
        for (let cell of row) {
            boardBlock.appendChild(cell);
        }
    }

    // Axes
    xAxis.style.gridTemplateColumns = `repeat(${board[0].length}, 1fr)`;
    yAxis.style.gridTemplateRows = `repeat(${board.length}, 1fr)`;
    for (let y = board.length; y >= 1; y--) {
        let axisCell = document.createElement("div");
        axisCell.classList.add("axis-cell");
        axisCell.innerHTML = y;
        axisCell.dataset.y = y;
        yAxis.appendChild(axisCell);
    }
    for (let x = 1; x <= board.length; x++) {
        let axisCell = document.createElement("div");
        axisCell.classList.add("axis-cell");
        axisCell.innerHTML = x;
        axisCell.dataset.y = x;
        xAxis.appendChild(axisCell);
    }
}

function clearBoard() {
    boardBlock.innerHTML = "";
    xAxis.innerHTML = "";
    yAxis.innerHTML = "";
}

function renderGameInfo(game) {
    gameIdBlock.innerHTML = `Game ID: ${game.id}`;
}

function showPlayersSection(game) {
    gamePlayersSection.style.visibility = "visible";
    if (game.num_players == 3) {
        gamePlayersSection.querySelector("#player-gray").style.display = "flex";
    }
}

function renderPlayers(game) {
    if (game.player_1) addPlayerInBlock("white", game.player_1.player.name);
    if (game.player_2) addPlayerInBlock("black", game.player_2.player.name);
    if (game.player_3) addPlayerInBlock("gray", game.player_3.player.name);
}

function addPlayerInBlock(color, playerName) {
    // color: white | black | gray
    let playerBlock = gamePlayersSection.querySelector(`#player-${color}`);
    let playerBlockName = playerBlock.querySelector(".player-name");
    playerBlockName.innerHTML = playerName;
}

function renderControls(game, my_role) {
    if (my_role == "4") {
        gameParticipateMode.style.display = "block";
    } else {
        btnReady.style.display = "block";
    }
}
