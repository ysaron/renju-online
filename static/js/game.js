const timePanel = document.getElementById("time-panel")
const movesPanel = document.getElementById("moves-panel")
const boardWrapper = document.getElementById("board-wrapper")
const boardBlock = document.getElementById("board")
const gamePlayersSection = document.getElementById("game-players-section")
const gameIdBlock = document.getElementById("game-id-block")
const readyBlock = document.getElementById("ready-block")
const gameParticipateMode = document.getElementById("game-participate-mode")
const btnReady = document.getElementById("btn-ready")

function openGame(game, my_role) {
    console.log("game:", game);
    console.log("me:", my_role);
    hideAllScreens();
    screenGame.style.display = "flex";

    buildBoard(game.board_size);        // TODO: рендер борды из game.board

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

function buildBoard(numRowItems) {
    boardBlock.style.gridTemplateColumns = `repeat(${numRowItems}, 1fr)`;
    boardBlock.style.gridTemplateRows = `repeat(${numRowItems}, 1fr)`;
    let numCells = numRowItems * numRowItems;
    for (let i = numCells; i >= 1; i--) {
        let cell = document.createElement("div");
        cell.classList.add("cell");
        let x = Math.floor(i % numRowItems);
        if (x == 0) x = numRowItems;
        let y = Math.ceil(i / numRowItems);
//        cell.innerHTML = `[${x} ${y}]`;
//        cell.innerHTML = i;

        // Записывать х & у в data-x & data-y соотв.
        // Добавить еще 2 сетки для координат. Х: только Columns; Y: только Rows устанавливать.
        // Им - тоже соотв. data-x OR data-y.

        boardBlock.appendChild(cell);
    }
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
