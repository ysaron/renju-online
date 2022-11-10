const gameList = document.getElementById("game-list")
const gameListLoader = makeLoaderGrid("gamelist-loader")

for (let btn of btnsJoinGame) {btn.addEventListener("click", openGameList)}

btnRefreshGameList.addEventListener("click", updateGameList)

function showScreenGameList() {
    hideAllScreens();
    screenGameList.style.display = "flex";
}

function openGameList() {
    showScreenGameList();
    updateGameList();

    send({action: 'example', data: 'eome data !!1'});
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

function addGameInList(game) {
    let gameItem = document.createElement("div");
    gameItem.dataset.id = game.id;
    gameItem.classList.add("game-item");

    // --- Info ---------------------------------------------------
    let gameInfo = document.createElement("div");
    // Creator
    let creator = document.createElement("div");
    creator.innerHTML = "by ";
    let creatorName = document.createElement("span");
    creatorName.innerHTML = getPlayer(game, "1").player.name;
    creatorName.classList.add("highlight", "green");
    creator.appendChild(creatorName);
    gameInfo.appendChild(creator);
    // Datetime
    let createdAt = document.createElement("div");
    createdAt.innerHTML = "at ";
    let createdAtDate = document.createElement("span");
    let date = new Date(game.created_at);
    createdAtDate.innerHTML = date.toLocaleString("ru-RU", {dateStyle: "short", timeStyle: "short"});
    createdAtDate.classList.add("highlight", "datetime");
    createdAt.appendChild(createdAtDate);
    gameInfo.appendChild(createdAt);

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
    // Header
    let gameStateHeader = document.createElement("div");
    gameStateHeader.innerHTML = "State";
    gameState.appendChild(gameStateHeader);
    // Value
    let gameStateValue = document.createElement("div");
    let stateColor = getGameStateColor(game.state);
    gameStateValue.classList.add("highlight", stateColor);
    gameStateValue.innerHTML = game.state;
    gameState.appendChild(gameStateValue);

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
    for(let i=0; i < game.num_players; ++i) {
        let indicator = document.createElement("div");
        let indClass = getAllPlayers(game)[i] ? "indicator-green" : "indicator-empty";
        indicator.classList.add("indicator", indClass);
        indicatorBlock.appendChild(indicator);
    }
    playersBlock.appendChild(indicatorBlock);

    gameItem.appendChild(playersBlock);

    // --- Spectators info -------------------------------------------------------------------
    let spectatorsBlock = document.createElement("div");
    let svgEye = svgEyeTemp.content.firstElementChild.cloneNode(true);
    spectatorsBlock.appendChild(svgEye);
    spectatorsBlock.innerHTML += ` ${getAllSpectators(game).length}`;

    gameItem.appendChild(spectatorsBlock);

    // --- Control buttons ---------------------------------------------------------------------
    gameItem.appendChild(joinSpectateBtnsTemp.content.firstElementChild.cloneNode(true));

    gameList.appendChild(gameItem);

}

function getPlayer(game, role) {
    if (!playerRoles.includes(role)) throw "Unknown player role";
    for (let player of game.players) {
        if (player.role == role) return player;
    }
}

function getAllPlayers(game) {
    let allPlayers = [];
    for (let player of game.players) {
        if (playerRoles.includes(player.role)) allPlayers.push(player);
    }
    return allPlayers
}

function getAllSpectators(game) {
    let allSpectators = [];
    for (let player of game.players) {
        if (spectatorRoles.includes(player.role)) allSpectators.push(player);
    }
    return allSpectators
}
