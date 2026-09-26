const wsURI = "ws://localhost:8765";
const chat = document.getElementById("chat");
let websocket;
let authenticator = {
    name: "",
    password: ""
};
function processIdentification(message) {
    if (message.type == "identification") {
        console.log("Identification started");
        console.log("connected");
        const popup = document.getElementById("myPopup");
        popup.close();
        manager.removeProcess(identificationProcess);
        manager.addProcess(chatProcess);
    }else if (message.type == "error") {
        console.log("not ok");
        let passwordField = document.getElementById("userPassword");
        passwordField.value = '';
    }
}

function processChat(message) {
    if (message.type == "chat" || message.type == "connection") {
        console.log("Show");
        showChat(message.payload);
        console.log(`Message received '${message.payload.chat}'`);
    }      
}
function processPingPong(message) {
    if (message.type == "ping") {
        let pong = new Message("ping", "Pong");
        pong.send();
    }
}
class Process {
    constructor(fn) {
        this.fn = fn;
        this.controller = new AbortController();
    }
}
class ProcessManager {
    constructor() {
        if (!!ProcessManager.instance) {
            return ProcessManager.instance;
        }
        ProcessManager.instance = this;
        return this;
    }
    addProcess(process) {
        console.log(process)
        console.log("Adding process");
        websocket.addEventListener("message", ({ data }) => {
            let pkg = Message.receive(data);
            process.fn(pkg);
        }, { signal: process.controller.signal });
    }
    removeProcess(process) {
        process.controller.abort();
    }
}
const identificationProcess = new Process(processIdentification);
const chatProcess = new Process(processChat);
const pingpongProcess = new Process(processPingPong);
const manager = new ProcessManager();
class Message {
    constructor(type, payload) {
        this.payload = payload;
        this.type = type;
    }
    static receive(data) {
        let message = JSON.parse(data);
        return new Message(message.type, message.payload);
    }
    send() {
        websocket.send(JSON.stringify(this));
    }
}
document.addEventListener("DOMContentLoaded", () => {
    const popup = document.getElementById("myPopup");
    popup.showModal();
});
function initSocket() {
    websocket = new WebSocket(wsURI);
    websocket.addEventListener("open", () => {
        console.log("CONNECTED");
    });
    manager.addProcess(pingpongProcess);
    manager.addProcess(identificationProcess);
}
function showChat(payload) {
    const newMessage = document.createElement("p");
    let line = `[${payload.author}]: ${payload.chat}`;
    newMessage.textContent = line;
    if (chat) {
        chat.appendChild(newMessage);
        chat.scrollTop = chat.scrollHeight;
    }
}
function sendMessage() {
    let textarea = document.getElementById("messageInput");
    let chat = textarea.value;
    if (chat == '') {
        return;
    }
    textarea.value = '';
    let message = new Message("chat", {author: authenticator.name, chat: chat});
    message.send();
}
function sendIdentification() {
    let name = document.getElementById("name").value;
    let password = document.getElementById("userPassword").value;
    authenticator.name = name;
    authenticator.password = password;
    let authentification = new Message("identification", {name : authenticator.name, password: authenticator.password});
    authentification.send();
    manager.addProcess(identificationProcess);
}
function handleKeyDown(event, type) {
    if (event.key == 'Enter') {
        event.preventDefault();
        const form = event.target.form;
        if (form && !form.checkValidity()) {
            form.reportValidity();
            return;
        }
        const messageInput = document.getElementById("messageInput");
        messageInput.blur();
        if (type == 'message') {
            sendMessage();
        }
        else if (type == 'identification') {
            sendIdentification();
        }
    }
}
initSocket();