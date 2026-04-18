(function() {
    const toggleBtn = document.getElementById('dj-chatbot-toggle');
    const chatWindow = document.getElementById('dj-chatbot-window');
    const closeBtn = document.getElementById('dj-chatbot-close');
    const form = document.getElementById('dj-chatbot-form');
    const input = document.getElementById('dj-chatbot-input');
    const submitBtn = form.querySelector('button[type="submit"]');
    const messages = document.getElementById('dj-chatbot-messages');
    const root = document.getElementById('dj-chatbot');
    const endpoint = root.dataset.endpoint;
    const historyEndpoint = root.dataset.history;
    const welcomeMessage = root.dataset.welcome;

    function addMessage(text, role) {
        const div = document.createElement('div');
        div.className = 'dj-chatbot__msg dj-chatbot__msg--' + role;
        div.textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    async function loadHistory() {
        try {
            const res = await fetch(historyEndpoint);
            if (!res.ok) return;
            const data = await res.json();
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => addMessage(msg.content, msg.role));
            } else if (welcomeMessage) {
                addMessage(welcomeMessage, 'assistant');
            }
        } catch {
            if (welcomeMessage) addMessage(welcomeMessage, 'assistant');
        }
        requestAnimationFrame(() => {
            messages.scrollTop = messages.scrollHeight;
        });
    }

    let historyLoaded = false;

    function isOpen() {
        return chatWindow.style.display === 'flex';
    }

    function openChat() {
        chatWindow.style.display = 'flex';
        toggleBtn.setAttribute('aria-expanded', 'true');
        input.focus();
        if (!historyLoaded) {
            historyLoaded = true;
            loadHistory();
        }
        requestAnimationFrame(() => {
            messages.scrollTop = messages.scrollHeight;
        });
    }

    function closeChat() {
        chatWindow.style.display = 'none';
        toggleBtn.setAttribute('aria-expanded', 'false');
        toggleBtn.focus();
    }

    function toggleChat() {
        if (isOpen()) closeChat(); else openChat();
    }

    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', closeChat);

    chatWindow.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            closeChat();
            return;
        }
        if (e.key !== 'Tab') return;
        const focusable = chatWindow.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        input.disabled = true;
        submitBtn.disabled = true;

        addMessage(text, 'user');
        input.value = '';

        const assistantDiv = addMessage('', 'assistant');
        assistantDiv.classList.add('dj-chatbot__msg--loading');
        assistantDiv.innerHTML = '<span class="dj-chatbot__dots"><span>.</span><span>.</span><span>.</span></span>';
        scrollToBottom();

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
            || document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

        const formData = new FormData();
        formData.append('message', text);

        function clearLoading() {
            assistantDiv.classList.remove('dj-chatbot__msg--loading');
            assistantDiv.textContent = '';
        }

        function scrollToBottom() {
            requestAnimationFrame(() => {
                messages.scrollTop = messages.scrollHeight;
            });
        }

        try {
            let res;
            try {
                res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData,
                });
            } catch {
                clearLoading();
                assistantDiv.textContent = 'Error: could not connect to the server.';
                scrollToBottom();
                return;
            }

            if (!res.ok) {
                clearLoading();
                assistantDiv.textContent = 'Error: could not get a response.';
                scrollToBottom();
                return;
            }

            const contentType = res.headers.get('content-type') || '';
            if (contentType.includes('text/event-stream')) {
                let first = true;
                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });

                    const lines = buffer.split('\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        const data = line.slice(6);
                        if (data === '[DONE]') break;
                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.error) {
                                clearLoading();
                                assistantDiv.textContent = 'Error: ' + parsed.error;
                                scrollToBottom();
                                return;
                            }
                            if (first) { clearLoading(); first = false; }
                            assistantDiv.textContent += parsed.token;
                            messages.scrollTop = messages.scrollHeight;
                        } catch {}
                    }
                }
            } else {
                clearLoading();
                const data = await res.json();
                assistantDiv.textContent = data.content;
                scrollToBottom();
            }
        } finally {
            input.disabled = false;
            submitBtn.disabled = false;
            input.focus();
        }
    });
})();
