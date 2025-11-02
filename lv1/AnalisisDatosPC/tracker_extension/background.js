// background.js (Manifest V3 service worker)
const BACKEND_URL = "http://localhost:5000/activity";
const RETRY_INTERVAL_MS = 60 * 1000; // reintentar cola cada minuto

// Helper: extraer hostname (dominio) desde una URL
function extractDomain(url) {
  try {
    const u = new URL(url);
    const host = u.hostname;
    // Forma simple de obtener "example.com" de "sub.example.com"
    const parts = host.split('.');
    if (parts.length >= 2) {
      return parts.slice(-2).join('.');
    }
    return host;
  } catch (e) {
    return null;
  }
}

// Guarda item en cola local (storage) si no se pudo enviar
async function enqueueEvent(event) {
  const items = (await chrome.storage.local.get({queue: []})).queue;
  items.push(event);
  await chrome.storage.local.set({queue: items});
}

// Intenta enviar un evento al backend
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

// Procesar cola almacenada y reenviar
async function flushQueue() {
  const data = await chrome.storage.local.get({queue: []});
  const queue = data.queue || [];
  if (!queue.length) return;
  const remaining = [];
  for (const ev of queue) {
    try {
      const ok = await sendEvent(ev); // sendEvent vuelve a encolar si falla
      if (!ok) remaining.push(ev);
    } catch (e) {
      remaining.push(ev);
    }
  }
  await chrome.storage.local.set({queue: remaining});
}

// Construir evento y enviarlo
async function handleTabInfo(tabId) {
  try {
    const tab = await chrome.tabs.get(tabId);
    if (!tab || !tab.url) return;

    const domain = extractDomain(tab.url) || "unknown";
    const payload = {
      domain: domain,
      url: tab.url,
      title: tab.title || "",
      timestamp: new Date().toISOString()
    };
    // enviar o encolar en caso de falla
    await sendEvent(payload);
  } catch (err) {
    console.error("handleTabInfo error", err);
  }
}

// Escucha cuando la pestaña activa cambia (cambio de foco entre pestañas)
chrome.tabs.onActivated.addListener((activeInfo) => {
  handleTabInfo(activeInfo.tabId);
});

// Escucha cuando una pestaña actualiza (navegación carga nueva url)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // changeInfo.url disponible cuando la URL cambia
  if (changeInfo.status === "complete" || changeInfo.url) {
    handleTabInfo(tabId);
  }
});

// Reintentar la cola periódicamente
setInterval(flushQueue, RETRY_INTERVAL_MS);

// Opcional: al instalar inicializa cola vacía
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({queue: []});
});
