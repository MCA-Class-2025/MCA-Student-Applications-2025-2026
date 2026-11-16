// ==========================================
// Elements
// ==========================================

const aiButton = document.getElementById("aiButton");

const chatWindow = document.getElementById("chatWindow");

const closeChat = document.getElementById("closeChat");

const minimizeChat = document.getElementById("minimizeChat");

const chatInput = document.getElementById("chatInput");

const sendBtn = document.getElementById("sendBtn");

const chatBody = document.getElementById("chatBody");


// ==========================================
// Open Chat
// ==========================================

aiButton.addEventListener("click", function(){

    chatWindow.style.display = "flex";

    aiButton.style.display = "none";

});


// ==========================================
// Close Chat
// ==========================================

closeChat.addEventListener("click", function(){

    chatWindow.style.display = "none";

    aiButton.style.display = "flex";

});


// ==========================================
// Minimize Chat
// ==========================================

minimizeChat.addEventListener("click", function(){

    chatWindow.style.display = "none";

    aiButton.style.display = "flex";

});


// ==========================================
// Send Message
// ==========================================

async function sendMessage(){

    let question = chatInput.value.trim();

    if(question === "")
        return;

    // -----------------------------
    // Show Admin Message
    // -----------------------------

    let message = document.createElement("div");

    message.className = "message admin-message";

    message.innerHTML =
        '<div class="bubble">' +
        question +
        '</div>';

    chatBody.appendChild(message);

    chatInput.value = "";

    chatBody.scrollTo({
        top: chatBody.scrollHeight,
        behavior: "smooth"
    });

    // -----------------------------
    // Send to PHP
    // -----------------------------

    try{

        const response = await fetch("../ai/chatbot.php",{

            method:"POST",

            headers:{
                "Content-Type":"application/x-www-form-urlencoded"
            },

            body:"question=" + encodeURIComponent(question)

        });

        const data = await response.json();

        console.log(data);

        // -----------------------------
        // Show AI Reply
        // -----------------------------

        let reply = document.createElement("div");

        reply.className = "message ai-message";

        if(data.status === "success"){

            reply.innerHTML =
                '<div class="bubble">' +
                data.answer.replace(/\n/g, "<br>") +
                '</div>';

        }
        else{

            reply.innerHTML =
                '<div class="bubble">' +
                data.message +
                '</div>';

        }

        chatBody.appendChild(reply);

        chatBody.scrollTop = chatBody.scrollHeight;

    }

    catch(error){

        console.error(error);

        let reply = document.createElement("div");

        reply.className = "message ai-message";

        reply.innerHTML =
            '<div class="bubble">' +
            "Unable to communicate with AI assistant." +
            '</div>';

        chatBody.appendChild(reply);

    }

}


// ==========================================
// Send Button
// ==========================================

sendBtn.addEventListener("click", sendMessage);


// ==========================================
// Press Enter
// ==========================================

chatInput.addEventListener("keypress", function(e){

    if(e.key === "Enter"){

        sendMessage();

    }

});