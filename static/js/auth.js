const mainContainer = document.getElementById("main")
const screenMainNotLogged = document.getElementById("mainscreen-not-logged")
const screenMainLogged = document.getElementById("mainscreen-logged")

const modalSignup = document.getElementById("modal-signup")
const modalLogin = document.getElementById("modal-login")
const modalRequestVerification = document.getElementById("modal-request-verify")
const modalForgotPassword = document.getElementById("modal-forgot-password")
const modalResetPassword = document.getElementById("modal-reset-password")
const modalVerify = document.getElementById("modal-verify")
const modalTop = document.getElementById("modal-top")
const modalMyStat = document.getElementById("modal-myStat")

const btnLogout = document.querySelector(".logout")
const spanUsername = document.querySelector(".span-username")
const btnMyStat = document.querySelector(".btn-myStat")
const btnRequestVerification = document.querySelector(".request-verify")
const btnForgotPassword = document.querySelector(".forgot-password")

const formSignup = document.querySelector(".form-signup")
const formRequestVerification = document.querySelector(".form-request-verify")
const formForgotPassword = document.querySelector(".form-forgot-password")
const formResetPassword = document.querySelector(".form-reset-password")
const formVerify = document.querySelector(".form-verify")
const formLogin = document.querySelector(".form-login")

const commonData = document.getElementById("common-data")
const origin = `http://${commonData.dataset.remotehost}:${commonData.dataset.port}`

document.addEventListener("DOMContentLoaded", function() {
    // автологин

//    console.log(sessionStorage.getItem('token'));
//    console.log(sessionStorage.getItem('username'));
    if (sessionStorage.getItem('token') && sessionStorage.getItem('username')) {
        let username = sessionStorage.getItem('username');
//        hideLoginSignup();
//        showBtnMyStat();
        showUsername(username);
        hideAllScreens();
        screenMainLoggedShow();
//        showLogout();
    } else {
        hideAllScreens();
        screenMainNotLoggedShow();
    }
});

document.querySelector(".signup").addEventListener("click", modalSignupOpen)
document.getElementsByClassName("close")[0].addEventListener("click", modalSignupClose)
formSignup.addEventListener("submit", sendFormSignup)
formRequestVerification.addEventListener("submit", sendFormRequestVerification)
formForgotPassword.addEventListener("submit", sendFormForgotPassword)
formResetPassword.addEventListener("submit", sendFormResetPassword)
formVerify.addEventListener("submit", sendFormVerify)

document.querySelector(".login").addEventListener("click", modalLoginOpen)
document.getElementsByClassName("close")[1].addEventListener("click", modalLoginClose)
formLogin.addEventListener("submit", sendFormLogin)

btnRequestVerification.addEventListener("click", modalRequestVerificationOpen)
btnForgotPassword.addEventListener("click", modalForgotPasswordOpen)
btnLogout.addEventListener("click", logout)

document.querySelector(".btn-top").addEventListener("click", modalTopOpen)
document.querySelector(".close-top").addEventListener("click", modalTopClose)

btnMyStat.addEventListener("click", modalMyStatOpen)
document.querySelector(".close-myStat").addEventListener("click", modalMyStatClose)


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

function modalSignupOpen() {
    modalSignup.style.display = "block"
}

function modalSignupClose() {
    modalSignup.style.display = "none";
    formSignup.reset();
}

function modalLoginOpen() {
    modalLogin.style.display = "block"
}

function modalLoginClose() {
    modalLogin.style.display = "none";
    formLogin.reset();
}

function modalRequestVerificationOpen() {modalRequestVerification.style.display = "block"}

function modalRequestVerificationClose() {modalRequestVerification.style.display = "none"}

function modalVerifyOpen() {modalVerify.style.display = "block"}

function modalVerifyClose() {
    modalVerify.style.display = "none";
    formVerify.reset();
}

function modalForgotPasswordOpen() {
    modalForgotPassword.style.display = "block";
}

function modalForgotPasswordClose() {
    modalForgotPassword.style.display = "none";
    formForgotPassword.reset();
}

function modalResetPasswordOpen() {
    modalResetPassword.style.display = "block";
}

function modalResetPasswordClose() {
    modalResetPassword.style.display = "none";
    formResetPassword.reset();
}

function modalTopOpen() {
    modalTop.style.display = "block"
}

function modalTopClose() {
    modalTop.style.display = "none"
}

function modalMyStatOpen() {
    modalMyStat.style.display = "block"
//    send({action: "stat"})
}

function modalMyStatClose() {
    modalMyStat.style.display = "none"
}

function showLogout() {
    btnLogout.style.display = "block"
}

function hideLogout() {
    btnLogout.style.display = "none"
}

function showRequestVerification() {
    btnRequestVerification.style.display = "block"
}

function hideRequestVerification() {
    btnRequestVerification.style.display = "none"
}

function showLoginSignup() {
    document.querySelector(".signup").style.display = "block"
    document.querySelector(".login").style.display = "block"
}

function hideLoginSignup() {
    document.querySelector(".signup").style.display = "none"
    document.querySelector(".login").style.display = "none"
}

function showUsername(username) {
    spanUsername.innerHTML = username
}

function hideUsername() {
    spanUsername.innerHTML = ""
}

function showBtnMyStat() {
    btnMyStat.style.display = "block"
}

function hideBtnMyStat() {
    btnMyStat.style.display = "none"
}

window.onclick = function (event) {
    switch (event.target) {
        case modalSignup:
            modalSignupClose()
            break
        case modalLogin:
            modalLoginClose()
            break
        case modalRequestVerification:
            modalRequestVerificationClose()
            break
        case modalVerify:
            modalVerifyClose()
            break
        case modalForgotPassword:
            modalForgotPasswordClose()
            break
        case modalResetPassword:
            modalResetPasswordClose()
            break
        case modalTop:
            modalTopClose()
            break
        case modalMyStat:
            modalMyStatClose()
            break
        default:
            break
    }
}

function getMe(token) {
    // возвращает промис с данными о текущем пользователе
    return fetch(`${origin}/users/me`, {
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
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            console.log(info);
        }))
}

function requestVerification(user_email) {
    // запрашивает отправку токена верификации емейла на этот емейл

    let data = {email: user_email};
    fetch(`${origin}/auth/request-verify-token`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                return response.json()
            }
            return Promise.reject(response);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
}

function sendFormRequestVerification() {
    event.preventDefault()
    let data = {}
    let formData = new FormData(this)
    formData.forEach(function (value, key) {
        data[key] = value;
    });
    requestVerification(data.email);
    modalRequestVerificationClose();
    modalVerifyOpen();
}

function sendFormSignup(event) {
    // отправляет на сервер данные с формы регистрации

    event.preventDefault()
    let data = {}
    let formData = new FormData(this)
    formData.forEach(function (value, key) {
        data[key] = value;
    });

    fetch(`${origin}/auth/register`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (response.ok) {
                alert("Account created")
                modalSignupClose()

                return response.json()
            }
            return Promise.reject(response);
        })
        .then(response => {
            requestVerification(response.email);
            modalVerifyOpen();
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
}

function sendFormVerify(event) {
    // отправляет на сервер токен верификации емейла

    event.preventDefault()
    let data = {}
    let formData = new FormData(this)
    formData.forEach(function (value, key) {
        data[key] = value;
    });

    fetch(`${origin}/auth/verify`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                alert("Account verified")
                modalVerifyClose()
                return response.json()
            }
            return Promise.reject(response);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
}

function sendFormLogin(event) {
    // отправляет на сервер данные для аутентификации юзера как multipart/form-data

    event.preventDefault()
    let data = {}
    let form = new FormData(this)

    fetch(`${origin}/auth/login`, {
        method: "POST",
        mode: "cors",
        body: form,
    })
        .then(response => {
            if (response.ok) {
                return response.json()
            }
            return Promise.reject(response);
        })
        .then(response => {
//            console.log(`Token = ${response.access_token}`);
            getMe(response.access_token).then(myData => {
//                console.log(`myData: ${JSON.stringify(myData)}`);
                sessionStorage.setItem('username', myData.name);
            })
                .then(myData => {
                    let username = sessionStorage.getItem('username')
                    showUsername(username);
                })
                .catch(err => {console.log(err)})

            sessionStorage.setItem('token', response.access_token)

            screenMainNotLoggedHide();
            screenMainLoggedShow();
//            showLogout()
//            showBtnMyStat()
//            hideLoginSignup()
            modalLoginClose()
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
            if (response.detail == "LOGIN_USER_NOT_VERIFIED") {
                showRequestVerification();
            }
        }))
}

function sendFormForgotPassword(event) {
    // отправляет на сервер емейл, для которого запрашивается смена пароля

    event.preventDefault()
    let data = {}
    let formData = new FormData(this)
    formData.forEach(function (value, key) {
        data[key] = value;
    });

    fetch(`${origin}/auth/forgot-password`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                modalForgotPasswordClose()
                modalResetPasswordOpen()
                return response.json()
            }
            return Promise.reject(response);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
}

function sendFormResetPassword(event) {
    // отправляет на сервер новый пароль юзера и верифицирующий токен

    event.preventDefault()
    let data = {}
    let formData = new FormData(this)
    formData.forEach(function (value, key) {
        data[key] = value;
    });

    fetch(`${origin}/auth/reset-password`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                alert("Password changed")
                modalResetPasswordClose()
                hideRequestVerification()
                return response.json()
            }
            return Promise.reject(response);
        })
        .catch(response => response.json().then(response => {
            let info = getErrorInfo(response);
            alert(info);
        }))
}

function logout() {
    sessionStorage.removeItem("token")
    sessionStorage.removeItem("username")

    screenMainLoggedHide();
    screenMainNotLoggedShow();
//    hideLogout()
//    hideBtnMyStat()
//    hideUsername()
//    showLoginSignup()
    closeWS()
    start()
}
