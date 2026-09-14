const wsURI = "ws:localhost:8765";
const chat = document.getElementById("chat")
let websocket;
let identifier = {
    name: "",
    password: ""
};


function processIdentification(package) {
    if (package.type == "identification") {
        console.log("Identification started")
            if (package.content == "ok") {
                console.log("connected")
                const popup = document.getElementById("myPopup");
                popup.close();
                identificationProcess.removeProcess()
                messageProcess.addProcess()
            } else if (package.content == "password") {
                console.log("not ok")
                document.getElementById("userPassword").value = ''
            }
        } 
}

function processMessage(package) {
    if (package.type == "message" || package.type == "connection"){
            console.log("Show")
            showMessage(package)
            console.log(`Message received '${package.content}'`)
        }
}

function processPingPong(package) {
    if (package.type == "ping") {
            pong = new Package("Pong", null, "ping")
            pong.send()
        }
}
class Process {
    constructor(fn) {
        this.fn = fn
        this.controller = new AbortController()
    }

    addProcess() {
        console.log("Adding process")
        websocket.addEventListener("message", ({ data }) => {
            console.log(this.fn)
            let pkg = Package.receive(data)
            this.fn(pkg);
        }, {signal : this.controller.signal})
    }
    removeProcess() {
        this.controller.abort()
    }
}

identificationProcess = new Process(processIdentification)
messageProcess = new Process(processMessage)
pingpongProcess = new Process(processPingPong)

class Package {
    constructor(content = undefined, author = undefined,type = undefined, counter = 0) {
        this.content = content
        this.author = author
        this.type = type
        this.counter = counter
    }

    static receive(data) {
        let message = JSON.parse(data)
        return new Package(message.content, message.author, message.type, message.counter)
    }

    send() {
        websocket.send(JSON.stringify(this))
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const popup = document.getElementById("myPopup");
    popup.showModal();
});

function initSocket() {
    websocket = new WebSocket(wsURI)
    websocket.addEventListener("open", () => {
        console.log("CONNECTED");
    });
    pingpongProcess.addProcess()
    identificationProcess.addProcess()
}

function showMessage(package) {
    const newMessage = document.createElement("p")
    line = `[${package.author}]: ${package.content}`
    newMessage.textContent = line
    chat.appendChild(newMessage)
    chat.scrollTop = chat.scrollHeight;
}

function sendMessage() {
    textarea = document.getElementById("messageInput")
    content = textarea.value
    if (content == '') {
        return
    }
    textarea.value = ''
    package = new Package(content, name, "message")
    package.send()
}

function sendIdentification() {
    name = document.getElementById("name").value
    password = document.getElementById("userPassword").value
    identifier.name = name
    identifier.password = password
    identification = new Package(`${identifier.name}\n${identifier.password}`, identifier.name, "identification")
    identification.send()
    identificationProcess.addProcess()
}



function handleKeyDown(event, type) {
    if (event.key == 'Enter') {
        event.preventDefault()
        const form = event.target.form 

        if (form && !form.checkValidity()) {
      form.reportValidity();
      return; 
    }
        const messageInput = document.getElementById("messageInput");
        messageInput.blur();
        if (type == 'message'){
            sendMessage()
        } else if (type == 'identification') {
            sendIdentification()
        }
    }
}




initSocket()
