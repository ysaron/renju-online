const mainContainer = document.getElementById("main")
const screens = document.getElementById("screens")
const onlineBlock = document.getElementById("online-block")
const onlineCounterBlock = document.getElementById("online-counter-block")
const screenMainNotLogged = document.getElementById("mainscreen-not-logged")
const screenMainLogged = document.getElementById("mainscreen-logged")
const screenGameCreation = document.getElementById("game-creation")
const screenGameList = document.getElementById("game-list-screen")
const screenGame = document.getElementById("game-screen")
const activeGameMarker = document.getElementById("active-game-marker")

const modalSignup = document.getElementById("modal-signup")
const modalLogin = document.getElementById("modal-login")
const modalRequestVerification = document.getElementById("modal-request-verify")
const modalForgotPassword = document.getElementById("modal-forgot-password")
const modalResetPassword = document.getElementById("modal-reset-password")
const modalVerify = document.getElementById("modal-verify")
const modalNotification = document.getElementById("modal-notification")

const btnLogout = document.querySelector(".logout")
const spanUsername = document.querySelector(".span-username")
const btnMyStat = document.querySelector(".btn-myStat")
const btnRequestVerification = document.querySelector(".request-verify")
const btnForgotPassword = document.querySelector(".forgot-password")

const btnsCreateGame = document.getElementsByClassName("btn-create-game")
const btnsJoinGame = document.getElementsByClassName("btn-join-game")

const btnsHome = document.getElementsByClassName('btn-home')
for (let btn of btnsHome) {btn.addEventListener("click", showMainScreen)}

const btnRefreshGameList = document.querySelector(".btn-refresh");

const formSignup = document.querySelector(".form-signup")
const formRequestVerification = document.querySelector(".form-request-verify")
const formForgotPassword = document.querySelector(".form-forgot-password")
const formResetPassword = document.querySelector(".form-reset-password")
const formVerify = document.querySelector(".form-verify")
const formLogin = document.querySelector(".form-login")

const formCreateGame = document.querySelector(".form-game-creation")

const commonData = document.getElementById("common-data")
const origin = `http://${commonData.dataset.remotehost}:${commonData.dataset.port}`
const wsURL = `ws://${commonData.dataset.remotehost}:${commonData.dataset.port}/renju/ws`

const joinBtnTemp = document.getElementById("join-btn-template");
const spectateBtnTemp = document.getElementById("spectate-btn-template");
const svgEyeTemp = document.getElementById("svg-eye");

const playerRoles = ["1", "2", "3"];
const spectatorRoles = ["4"];

let ws;

function showMainScreen() {
    hideAllScreens();
    if (sessionStorage.getItem('token') && sessionStorage.getItem('username')) {
        let username = sessionStorage.getItem('username');
        showUsername(username);
        screenMainLoggedShow();
    } else {
        screenMainNotLoggedShow();
    }
}

function getToken() {
    token = sessionStorage.getItem('token');
    if (!token) {
        alert("Unauthorized. Please, log in");
        closeWS();
        showMainScreen();
    }
    return token
}

document.addEventListener("DOMContentLoaded", function() {
    showMainScreen();
    if (sessionStorage.getItem('token') && sessionStorage.getItem('username')) openWS();
});

function onFetchError(statusCode) {
    switch (statusCode) {
        case 401:
            logout();
            break;
        default:
            break;
    }
}

function humanizeError(code) {
    switch (code) {
        case "REGISTER_USER_ALREADY_EXISTS":
            return "A user with this name or email already exists."
        case "VERIFY_USER_ALREADY_VERIFIED":
            return "The user is already verified."
        case "VERIFY_USER_BAD_TOKEN":
            return "Bad token, non-existing user or not the e-mail currently set for the user."
        case "RESET_PASSWORD_BAD_TOKEN":
            return "Bad or expired token."
        case "BAD_TOKEN":
            return "Please, log in again."
        case "EXPIRED_TOKEN":
            return "Expired access token"
        case "USER_NOT_FOUND":
            return "User not found"
        case "USER_NOT_VERIFIED":
            return "User not verified. Try log in again"
        case "LOGIN_BAD_CREDENTIALS":
            return "Bad credentials or user is inactive."
        case "LOGIN_USER_NOT_VERIFIED":
            return "The user is not verified"
        case "PASSWORD_TOO_SHORT":
            return "Password should be at least 8 characters"
        case "PASSWORD_INSECURE":
            return "Password is too similar to email or username"
        default:
            return code
    }
}

function getErrorInfo(response) {
    switch (response.detail.constructor.name) {
        case "Object":
            return response.detail.reason
        case "Array":
            return JSON.stringify(response)
        default:
            return humanizeError(response.detail)
    }
}

function hideAllScreens() {
    for (const child of screens.children) {
        if (child.classList.contains('screen')) {
            child.style.display = 'none';
        }
    }
}

function screenMainNotLoggedShow() {
    screenMainNotLogged.style.display = "flex"
}

function screenMainNotLoggedHide() {
    screenMainNotLogged.style.display = "none"
}

function screenMainLoggedShow() {
    screenMainLogged.style.display = "flex"
}

function screenMainLoggedHide() {
    screenMainLogged.style.display = "none"
}

function createRulesTooltip(time_limit, board_size, classic_mode, with_myself, three_players) {
    const tooltip = document.createElement("div");

    if (time_limit != null) {
        let p = document.createElement("p");
        if (time_limit == 0) {
            var limit = "No";
        } else {
            var limit = `${time_limit}s`;
        }
        p.innerHTML = `Time limit: ${limit}`;
        tooltip.appendChild(p);
    }
    if (board_size) {
        let p = document.createElement("p");
        p.innerHTML = `Board: ${board_size} x ${board_size}`;
        tooltip.appendChild(p);
    }
    if (classic_mode) {
        let p = document.createElement("p");
        p.innerHTML = "Classic mode";
        tooltip.appendChild(p);
    }
    if (with_myself) {
        let p = document.createElement("p");
        p.innerHTML = "With myself";
        tooltip.appendChild(p);
    }
    if (three_players) {
        let p = document.createElement("p");
        p.innerHTML = "3 players";
        tooltip.appendChild(p);
    }
    return tooltip
}

function getGameStateColor(state) {
    switch (state) {
        case "created":
            return "green"
        case "pending":
            return "blue"
        case "finished":
            return "red"
        default:
            return "black"
    }
}

function makeLoaderGrid(id) {
    let grid = document.createElement("div");
    grid.classList.add("lds-grid");
    for (let i=0; i<9; i++) {
        let elem = document.createElement("div");
        grid.appendChild(elem);
    }
    grid.id = id;
    return grid
}

function openWS() {
    let token = getToken();
    ws = new WebSocket(`${wsURL}?querytoken=${token}`);
    console.log("example", `${wsURL}?querytoken=${token}`)
    setMeOnline();
    wsDispatcher();
}

function wsDispatcher() {
    ws.onopen = function (event) {
        console.log("open", event);
    }

    ws.onmessage = function (event) {
        let data = JSON.parse(event.data);
        console.log("data.action", data.action);
        switch (data.action) {
            case "online_counter":
                updateTotalOnline(data.total);
                break;
            case "game_added":
                // была создана игра --> обновляем список GameList (+ gameBlock в список)
                addGameInList(data.game);
                break;
            case "open_game":
                // открываем игру как игрок или зритель, рендерим экран игры
                openGame(data.game, data.my_role);
                break;
            case "player_joined":
                // отражаем изменения на экране игры (update playerBlock)
                playerJoined(data.game, data.player_name);
                console.log("Game: ", data.game);
                break;
            case "player_joined_list":
                // отражаем изменения на экране списка игр (индикатор, возможная блокировка кнопки JOIN)
                playerJoinedList(data.game, data.player_name);
                break;
            case "spectator_joined":
                // отражаем изменения на экране игры (инкремент счетчика зрителей)
                spectatorJoined(data.game);
                break;
            case "spectator_joined_list":
                // отражаем изменения на экране списка игр (инкремент счетчика зрителей)
                break;
            case "ready":
                playerReady(data.game, data.player_name, data.player_role);
                break;
            case "game_started":
                gameStarted(data.game);
                break;
            case "unblock_board":
                unblockBoard(data.game.id);
                break;
            case "game_removed_list":
                gameRemovedList(data.game_id);
                break;
            case "game_removed":
                gameRemoved(data.game_id);
                break;
            case "update_game_list":
                updateGameInList(data.game);
                break;
            case "update_game":
                updateGame(data.game);
                break;
            case "move":
                renderMove(data.game, data.move);
                break;
            case "left_game":
                leftGame(data.game);
                break;
            case "game_finished":
                gameFinished(data.game, data.result);
                break;
            case "error":
                alert(data.detail);
                break;
            default:
                break
        }
    }

    ws.onclose = function (event) {
        console.log('Disconnected;', event);
        setMeOffline();
        hideTotalOnline();
        if (event.code == 1008) {
            console.log(event.code);
            logout();
        }
    }
    ws.onerror = function (event) {
        console.log('ERROR:', event);
    }
}

function send(data) {
    ws.send(JSON.stringify(data));
}

function closeWS() {
    ws.close();
}

function setMeOnline() {
    let indicator = onlineBlock.querySelector(".indicator");
    let onlineText = onlineBlock.querySelector(".online-text");
    indicator.className = "";
    indicator.classList.add("indicator", "indicator-green");
    onlineText.innerHTML = "Online";
}

function setMeOffline() {
    let indicator = onlineBlock.querySelector(".indicator");
    let onlineText = onlineBlock.querySelector(".online-text");
    indicator.className = "";
    indicator.classList.add("indicator", "indicator-red");
    onlineText.innerHTML = "Offline";
}

function updateTotalOnline(number) {
    onlineCounterBlock.style.display = "flex";
    let counter = onlineCounterBlock.querySelector(".online-counter");
    counter.innerHTML = number;
}

function hideTotalOnline() {
    onlineCounterBlock.style.display = "none";
}

function blockButton(btn) {
    btn.disabled = true;
    btn.classList.add("btn-blocked");
}

function unblockButton(btn) {
    btn.disabled = false;
    btn.classList.remove("btn-blocked");
}

function forgetGame(game_id) {
    console.log("DELETE ", game_id);
    delete currentBoards[game_id];
}
