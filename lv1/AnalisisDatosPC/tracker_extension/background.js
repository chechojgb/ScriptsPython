// background.js (Manifest V3 service worker)
const BACKEND_URL = "http://localhost:5000/activity";
const RETRY_INTERVAL_MS = 60 * 1000; // reintentar cola cada minuto
const CHECK_INTERVAL_MS = 5000; // Verificar cada 5 segundos

// Estado global para tracking
let currentPage = null;
let pageStartTime = null;
let pageInterval = null;
let checkInterval = null;

// Helper: extraer hostname (dominio) desde una URL
function extractDomain(url) {
  try {
    const u = new URL(url);
    const host = u.hostname;
    const parts = host.split('.');
    if (parts.length >= 2) {
      return parts.slice(-2).join('.');
    }
    return host;
  } catch (e) {
    return null;
  }
}

// Función para enviar página con duración calculada
async function sendPageWithDuration() {
    if (!currentPage || !pageStartTime) return;
    
    const endTime = new Date();
    const duration = Math.round((endTime - pageStartTime) / 1000); // segundos
    
    const payload = {
        domain: currentPage.domain,
        url: currentPage.url,
        title: currentPage.title,
        startTime: pageStartTime.toISOString(),
        endTime: endTime.toISOString(),
        duration: duration,
        browser: detectBrowser(currentPage.url)
    };
    
    await sendEvent(payload);
    console.log(` Enviada página: ${currentPage.domain} - ${duration}s`);
}

// Detectar navegador desde la URL
function detectBrowser(url) {
    if (url.includes('chrome://') || url.includes('chrome-extension://')) return 'chrome.exe';
    if (url.includes('edge://') || url.includes('extension://')) return 'msedge.exe';
    if (url.includes('opera://')) return 'opera.exe';
    if (url.includes('firefox://')) return 'firefox.exe';
    return 'browser.exe';
}

// Iniciar tracking de una nueva página
async function startTrackingPage(tab) {
    const domain = extractDomain(tab.url) || "unknown";
    const newPage = {
        domain: domain,
        url: tab.url,
        title: tab.title || ""
    };

    // Si es la misma página, no hacer nada
    if (currentPage && 
        currentPage.domain === newPage.domain && 
        currentPage.url === newPage.url) {
        return;
    }

    // Si cambió la página, enviar la anterior con duración
    if (currentPage) {
        await sendPageWithDuration();
    }

    // Actualizar estado con nueva página
    currentPage = newPage;
    pageStartTime = new Date();
    console.log(` Nueva página: ${currentPage.domain}`);

    // Reiniciar intervalo de 1 minuto
    if (pageInterval) clearInterval(pageInterval);
    pageInterval = setInterval(async () => {
        if (currentPage) {
            await sendPageWithDuration();
            // Reiniciar contador para el próximo minuto
            pageStartTime = new Date();
            console.log(` Minuto completado: ${currentPage.domain}`);
        }
    }, 60000); // 1 minuto
}

// Verificar periódicamente si cambió la página activa
async function checkActivePage() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url) {
            await startTrackingPage(tab);
        }
    } catch (err) {
        console.error("Error checking active page:", err);
    }
}

// [MANTENER TODAS ESTAS FUNCIONES SIN CAMBIOS]
async function enqueueEvent(event) {
    const items = (await chrome.storage.local.get({queue: []})).queue;
    items.push(event);
    await chrome.storage.local.set({queue: items});
}

async function sendEvent(event) {
    try {
        const resp = await fetch(BACKEND_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(event),
            keepalive: true
        });
        if (!resp.ok) {
            throw new Error("Bad response " + resp.status);
        }
        return true;
    } catch (err) {
        console.warn("sendEvent failed:", err);
        await enqueueEvent(event);
        return false;
    }
}

async function flushQueue() {
    const data = await chrome.storage.local.get({queue: []});
    const queue = data.queue || [];
    if (!queue.length) return;
    const remaining = [];
    for (const ev of queue) {
        try {
            const ok = await sendEvent(ev);
            if (!ok) remaining.push(ev);
        } catch (e) {
            remaining.push(ev);
        }
    }
    await chrome.storage.local.set({queue: remaining});
}

// [MODIFICAR ESTOS LISTENERS]
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab) startTrackingPage(tab);
    });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" || changeInfo.url) {
        startTrackingPage(tab);
    }
});

// [AGREGAR ESTO] - Verificación cada 5 segundos
checkInterval = setInterval(checkActivePage, CHECK_INTERVAL_MS);

// [MANTENER ESTO SIN CAMBIOS]
setInterval(flushQueue, RETRY_INTERVAL_MS);

chrome.runtime.onInstalled.addListener(() => {
    chrome.storage.local.set({queue: []});
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "flushQueue") {
        flushQueue()
            .then(() => sendResponse({ ok: true, message: "Cola enviada correctamente" }))
            .catch(() => sendResponse({ ok: false, message: "Error al enviar cola" }));
        return true;
    }
});

// Limpiar intervalos al desinstalar
chrome.runtime.onSuspend.addListener(() => {
    if (pageInterval) clearInterval(pageInterval);
    if (checkInterval) clearInterval(checkInterval);
});