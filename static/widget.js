(function() {
    if (window.__smRobotitoWidgetLoaded) {
        return;
    }
    window.__smRobotitoWidgetLoaded = true;

    // URL base de la API y parámetros de integración
    const scriptTag = document.currentScript || document.querySelector('script[data-api-key][src*="widget.js"]');
    let apiBaseUrl = "http://localhost:8000";
    let apiKey = "";
    let initialPrimaryColor = "#007bff";
    let initialBotName = "Asistente Inteligente SixManager";
    let widgetPosition = "right";
    let widgetZIndex = "999999";
    if (scriptTag) {
        const explicitApiBase = scriptTag.getAttribute('data-api-base');
        if (explicitApiBase) {
            apiBaseUrl = explicitApiBase.replace(/\/$/, "");
        } else if (scriptTag.src) {
            const url = new URL(scriptTag.src);
            apiBaseUrl = `${url.protocol}//${url.host}`;
        }
        apiKey = scriptTag.getAttribute('data-api-key') || "";
        initialPrimaryColor = scriptTag.getAttribute('data-primary-color') || initialPrimaryColor;
        initialBotName = scriptTag.getAttribute('data-bot-name') || initialBotName;
        widgetPosition = scriptTag.getAttribute('data-position') === "left" ? "left" : "right";
        widgetZIndex = scriptTag.getAttribute('data-z-index') || widgetZIndex;
    }

    // Gestión de Session ID
    let sessionId = sessionStorage.getItem("sm-chat-session-id");
    if (!sessionId) {
        sessionId = self.crypto && self.crypto.randomUUID ? self.crypto.randomUUID() : Math.random().toString(36).substring(2, 15);
        sessionStorage.setItem("sm-chat-session-id", sessionId);
    }

    console.log("Widget SixManager cargado");

    // Cargar Marked.js dinámicamente para parsear Markdown
    if (typeof window.marked === 'undefined') {
        const markedScript = document.createElement("script");
        markedScript.src = "https://cdn.jsdelivr.net/npm/marked/marked.min.js";
        markedScript.onload = () => console.log("Marked JS cargado exitosamente.");
        document.head.appendChild(markedScript);
    }

    // Estilos del Widget (Glassmorphism Premium)
    const style = document.createElement("style");
    style.innerHTML = `
        #sm-chat-widget-container {
            --sm-primary: ${initialPrimaryColor};
            position: fixed;
            bottom: 20px;
            ${widgetPosition}: 20px;
            z-index: ${widgetZIndex};
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        
        #sm-chat-button {
            width: 65px;
            height: 65px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--sm-primary), #00aaff);
            color: white;
            border: none;
            box-shadow: 0 8px 20px rgba(0,123,255,0.4);
            cursor: pointer;
            font-size: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        #sm-chat-button:hover {
            transform: scale(1.1) translateY(-5px);
            box-shadow: 0 12px 25px rgba(0,123,255,0.6);
        }

        #sm-chat-window {
            position: absolute;
            bottom: 90px;
            right: 0;
            width: 380px;
            height: 550px;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            opacity: 0;
            transform: translateY(30px) scale(0.95);
            pointer-events: none;
            transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1);
            max-height: 85vh;
            max-width: 90vw;
        }

        #sm-chat-window.sm-open {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: all;
        }

        #sm-chat-header {
            background: linear-gradient(135deg, var(--sm-primary), #00c6ff);
            color: white;
            padding: 18px 20px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            letter-spacing: 0.5px;
        }

        #sm-chat-header-close {
            cursor: pointer;
            font-size: 24px;
            line-height: 1;
            transition: transform 0.2s;
        }
        #sm-chat-header-close:hover {
            transform: rotate(90deg);
        }

        #sm-chat-messages {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background-color: transparent;
        }

        .sm-chat-msg {
            max-width: 82%;
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.5;
            font-size: 14px;
            word-wrap: break-word;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            animation: sm-msg-fadein 0.3s ease-out;
        }
        
        @keyframes sm-msg-fadein {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .sm-chat-msg.user {
            background: linear-gradient(135deg, var(--sm-primary), #0056b3);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .sm-chat-msg.bot {
            background-color: #ffffff;
            color: #333;
            border: 1px solid #eaeaea;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .sm-chat-msg.bot p { margin: 0 0 8px 0; }
        .sm-chat-msg.bot p:last-child { margin-bottom: 0; }
        .sm-chat-msg.bot ul, .sm-chat-msg.bot ol { margin: 8px 0; padding-left: 20px; }
        .sm-chat-msg.bot li { margin-bottom: 4px; }
        .sm-chat-msg.bot strong { font-weight: 600; color: #111; }
        .sm-chat-msg.bot code { background: #f4f4f4; padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 13px; }
        .sm-chat-msg.bot pre { background: #f4f4f4; padding: 8px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
        .sm-chat-msg.bot pre code { background: transparent; padding: 0; }
        .sm-chat-msg.bot table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
        .sm-chat-msg.bot th, .sm-chat-msg.bot td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        .sm-chat-msg.bot th { background-color: #f8f9fa; font-weight: 600; }

        .sm-chat-msg.sources {
            font-size: 11px;
            color: #777;
            margin-top: 2px;
            background: none;
            box-shadow: none;
            padding: 0 5px;
            align-self: flex-start;
        }

        #sm-chat-input-container {
            display: flex;
            border-top: 1px solid rgba(0,0,0,0.05);
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(5px);
        }

        #sm-chat-input {
            flex-grow: 1;
            border: 1px solid #ccc;
            border-radius: 20px;
            padding: 10px 15px;
            outline: none;
            font-size: 14px;
        }

        #sm-chat-submit {
            background-color: var(--sm-primary);
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            margin-left: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .sm-typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 10px 15px;
            background-color: #e2e8f0;
            border-radius: 12px;
            width: fit-content;
            align-self: flex-start;
        }

        .sm-dot {
            width: 6px;
            height: 6px;
            background-color: #666;
            border-radius: 50%;
            animation: sm-typing 1.4s infinite ease-in-out;
        }

        .sm-dot:nth-child(1) { animation-delay: -0.32s; }
        .sm-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes sm-typing {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        .sm-feedback-container {
            display: flex;
            gap: 8px;
            margin-top: 4px;
            align-self: flex-start;
            padding-left: 4px;
        }

        .sm-feedback-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
            opacity: 0.6;
            transition: all 0.2s;
            padding: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .sm-feedback-btn:hover:not(:disabled) {
            opacity: 1;
            transform: scale(1.2);
        }

        .sm-feedback-btn:disabled {
            cursor: default;
        }

        .sm-feedback-btn.active {
            opacity: 1;
            filter: drop-shadow(0 0 2px var(--sm-primary));
        }
        #sm-chat-footer {
            padding: 5px 10px;
            font-size: 9px;
            color: #999;
            background: #fff;
            text-align: center;
            border-top: 1px solid #eee;
        }

        /* Estilos del Modal */
        #sm-lead-modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000000;
            backdrop-filter: blur(2px);
        }

        #sm-lead-modal {
            background: white;
            width: 90%;
            max-width: 400px;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            position: relative;
            animation: sm-modal-fade 0.3s ease;
        }

        @keyframes sm-modal-fade {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        #sm-lead-modal h3 { margin-top: 0; color: var(--sm-primary); margin-bottom: 10px; }
        #sm-lead-modal p { font-size: 14px; color: #555; margin-bottom: 20px; line-height: 1.5; }
        
        .sm-form-group { margin-bottom: 15px; }
        .sm-form-group label { display: block; font-size: 12px; font-weight: bold; margin-bottom: 5px; color: #444; }
        .sm-form-group input { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 6px; 
            font-size: 14px; 
            box-sizing: border-box;
        }

        .sm-form-legal { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 15px; }
        .sm-form-legal input { transform: translateY(3px); }
        .sm-form-legal label { font-size: 11px; color: #666; line-height: 1.3; }

        .sm-form-captcha { 
            background: #f0f4f8; 
            padding: 10px; 
            border-radius: 6px; 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            margin-bottom: 20px; 
        }
        .sm-captcha-question { font-weight: bold; font-size: 14px; color: var(--sm-primary); white-space: nowrap; }
        .sm-form-captcha input { width: 60px; padding: 5px; border: 1px solid #ccc; border-radius: 4px; text-align: center; }

        #sm-lead-submit {
            width: 100%;
            padding: 12px;
            background: var(--sm-primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
        }
        #sm-lead-submit:hover { opacity: 0.9; }
        #sm-lead-submit:disabled { background: #ccc; cursor: not-allowed; }

        #sm-modal-close {
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 20px;
            cursor: pointer;
            color: #aaa;
        }

        /* Botón de CTA en el chat */
        .sm-cta-container {
            margin: 10px 0;
            padding: 10px;
            background: #f9f9f9;
            border-left: 4px solid var(--sm-primary);
            border-radius: 4px;
            font-size: 13px;
            animation: sm-modal-fade 0.5s ease;
        }
        .sm-cta-btn {
            display: inline-block;
            margin-top: 8px;
            padding: 8px 15px;
            background: var(--sm-primary);
            color: white !important;
            border-radius: 20px;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            border: none;
            font-size: 12px;
        }
        .sm-cta-btn:hover { transform: scale(1.03); }

        @media (max-width: 640px) {
            #sm-chat-widget-container {
                right: 12px;
                left: 12px;
                bottom: 12px;
            }

            #sm-chat-window {
                right: 0;
                left: 0;
                width: auto;
                height: min(70vh, 560px);
                max-width: none;
            }

            #sm-chat-button {
                margin-left: auto;
            }
        }
    `;
    document.head.appendChild(style);

    // HTML del Widget + Modal
    const container = document.createElement("div");
    container.id = "sm-chat-widget-container";
    container.innerHTML = `
        <button id="sm-chat-button">💬</button>
        <div id="sm-chat-window">
            <div id="sm-chat-header">
                <span>${initialBotName}</span>
                <span id="sm-chat-header-close">&times;</span>
            </div>
            <div id="sm-chat-messages">
                <div class="sm-chat-msg bot">¡Hola! Soy ${initialBotName}. Estoy aquí para ayudarte con información oficial de SixManager. ¿En qué te puedo ayudar hoy?</div>
            </div>
            <div id="sm-chat-input-container">
                <input type="text" id="sm-chat-input" placeholder="Pregunta algo aquí..." autocomplete="off" />
                <button id="sm-chat-submit">➤</button>
            </div>
            <div id="sm-chat-footer">
                Al interactuar, aceptas el tratamiento de datos según la Ley 19.628 (Chile).
            </div>
        </div>

        <!-- Modal de Leads -->
        <div id="sm-lead-modal-overlay">
            <div id="sm-lead-modal">
                <span id="sm-modal-close">&times;</span>
                <h3>✨ Atención Personalizada</h3>
                <p>He notado tu interés en nuestros servicios. Deja tus datos para que un consultor experto de SixManager se contacte contigo a la brevedad.</p>
                <form id="sm-lead-form">
                    <div class="sm-form-group">
                        <label>Nombre Completo*</label>
                        <input type="text" id="sm-lead-name" required placeholder="Ej: Juan Pérez" />
                    </div>
                    <div class="sm-form-group">
                        <label>Email Corporativo*</label>
                        <input type="email" id="sm-lead-email" required placeholder="juan@empresa.com" />
                    </div>
                    <div class="sm-form-group">
                        <label>Teléfono de Contacto*</label>
                        <input type="tel" id="sm-lead-phone" required placeholder="+569 1234 5678" />
                    </div>
                    <div class="sm-form-group">
                        <label>Empresa*</label>
                        <input type="text" id="sm-lead-company" required placeholder="Nombre de tu organización" />
                    </div>
                    <div class="sm-form-group">
                        <label>Cargo / Posición*</label>
                        <input type="text" id="sm-lead-cargo" required placeholder="Ej: Gerente de TI" />
                    </div>
                    <div class="sm-form-legal">
                        <input type="checkbox" id="sm-lead-legal" required />
                        <label for="sm-lead-legal">Acepto el tratamiento de mis datos personales según la Ley 19.628 de Chile para fines de contacto comercial.</label>
                    </div>
                    <div class="sm-form-captcha">
                        <span class="sm-captcha-question" id="sm-captcha-text"></span>
                        <input type="text" id="sm-lead-captcha" required placeholder="?" />
                    </div>
                    <button type="submit" id="sm-lead-submit">Enviar Solicitud</button>
                </form>
                <div id="sm-lead-success" style="display:none; text-align:center; padding: 40px 10px;">
                    <div style="font-size: 50px; margin-bottom: 20px;">✅</div>
                    <h2 style="color: var(--sm-primary); margin:0;">¡Enviado!</h2>
                    <p style="font-size: 14px; color: #666;">Tus datos se registraron con éxito. Pronto nos contactaremos contigo.</p>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(container);

    // Elementos del DOM
    const chatBtn = document.getElementById("sm-chat-button");
    const chatWin = document.getElementById("sm-chat-window");
    const closeBtn = document.getElementById("sm-chat-header-close");
    const input = document.getElementById("sm-chat-input");
    const submit = document.getElementById("sm-chat-submit");
    const messages = document.getElementById("sm-chat-messages");
    const headerTitle = chatWin.querySelector("#sm-chat-header span");
    const welcomeBubble = messages.querySelector(".sm-chat-msg.bot");

    const modalOverlay = document.getElementById("sm-lead-modal-overlay");
    const modalClose = document.getElementById("sm-modal-close");
    const leadForm = document.getElementById("sm-lead-form");
    const captchaText = document.getElementById("sm-captcha-text");
    const captchaInput = document.getElementById("sm-lead-captcha");

    let captchaAnswer = 0;
    let smShowSources = true;
    let smUseStreaming = false;

    function generateCaptcha() {
        const a = Math.floor(Math.random() * 9) + 1;
        const b = Math.floor(Math.random() * 9) + 1;
        captchaAnswer = a + b;
        captchaText.textContent = `Seguridad: ¿Cuánto es ${a} + ${b}?`;
        captchaInput.value = "";
    }

    function showModal() {
        generateCaptcha();
        modalOverlay.style.display = "flex";
    }

    modalClose.onclick = () => modalOverlay.style.display = "none";
    
    leadForm.onsubmit = async (e) => {
        e.preventDefault();
        
        if (parseInt(captchaInput.value) !== captchaAnswer) {
            alert("Respuesta de seguridad incorrecta. Por favor intenta de nuevo.");
            generateCaptcha();
            return;
        }

        const submitBtn = document.getElementById("sm-lead-submit");
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando...";

        const formData = {
            session_id: sessionId,
            name: document.getElementById("sm-lead-name").value,
            email: document.getElementById("sm-lead-email").value,
            phone: document.getElementById("sm-lead-phone").value,
            company: document.getElementById("sm-lead-company").value,
            cargo: document.getElementById("sm-lead-cargo").value
        };

        try {
            const res = await fetch(`${apiBaseUrl}/submit-lead-form`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-API-KEY": apiKey
                },
                body: JSON.stringify(formData)
            });

            if (res.ok) {
                const modalInside = document.getElementById("sm-lead-modal");
                const successDiv = document.getElementById("sm-lead-success");
                const formEl = document.getElementById("sm-lead-form");
                const headerP = modalInside.querySelector("p"); // El párrafo descriptivo inicial
                
                formEl.style.display = "none";
                if(headerP) headerP.style.display = "none";
                successDiv.style.display = "block";
                
                setTimeout(() => {
                    modalOverlay.style.display = "none";
                    // Resetear para futuro uso
                    formEl.reset();
                    formEl.style.display = "block";
                    if(headerP) headerP.style.display = "block";
                    successDiv.style.display = "none";
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Enviar Solicitud";
                    addMessage("¡Gracias! Tus datos han sido registrados. Un consultor experto te contactará pronto.", "bot");
                }, 3000);
            } else {
                alert("Hubo un error al enviar tus datos. Por favor intenta nuevamente.");
                submitBtn.disabled = false;
                submitBtn.textContent = "Enviar Solicitud";
            }
        } catch (err) {
            console.error(err);
            alert("Error de conexión. Intenta más tarde.");
            submitBtn.disabled = false;
            submitBtn.textContent = "Enviar Solicitud";
        }
    };

    // Cargar configuración inicial (Nombre del bot)
    fetch(`${apiBaseUrl}/widget-config`, {
        headers: { "X-API-KEY": apiKey }
    })
        .then(res => res.json())
        .then(data => {
            if(data.bot_name) {
                headerTitle.textContent = data.bot_name;
                welcomeBubble.textContent = `¡Hola! Soy ${data.bot_name}, el asistente inteligente experto en SixManager. Estoy aquí para aclarar tus dudas sobre nuestros servicios, metodologías y marcas representadas. ¿En qué te puedo asesorar el día de hoy?`;
            }
            if(data.primary_color) {
                container.style.setProperty('--sm-primary', data.primary_color);
            }
            if(data.hasOwnProperty('show_sources')) {
                smShowSources = data.show_sources;
            }
            if(data.hasOwnProperty('use_streaming')) {
                smUseStreaming = data.use_streaming;
            }
        })
        .catch(e => console.error("No se pudo cargar config del widget", e));

    function toggleChat() {
        chatWin.classList.toggle("sm-open");
        if (chatWin.classList.contains("sm-open")) {
            input.focus();
        }
    }

    chatBtn.addEventListener("click", toggleChat);
    closeBtn.addEventListener("click", toggleChat);

    function addMessage(text, sender, isSources = false, messageId = null) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("sm-chat-msg");
        msgDiv.classList.add(sender);
        if (isSources) msgDiv.classList.add("sources");
        
        if (window.marked && sender === 'bot' && !isSources) {
            try {
                msgDiv.innerHTML = window.marked.parse(text);
            } catch(e) {
                msgDiv.innerHTML = text.replace(/\n/g, '<br>');
            }
        } else {
            msgDiv.innerHTML = text.replace(/\n/g, '<br>');
        }
        messages.appendChild(msgDiv);

        // Añadir feedback pack solo para mensajes del bot que no sean fuentes
        if (sender === "bot" && !isSources && messageId) {
            const feedbackDiv = document.createElement("div");
            feedbackDiv.classList.add("sm-feedback-container");
            feedbackDiv.innerHTML = `
                <button class="sm-feedback-btn" data-type="like" title="Útil">👍</button>
                <button class="sm-feedback-btn" data-type="dislike" title="No útil">👎</button>
            `;
            
            const btns = feedbackDiv.querySelectorAll(".sm-feedback-btn");
            btns.forEach(btn => {
                btn.addEventListener("click", () => handleFeedback(messageId, btn.dataset.type, btns));
            });
            
            messages.appendChild(feedbackDiv);
        }

        messages.scrollTop = messages.scrollHeight;
    }

    async function handleFeedback(messageId, rating, buttons) {
        // Deshabilitar botones inmediatamente para evitar spam
        buttons.forEach(b => {
            b.disabled = true;
            if (b.dataset.type === rating) b.classList.add("active");
            else b.style.opacity = "0.2";
        });

        try {
            await fetch(`${apiBaseUrl}/feedback`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-API-KEY": apiKey
                },
                body: JSON.stringify({ 
                    message_id: messageId,
                    rating: rating
                })
            });
        } catch (e) {
            console.error("Error al enviar feedback", e);
        }
    }

    function showTyping() {
        const id = "typing-" + Date.now();
        const typingDiv = document.createElement("div");
        typingDiv.id = id;
        typingDiv.classList.add("sm-typing-indicator");
        typingDiv.innerHTML = '<div class="sm-dot"></div><div class="sm-dot"></div><div class="sm-dot"></div>';
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    async function handleSend() {
        const text = input.value.trim();
        if (!text) return;

        input.value = "";
        addMessage(text, "user");
        
        const typingId = showTyping();

        try {
            const bodyData = { 
                message: text,
                session_id: sessionId,
                stream: smUseStreaming
            };

            const response = await fetch(`${apiBaseUrl}/chat`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-API-KEY": apiKey
                },
                body: JSON.stringify(bodyData)
            });

            if (!response.ok) {
                removeTyping(typingId);
                const dataError = await response.json().catch(()=>({}));
                addMessage("Hubo un error al conectar con el servidor: " + (dataError.detail || response.statusText), "bot");
                return;
            }

            if (smUseStreaming) {
                removeTyping(typingId);
                const msgDiv = document.createElement("div");
                msgDiv.classList.add("sm-chat-msg", "bot");
                messages.appendChild(msgDiv);
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let accSources = [];
                let accMsgId = null;
                let accShowModal = false;
                let fullBotText = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, {stream: true});
                    const lines = chunk.split('\n\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.substring(6);
                            if (!dataStr.trim()) continue;
                            try {
                                const payload = JSON.parse(dataStr);
                                if (payload.token) {
                                    fullBotText += payload.token;
                                    if (window.marked) {
                                        try {
                                            msgDiv.innerHTML = window.marked.parse(fullBotText);
                                        } catch(e) {
                                            msgDiv.innerHTML = fullBotText.replace(/\n/g, '<br>');
                                        }
                                    } else {
                                        msgDiv.innerHTML = fullBotText.replace(/\n/g, '<br>');
                                    }
                                    messages.scrollTop = messages.scrollHeight;
                                }
                                if (payload.sources) accSources = payload.sources;
                                if (payload.message_id) accMsgId = payload.message_id;
                                if (payload.show_modal) accShowModal = payload.show_modal;
                                if (payload.error) msgDiv.innerHTML += "<br><span style='color:red'>Error: " + payload.error + "</span>";
                            } catch(e) {}
                        }
                    }
                }

                if (accMsgId) {
                    const feedbackDiv = document.createElement("div");
                    feedbackDiv.classList.add("sm-feedback-container");
                    feedbackDiv.innerHTML = `
                        <button class="sm-feedback-btn" data-type="like" title="Útil">👍</button>
                        <button class="sm-feedback-btn" data-type="dislike" title="No útil">👎</button>
                    `;
                    const btns = feedbackDiv.querySelectorAll(".sm-feedback-btn");
                    btns.forEach(btn => btn.addEventListener("click", () => handleFeedback(accMsgId, btn.dataset.type, btns)));
                    msgDiv.after(feedbackDiv);
                }

                if (smShowSources && accSources.length > 0) {
                    const sourceText = "<i>Fuentes: " + accSources.map(s => s.replace('.pdf', '')).join(', ') + "</i>";
                    addMessage(sourceText, "bot", true);
                }

                if (accShowModal) {
                    setTimeout(() => {
                        const ctaDiv = document.createElement("div");
                        ctaDiv.classList.add("sm-cta-container");
                        ctaDiv.innerHTML = `
                            <div>¿Te gustaría obtener una atención más personalizada y un presupuesto a tu medida?</div>
                            <button class="sm-cta-btn">Solicitar Atención Personalizada ✨</button>
                        `;
                        ctaDiv.querySelector(".sm-cta-btn").onclick = () => showModal();
                        messages.appendChild(ctaDiv);
                        messages.scrollTop = messages.scrollHeight;
                    }, 1000);
                }

            } else {
                // FALLBACK MODO SINCRONO NORMAL
                const data = await response.json();
                removeTyping(typingId);

                addMessage(data.response, "bot", false, data.message_id);

                if (smShowSources && data.sources && data.sources.length > 0) {
                    const sourceText = "<i>Fuentes: " + data.sources.map(s => s.replace('.pdf', '')).join(', ') + "</i>";
                    addMessage(sourceText, "bot", true);
                }

                if (data.show_modal) {
                    setTimeout(() => {
                        const ctaDiv = document.createElement("div");
                        ctaDiv.classList.add("sm-cta-container");
                        ctaDiv.innerHTML = `
                            <div>¿Te gustaría obtener una atención más personalizada y un presupuesto a tu medida?</div>
                            <button class="sm-cta-btn">Solicitar Atención Personalizada ✨</button>
                        `;
                        ctaDiv.querySelector(".sm-cta-btn").onclick = () => showModal();
                        messages.appendChild(ctaDiv);
                        messages.scrollTop = messages.scrollHeight;
                    }, 1000);
                }
            }

        } catch (e) {
            removeTyping(typingId);
            addMessage("No me pude conectar al backend de inteligencia artificial.", "bot");
            console.error(e);
        }
    }

    submit.addEventListener("click", handleSend);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSend();
    });

})();
