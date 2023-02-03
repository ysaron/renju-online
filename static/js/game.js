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
const btnLeave = document.getElementById("btn-leave")

let currentBoards = {};

function updateCurrentGames(game) {
    currentBoards[game.id].gameObj = game;
}

function openGame(game, my_role) {
    console.log("game:", game);
    console.log("me:", my_role);
    hideAllScreens();
    screenGame.style.display = "flex";

    if (!currentBoards[game.id]) {
        currentBoards[game.id] = {
            gameObj: game,
            allow_moves: false,
            role: my_role
        };
    }
    buildBoard(game);

    renderGameInfo(game);
    showPlayersSection(game);
    renderPlayers(game);
    renderControls(game, my_role);
    console.log("OpenGame ", currentBoards);
}

function playerJoined(game, playerName) {
    console.log(`${playerName} joined!`);
    renderPlayers(game);
    updateCurrentGames(game);
}

function playerReady(game, playerName, playerRole) {
    console.log(`${playerName} ready!`);
    btnLeave.innerHTML = "Concede";
    renderPlayers(game);
    updateCurrentGames(game);
}

function spectatorJoined(game) {
    updateCurrentGames(game);
}

function playerLeft(game, playerName) {
    console.log(`${playerName} left...`);
    updateCurrentGames(game);
}

function spectatorLeft(game) {
    updateCurrentGames(game);
}

function buildBoard(game) {
    console.log(currentBoards);
    // game.board: 2D Array 15х15 or 30х30
    clearBoard();
    let cellsArr = [];
    for (let y = 1; y <= game.board.length; y++) {
        let cellsRow = [];
        for (let x = 1; x <= game.board[y-1].length; x++) {
            let cell = document.createElement("div");
            cell.classList.add("cell");
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.addEventListener("mouseover", highlightCell);
            cell.addEventListener("mouseleave", cancelHighlightCell);
            cell.addEventListener("click", cellClicked);
            cellsRow.push(cell);
        }
        cellsArr.push(cellsRow);
    }
    cellsArr.reverse();

    boardBlock.dataset.gameid = game.id;
    boardBlock.style.gridTemplateColumns = `repeat(${game.board.length}, minmax(0, 1fr))`;
    boardBlock.style.gridTemplateRows = `repeat(${game.board.length}, minmax(0, 1fr))`;

    for (let row of cellsArr) {
        for (let cell of row) {
            boardBlock.appendChild(cell);
        }
    }

    // Axes
    xAxis.style.gridTemplateColumns = `repeat(${game.board[0].length}, minmax(0, 1fr))`;
    yAxis.style.gridTemplateRows = `repeat(${game.board.length}, minmax(0, 1fr))`;
    for (let y = game.board.length; y >= 1; y--) {
        let axisCell = document.createElement("div");
        axisCell.classList.add("axis-cell");
        axisCell.innerHTML = y;
        axisCell.dataset.y = y;
        yAxis.appendChild(axisCell);
    }
    for (let x = 1; x <= game.board.length; x++) {
        let axisCell = document.createElement("div");
        axisCell.classList.add("axis-cell");
        axisCell.innerHTML = x;
        axisCell.dataset.x = x;
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
    clearPlayersSection();
    if (game.player_1) {
        addPlayerInBlock("white", game.player_1.player.name);
        if (game.player_1.ready) setPlayerReady("white");
        if (game.player_1.can_move) setPlayerCanMove("white");
    }
    if (game.player_2) {
        addPlayerInBlock("black", game.player_2.player.name);
        if (game.player_2.ready) setPlayerReady("black");
        if (game.player_2.can_move) setPlayerCanMove("black");
    }
    if (game.player_3) {
        addPlayerInBlock("gray", game.player_3.player.name);
        if (game.player_3.ready) setPlayerReady("gray");
        if (game.player_3.can_move) setPlayerCanMove("gray");
    }
}

function clearPlayersSection() {
    for (let block of gamePlayersSection.children) {
        block.className = "";
        block.classList.add("player", "player-none");
        let playerBlockName = block.querySelector(".player-name");
        playerBlockName.innerHTML = "Unknown";
        let playerBlockReady = block.querySelector(".player-ready");
        playerBlockReady.innerHTML = "";
    }
}

function addPlayerInBlock(color, playerName) {
    // color: white | black | gray
    let playerBlock = gamePlayersSection.querySelector(`#player-${color}`);
    let playerBlockName = playerBlock.querySelector(".player-name");
    playerBlockName.innerHTML = playerName;
}

function setPlayerReady(color) {
    // color: white | black | gray
    let playerBlock = gamePlayersSection.querySelector(`#player-${color}`);
    let playerBlockReady = playerBlock.querySelector(".player-ready");
    playerBlockReady.innerHTML = "&#10004;";
    playerBlock.classList.remove("player-none");
    playerBlock.classList.add("player-confirmed");
}

function setPlayerCanMove(color) {
    // color: white | black | gray
    let playerBlock = gamePlayersSection.querySelector(`#player-${color}`);
    playerBlock.classList.remove("player-none", "player-confirmed");
    playerBlock.classList.add("player-active");
}

function setPlayerLose(color) {
    // color: white | black | gray
    let playerBlock = gamePlayersSection.querySelector(`#player-${color}`);
    let playerBlockReady = playerBlock.querySelector(".player-ready");
    playerBlockReady.innerHTML = "&#10008;";
    playerBlock.classList.remove("player-confirmed");
    playerBlock.classList.add("player-lost");
}

function renderControls(game, my_role) {
    btnLeave.innerHTML = "Leave";
    btnLeave.addEventListener("click", leaveGame);
    btnLeave.dataset.gameid = game.id;
    unblockButton(btnReady);
    if (my_role == "4") {
        gameParticipateMode.style.display = "block";
    } else {
        btnReady.style.display = "block";
        btnReady.dataset.gameid = game.id;
        btnReady.addEventListener("click", sendReadyAction);
    }
}

function sendReadyAction(event) {
    send({action: "ready", game_id: event.target.dataset.gameid});
    blockButton(event.target);
}

function showActiveGameMarker(role) {
    activeGameMarker.innerHTML = "ACTIVE GAME";
    if (role == "4") {
        let svgEye = svgEyeTemp.content.firstElementChild.cloneNode(true);
        activeGameMarker.innerHTML += " ";
        activeGameMarker.appendChild(svgEye);
    }
    activeGameMarker.style.display = "block";
}

function hideActiveGameMarker() {
    activeGameMarker.innerHTML = "";
    activeGameMarker.style.display = "none";
}

function gameStarted(game) {
    showActiveGameMarker(currentBoards[game.id].role);
    renderPlayers(game);
    console.log("Game started");
    console.log(game);
    updateCurrentGames(game);
}

function unblockBoard(game_id) {
    currentBoards[game_id].allow_moves = true;
    console.log("YOUR TURN!");
}

function blockBoard(game_id) {
    currentBoards[game_id].allow_moves = false;
}

function gameRemoved(game_id) {
    alert("This game has been removed.");
    showMainScreen();
    console.log("FORGET GAME gameRemoved");
    forgetGame(game_id);
}

function updateGame(game) {
    console.log("The game has been updated. Re-render players...");
    renderPlayers(game);
    updateCurrentGames(game);
}

function leaveGame(event) {
    send({action: "leave", game_id: event.target.dataset.gameid});
}

function leftGame(game) {
    console.log("FORGET GAME leftGame");
    forgetGame(game.id);
    showMainScreen();
}

function gameFinished(game) {
    hideActiveGameMarker();
    renderPlayers(game);
    alert(`The game has been finished. Result: ${game.result}`);
    console.log("FORGET GAME gameFinished");
    forgetGame(game.id);
    showMainScreen();
}

function getXAxisCell(cell) {
    let x;
    if (cell.classList.contains("cell")) {
        x = cell.dataset.x;
    } else {
        x = cell.parentNode.dataset.x;
    }
    for (let aCell of xAxis.children) {
        if (aCell.dataset.x == x) return aCell
    }
}

function getYAxisCell(cell) {
    let y;
    if (cell.classList.contains("cell")) {
        y = cell.dataset.y;
    } else {
        y = cell.parentNode.dataset.y;
    }
    for (let aCell of yAxis.children) {
        if (aCell.dataset.y == y) return aCell
    }
}

function getCell(x, y) {
    for (let cell of boardBlock.children) {
        if (cell.dataset.x == x && cell.dataset.y == y) return cell
    }
}

function highlightCell(event) {
    if (event.target.classList.contains("cell")) {
        event.target.classList.add("cell-highlight");
    }
    let xAxisCell = getXAxisCell(event.target);
    let yAxisCell = getYAxisCell(event.target);
    xAxisCell.classList.add("axis-cell-highlight");
    yAxisCell.classList.add("axis-cell-highlight");
}

function cancelHighlightCell(event) {
    event.target.classList.remove("cell-highlight");
    let xAxisCell = getXAxisCell(event.target);
    let yAxisCell = getYAxisCell(event.target);
    xAxisCell.classList.remove("axis-cell-highlight");
    yAxisCell.classList.remove("axis-cell-highlight");
}

function cellClicked(event) {
    let game_id = boardBlock.dataset.gameid;
    let gameData = currentBoards[game_id];
    if (!gameData.allow_moves) return;
    blockBoard(game_id);
    let x = event.target.dataset.x;
    let y = event.target.dataset.y;
    console.log(`Click! x${x}-y${y}`);
    send({action: "move", game_id: game_id, x: x, y: y});
}

function renderMove(game, move) {
    console.log("renderMove ", currentBoards);
    updateCurrentGames(game);
    let cell = getCell(move.x, move.y);
    let chip = document.createElement("div");
    let color;
    console.log("move.role ", move.role);
    switch (move.role) {
        case "1":
            color = "white";
            break;
        case "2":
            color = "black";
            break;
        case "3":
            color = "gray";
            break;
        default:
            break;
    }
    chip.classList.add("chip", `chip-${color}`);
    cell.appendChild(chip);
    cell.removeEventListener("click", cellClicked);

    renderPlayers(game);

    let moveRecord = document.createElement("div");
    moveRecord.innerHTML = `x${move.x}-y${move.y}`;
    moveRecord.classList.add("move-record", `move-record-${color}`);
    movesPanel.appendChild(moveRecord);
}
