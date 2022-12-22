const gameList = document.getElementById("game-list")
const gameListLoader = makeLoaderGrid("gamelist-loader")
const privateGameInput = document.getElementById("private-game-id")
const joinPrivateGameBtn = document.getElementById("join-private-game")
const spectatePrivateGameBtn = document.getElementById("spectate-private-game")

joinPrivateGameBtn.addEventListener("click", joinGameByID)
spectatePrivateGameBtn.addEventListener("click", spectateGameByID)

for (let btn of btnsJoinGame) {btn.addEventListener("click", openGameList)}

btnRefreshGameList.addEventListener("click", updateGameList)

function showScreenGameList() {
    hideAllScreens();
    screenGameList.style.display = "flex";
}

function openGameList() {
    showScreenGameList();
    updateGameList();
}

function clearGameList() {
    gameList.innerHTML = "";
}

function updateGameList() {
    let token = getToken();
    clearGameList();
    gameList.appendChild(gameListLoader);
    gameListLoader.style.display = "inline-block";
    fetch(`${origin}/games`, {
        method: "GET",
        mode: "cors",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
    })
        .then(response => {
            if (response.ok) {
                return response.json()
            }
            onFetchError(response.status);
            return Promise.reject(response);
        })
        .then(response => {
            gameListLoader.style.display = "none";
            fillGameList(response);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
        .finally(() => {
            gameListLoader.style.display = "none";
        })
}

function fillGameList(games) {
    for (let game of games) {addGameInList(game)}
}

function createGameBlock(game, gameItem) {
    gameItem.innerHTML = "";
    // --- Info ---------------------------------------------------
    let gameInfo = document.createElement("div");
    // Creator
    let creator = document.createElement("div");
    creator.innerHTML = "by";
    let creatorName = document.createElement("div");
    if (game.player_1) {
        creatorName.innerHTML = game.player_1.player.name;
    } else {
        creatorName.innerHTML = "unknown";
    }
    creatorName.classList.add("highlight", "green");
    creator.appendChild(creatorName);
    gameInfo.appendChild(creator);

    gameItem.appendChild(gameInfo);

    // --- Rules ---------------------------------------------------------------------------
    let rules = document.createElement("div");
    rules.innerHTML = "Rules";
    rules.classList.add("question");
    // Tooltip
    let three_players = game.num_players == 3;
    let tooltip = createRulesTooltip(
        game.time_limit, game.board_size, game.classic_mode, game.with_myself, three_players
    );
    tooltip.classList.add("tooltip", "tooltip-common");
    rules.appendChild(tooltip);

    gameItem.appendChild(rules);

    // --- State ---------------------------------------------------------------------------------
    let gameState = document.createElement("div");
    // Value
    let gameStateValue = document.createElement("div");
    let stateColor = getGameStateColor(game.state);
    gameStateValue.classList.add("highlight", stateColor);
    gameStateValue.innerHTML = game.state == "pending" ? "started" : game.state;
    gameState.appendChild(gameStateValue);
    // Datetime
    let dateBlock = document.createElement("div");
    dateBlock.innerHTML = "at ";
    let dateValue = document.createElement("span");
    let dateStateMapping = {
        created: game.created_at,
        pending: game.started_at,
        finished: game.finished_at
    }
    let dateJS = new Date(dateStateMapping[game.state]);
    dateValue.innerHTML = dateJS.toLocaleString("ru-RU", {dateStyle: "short", timeStyle: "short"});
    dateValue.classList.add("highlight", "datetime");
    dateBlock.appendChild(dateValue);
    gameState.appendChild(dateBlock);

    gameItem.appendChild(gameState);

    // --- Players' indicators ------------------------------------------------------------
    let playersBlock = document.createElement("div");
    // Header
    let playersBlockHeader = document.createElement("div");
    playersBlockHeader.innerHTML = "Players";
    playersBlock.appendChild(playersBlockHeader);
    // Indicators
    let indicatorBlock = document.createElement("div");
    indicatorBlock.classList.add("player-indicators");
    for (let i=0; i < game.num_players; ++i) {
        let indicator = document.createElement("div");
        indicator.classList.add("indicator", "indicator-empty");
        indicatorBlock.appendChild(indicator);
    }
    lightUpPlayerIndicators(game, indicatorBlock);

    playersBlock.appendChild(indicatorBlock);
    gameItem.appendChild(playersBlock);

    // --- Spectators info -------------------------------------------------------------------
    let spectatorsBlock = document.createElement("div");
    let svgEye = svgEyeTemp.content.firstElementChild.cloneNode(true);
    spectatorsBlock.appendChild(svgEye);
    spectatorsBlock.innerHTML += ` ${game.spectators.length}`;

    gameItem.appendChild(spectatorsBlock);

    // --- Control buttons ---------------------------------------------------------------------
    let joinBtn = joinBtnTemp.content.firstElementChild.cloneNode(true);
    let spectateBtn = spectateBtnTemp.content.firstElementChild.cloneNode(true);
    joinBtn.addEventListener("click", joinGameFromParent);
    spectateBtn.addEventListener("click", spectateGameFromParent);
    if (game.state != "created") blockButton(joinBtn);
    if (game.state == "finished") blockButton(spectateBtn);
    gameItem.appendChild(joinBtn);
    gameItem.appendChild(spectateBtn);
    return gameItem
}

function addGameInList(game) {
    let gameItem = document.createElement("div");
    gameItem.dataset.id = game.id;
    gameItem.classList.add("game-item");
    gameItem = createGameBlock(game, gameItem);
    gameList.insertBefore(gameItem, gameList.firstChild);
}

function lightUpPlayerIndicators(game, indicatorBlock) {
    for (indicator of indicatorBlock.children) {
        indicator.classList.add("indicator-empty");
    }
    if (game.player_1) {
        indicatorBlock.children[0].classList.remove("indicator-empty");
        let cls = game.player_1.result.result == 2 ? "indicator-red" : "indicator-green";
        indicatorBlock.children[0].classList.add(cls);
    }
    if (game.player_2) {
        indicatorBlock.children[1].classList.remove("indicator-empty");
        let cls = game.player_2.result.result == 2 ? "indicator-red" : "indicator-green";
        indicatorBlock.children[1].classList.add(cls);
    }
    if (game.player_3) {
        indicatorBlock.children[2].classList.remove("indicator-empty");
        let cls = game.player_3.result.result == 2 ? "indicator-red" : "indicator-green";
        indicatorBlock.children[2].classList.add(cls);
    }
}

function joinGameFromParent(event) {
    console.log("event", event);
    console.log("target", event.currentTarget);
    let game_id = event.currentTarget.parentNode.dataset.id;
    joinGame(game_id);
}

function joinGameByID() {
    game_id = privateGameInput.value;
    joinGame(game_id);
}

function joinGame(game_id) {
    console.log("game_id: ", game_id);
    send({action: "join_game", game_id: game_id});
}

function spectateGameFromParent() {
}

function spectateGameByID() {
}

function spectateGame(game_id) {
}

function getGameItem(game_id) {
    for (let gameItem of gameList.children) {
        if (gameItem.dataset.id == game_id) return gameItem;
    }
}

function playerJoinedList(game, playerName) {
    if (game.is_private) return;
    let gameItem = getGameItem(game.id);
    let indicatorBlock = gameItem.querySelector(".player-indicators");
    lightUpPlayerIndicators(game, indicatorBlock);
}

function updateGameInList(game) {
    let gameItem = getGameItem(game.id);
    gameItem = createGameBlock(game, gameItem);
}

function gameRemovedList(game_id) {
    let gameItem = getGameItem(game_id);
    gameItem.style.display = "none";
    delete currentBoards[game_id];
}
