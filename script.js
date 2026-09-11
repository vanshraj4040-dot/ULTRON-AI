/* =========================================
   ULTRON FRONTEND CONTROLLER
========================================= */

const userInput =
    document.getElementById("userInput");

const sendButton =
    document.getElementById("sendButton");

const chatWindow =
    document.getElementById("chatWindow");

const voiceButton =
    document.getElementById("voiceButton");

const clock =
    document.getElementById("clock");

const brainStatus =
    document.getElementById("brainStatus");


/* =========================================
   CLOCK
========================================= */

function updateClock() {

    const now = new Date();

    const hours =
        String(now.getHours()).padStart(2, "0");

    const minutes =
        String(now.getMinutes()).padStart(2, "0");

    const seconds =
        String(now.getSeconds()).padStart(2, "0");

    clock.textContent =
        `${hours}:${minutes}:${seconds}`;
}

setInterval(updateClock, 1000);

updateClock();


/* =========================================
   ADD MESSAGE
========================================= */

function addMessage(sender, text, isUser = false) {

    const message =
        document.createElement("div");

    message.className =
        isUser
            ? "message user-message"
            : "message ultron-message";

    message.innerHTML = `
        <div class="message-label">
            ${sender}
        </div>

        <p>${escapeHTML(text)}</p>
    `;

    chatWindow.appendChild(message);

    chatWindow.scrollTop =
        chatWindow.scrollHeight;
}


/* =========================================
   SECURITY
   Prevent user text from becoming HTML
========================================= */

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


/* =========================================
   CURRENT DEMO AI
========================================= */

function generateDemoResponse(input) {

    const command =
        input.toLowerCase().trim();


    if (
        command.includes("hello") ||
        command.includes("hi") ||
        command.includes("hey")
    ) {

        return "Greetings. ULTRON interface is online and awaiting your command.";
    }


    if (
        command.includes("who are you") ||
        command.includes("identify")
    ) {

        return "I am ULTRON — an experimental personal artificial intelligence system.";
    }


    if (
        command.includes("status") ||
        command.includes("system")
    ) {

        return "System status: ONLINE\nCore: READY\nNetwork: CONNECTED\nAI Interface: OPERATIONAL\nNeural Brain: STANDBY";
    }


    if (
        command.includes("diagnostic")
    ) {

        return "Running frontend diagnostics...\n\n✓ Interface: PASS\n✓ JavaScript: PASS\n✓ Communication layer: PASS\n✓ UI core: PASS\n\nNeural brain integration: PENDING.";
    }


    if (
        command.includes("brain")
    ) {

        return "The ULTRON neural brain integration is currently pending. The 30M parameter brain will be connected here later.";
    }


    return "Command received. My neural intelligence backend is not connected yet. This interface is currently running in demonstration mode.";
}


/* =========================================
   SEND COMMAND
========================================= */

function sendMessage() {

    const text =
        userInput.value.trim();

    if (!text) {
        return;
    }


    addMessage(
        "YOU",
        text,
        true
    );


    userInput.value = "";


    brainStatus.textContent =
        "PROCESSING";


    setTimeout(() => {

        const response =
            generateDemoResponse(text);

        addMessage(
            "ULTRON",
            response
        );

        brainStatus.textContent =
            "STANDBY";

    }, 600);
}


/* =========================================
   SEND BUTTON
========================================= */

sendButton.addEventListener(
    "click",
    sendMessage
);


/* =========================================
   ENTER KEY
========================================= */

userInput.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            sendMessage();
        }
    }
);


/* =========================================
   QUICK ACTIONS
========================================= */

const quickButtons =
    document.querySelectorAll(
        ".quick-actions button"
    );


quickButtons.forEach(button => {

    button.addEventListener(
        "click",
        () => {

            userInput.value =
                button.dataset.command;

            sendMessage();
        }
    );

});


/* =========================================
   VOICE BUTTON
========================================= */

voiceButton.addEventListener(
    "click",
    () => {

        addMessage(
            "ULTRON",
            "Voice interface is reserved for the next integration stage."
        );

    }
);


/* =========================================
   INITIALIZATION
========================================= */

console.log(
    "ULTRON interface initialized."
);

console.log(
    "Neural backend: NOT CONNECTED"
);

console.log(
    "30M brain integration: PENDING"
);
