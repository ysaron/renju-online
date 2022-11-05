const mainContainer = document.getElementById("main")
const screenMainNotLogged = document.getElementById("mainscreen-not-logged")
const screenMainLogged = document.getElementById("mainscreen-logged")
const screenGameCreation = document.getElementById("game-creation")
const screenGameList = document.getElementById("game-list-screen")

const modalSignup = document.getElementById("modal-signup")
const modalLogin = document.getElementById("modal-login")
const modalRequestVerification = document.getElementById("modal-request-verify")
const modalForgotPassword = document.getElementById("modal-forgot-password")
const modalResetPassword = document.getElementById("modal-reset-password")
const modalVerify = document.getElementById("modal-verify")

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

const joinSpectateBtnsTemp = document.getElementById("join-spectate-btns");
const svgEyeTemp = document.getElementById("svg-eye");

const playerRoles = ["1", "2", "3"];
const spectatorRoles = ["4"];

function showMainScreen() {
    if (sessionStorage.getItem('token') && sessionStorage.getItem('username')) {
        let username = sessionStorage.getItem('username');
        showUsername(username);
        hideAllScreens();
        screenMainLoggedShow();
    } else {
        hideAllScreens();
        screenMainNotLoggedShow();
    }
}

function getToken() {
    token = sessionStorage.getItem('token');
    if (!token) {
        alert("Unauthorized. Please, log in");
        showMainScreen();
    }
    return token
}

document.addEventListener("DOMContentLoaded", showMainScreen);

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
        case "LOGIN_BAD_CREDENTIALS":
            return "Bad credentials or user is inactive."
        case "LOGIN_USER_NOT_VERIFIED":
            return "The user is not verified"
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
    for (const child of mainContainer.children) {
        child.style.display = 'none';
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