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
    creatorName.innerHTML = game.player_1.player.name;
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
    for (let i=0; i < game.num_players; ++i) {
        let indicator = document.createElement("div");
        indicator.classList.add("indicator", "indicator-empty");
        indicatorBlock.appendChild(indicator);
    }
    if (game.player_1) {
        indicatorBlock.children[0].classList.remove("indicator-empty");
        indicatorBlock.children[0].classList.add("indicator-green");
    }
    if (game.player_2) {
        indicatorBlock.children[1].classList.remove("indicator-empty");
        indicatorBlock.children[1].classList.add("indicator-green");
    }
    if (game.player_3) {
        indicatorBlock.children[2].classList.remove("indicator-empty");
        indicatorBlock.children[2].classList.add("indicator-green");
    }

    playersBlock.appendChild(indicatorBlock);
    gameItem.appendChild(playersBlock);

    // --- Spectators info -------------------------------------------------------------------
    let spectatorsBlock = document.createElement("div");
    let svgEye = svgEyeTemp.content.firstElementChild.cloneNode(true);
    spectatorsBlock.appendChild(svgEye);
    spectatorsBlock.innerHTML += ` ${game.spectators.length}`;

    gameItem.appendChild(spectatorsBlock);

    // --- Control buttons ---------------------------------------------------------------------
    gameItem.appendChild(joinSpectateBtnsTemp.content.firstElementChild.cloneNode(true));

    gameList.appendChild(gameItem);

}
