const modeList = document.getElementById("mode-list")
const ruleList = document.getElementById("rule-list")

for (let btn of btnsCreateGame) {btn.addEventListener("click", startGameCreation)}

formCreateGame.addEventListener("submit", sendFormCreateGame)

function showScreenGameCreation() {
    hideAllScreens();
    screenGameCreation.style.display = "flex";
}

function startGameCreation() {
    showLoader();
    showScreenGameCreation();
    let token = getToken();
    fetch(`${origin}/modes`, {
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
            // response = {modes: array, rules: obj}
            addGameModeList(response.modes);
            updateCurrentRules(response.rules);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
        .finally(() => {
            hideLoader();
        })
}

function addGameModeList(modes) {
    modeList.innerHTML = "";
    header = document.createElement("h2");
    header.innerHTML = "Modes";
    modeList.appendChild(header);
    for (mode of modes) {
        const modeBlock = document.createElement("div");
        modeBlock.dataset.id = mode.id;
        modeBlock.classList.add("mode-block");
        modeBlock.addEventListener("click", addMode);

        const modeName = document.createElement("div");
        modeName.classList.add("mode-name");
        modeName.innerHTML = mode.name;

        const modeCheckbox = document.createElement("div");
        modeCheckbox.classList.add("mode-checkbox");
        if (!mode.is_active) {
            modeBlock.classList.add("mode-inactive");
            modeCheckbox.innerHTML = "&#10008;";
        }
        if (mode.dev) {
            modeBlock.classList.add("mode-dev");
            modeCheckbox.innerHTML = "&#10008;";
        }

        let modeTooltip = createRulesTooltip(
            mode.time_limit, mode.board_size, mode.classic_mode, mode.with_myself, mode.three_players, mode.dev
        );
        modeTooltip.classList.add("tooltip");

        modeBlock.appendChild(modeName);
        modeBlock.appendChild(modeCheckbox);
        modeBlock.appendChild(modeTooltip);
        modeList.appendChild(modeBlock);
    }
}

function updateCurrentRules(rules) {
    // изменяем список правил
    ruleList.innerHTML = "";
    const timeLimit = document.createElement("li");
    if (rules.time_limit == 0 || rules.time_limit == null) {
        timeLimit.innerHTML = "Time limit: &#8734;";
    } else {
        timeLimit.innerHTML = `Time limit: ${rules.time_limit} s`;
    }
    ruleList.appendChild(timeLimit);

    const boardSize = document.createElement("li");
    boardSize.innerHTML = `Board: ${rules.board_size}x${rules.board_size}`;
    ruleList.appendChild(boardSize);

    const players = document.createElement("li");
    let num_players = rules.three_players ? 3 : 2;
    players.innerHTML = `Players: ${num_players}`
    ruleList.appendChild(players);

    if (rules.classic_mode) {
        const classicMode = document.createElement("li");
        classicMode.innerHTML = "Classic Mode";
        ruleList.appendChild(classic_mode);
    }

    if (rules.with_myself) {
        const withMyself = document.createElement("li");
        withMyself.innerHTML = "With Myself";
        ruleList.appendChild(withMyself);
    }

}

function addMode(event) {
    mode = event.target.closest(".mode-block");
    if (mode.classList.contains("mode-inactive") || mode.classList.contains("mode-dev")) return;
    const checkBox = mode.getElementsByClassName("mode-checkbox")[0];
    if (mode.classList.contains("mode-set")) {
        mode.classList.remove("mode-set");
        checkBox.innerHTML = "";
    } else {
        mode.classList.add("mode-set");
        checkBox.innerHTML = "&#10004;";
    }
    modes = getChosenModes();
    let token = getToken();
    fetch(`${origin}/modes`, {
        method: "PUT",
        mode: "cors",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(modes),
    })
        .then(response => {
            if (response.ok) {
                return response.json()
            }
            onFetchError(response.status);
            return Promise.reject(response);
        })
        .then(response => {
            updateCurrentRules(response);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
}

function getChosenModes() {
    // Возвращает список объектов выбранных модов для отправки на сервер
    chosenModeElements = document.getElementsByClassName("mode-set");
    const modes = [];
    for (modeElem of chosenModeElements) {
        let mode = {name: "does not matter", id: modeElem.dataset.id};
        modes.push(mode);
    }
    return modes
}

function sendFormCreateGame(event) {
    event.preventDefault();
    modes = getChosenModes();
    let data = {action: "create_game"};
    data.modes = modes;
    let formData = new FormData(this)
    formData.forEach(function (value, key) {
        data[key] = value;
    });

    send(data);
}
