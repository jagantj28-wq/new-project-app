// FarmTwin AI Agronomist Copilot Controller

function openAdvisorDrawer() {
    const drawer = document.getElementById('advisor-drawer');
    if (drawer) {
        drawer.classList.remove('translate-x-full');
    }
}

function closeAdvisorDrawer() {
    const drawer = document.getElementById('advisor-drawer');
    if (drawer) {
        drawer.classList.add('translate-x-full');
    }
}

function sendQuickPrompt(promptText) {
    const input = document.getElementById('advisor-input');
    if (input) {
        input.value = promptText;
        submitAdvisorMessage();
    }
}

async function submitAdvisorMessage() {
    const input = document.getElementById('advisor-input');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    appendMessage('user', msg);

    // Typing indicator
    const typingId = appendTypingIndicator();

    try {
        const currentZone = window.getCurrentZone ? window.getCurrentZone() : null;
        const currentSim = window.getCurrentSimulation ? window.getCurrentSimulation() : null;

        const payload = {
            message: msg,
            zone_id: currentZone ? currentZone.id : "zone-1",
            simulation_context: {
                zone_name: currentZone ? currentZone.name : "Active Block",
                crop: currentZone ? currentZone.crop : "tomato",
                soil: currentZone ? currentZone.soil : "loam",
                current_moisture: currentSim ? currentSim.summary.current_moisture_pct : 25.0
            }
        };

        const resp = await fetch('/api/advisor/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        removeTypingIndicator(typingId);

        if (resp.ok) {
            const data = await resp.json();
            appendMessage('assistant', data.reply, data.action_items, data.source);
        } else {
            appendMessage('assistant', '⚠️ Unable to connect to agronomist service. Please try again.');
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        appendMessage('assistant', '⚠️ Network error communicating with advisory engine.');
    }
}

function appendMessage(sender, text, actionItems = [], source = "") {
    const container = document.getElementById('advisor-messages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'user' ? 'flex justify-end mb-3' : 'flex justify-start mb-3';

    // Simple markdown formatting for bold and bullets
    let formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br/>');

    let actionsHtml = '';
    if (actionItems && actionItems.length > 0) {
        actionsHtml = `
            <div class="mt-2 pt-2 border-t border-emerald-500/20 text-xs">
                <div class="font-semibold text-emerald-400 mb-1">Recommended Directives:</div>
                <ul class="list-disc pl-4 space-y-0.5 text-slate-300">
                    ${actionItems.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    let badgeHtml = '';
    if (source) {
        badgeHtml = `<span class="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 mb-1 inline-block">${source.replace('_', ' ')}</span>`;
    }

    if (sender === 'user') {
        msgDiv.innerHTML = `
            <div class="max-w-[85%] bg-emerald-600/30 border border-emerald-500/40 text-emerald-100 rounded-2xl rounded-tr-sm px-4 py-2.5 text-xs">
                ${formattedText}
            </div>
        `;
    } else {
        msgDiv.innerHTML = `
            <div class="max-w-[88%] bg-slate-900/90 border border-slate-700/60 text-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 text-xs leading-relaxed shadow-lg">
                ${badgeHtml}
                <div>${formattedText}</div>
                ${actionsHtml}
            </div>
        `;
    }

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
    const container = document.getElementById('advisor-messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex justify-start mb-3';
    div.innerHTML = `
        <div class="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-400 flex items-center space-x-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse delay-100"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse delay-200"></span>
            <span class="text-[10px] pl-1 font-mono">Analyzing farm telemetry...</span>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
