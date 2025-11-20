// background.js (Manifest V3 service worker)
const BACKEND_URL = "http://localhost:5000/activity";
const RETRY_INTERVAL_MS = 60 * 1000; // reintentar cola cada minuto
const CHECK_INTERVAL_MS = 5000; // Verificar cada 5 segundos
const MAX_QUEUE_SIZE = 50; // Límite máximo de eventos en cola
const MAX_EVENT_AGE_MS = 24 * 60 * 60 * 1000; // 24 horas máximo

// Estado global para tracking
let currentPage = null;
let pageStartTime = null;
let pageInterval = null;
let checkInterval = null;
let isBrowserActive = true; // Estado de actividad del navegador
let activityCheckInterval = null;

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

// Validar si la URL es válida para tracking
function isValidURL(url) {
  try {
    const u = new URL(url);
    // Excluir páginas internas del navegador
    return !u.protocol.startsWith('chrome') && 
           !u.protocol.startsWith('edge') && 
           !u.protocol.startsWith('about') &&
           !u.protocol.startsWith('moz-extension') &&
           !u.protocol.startsWith('opera') &&
           u.protocol.startsWith('http'); // Solo URLs web
  } catch {
    return false;
  }
}

// Función para enviar página con duración calculada
async function sendPageWithDuration() {
    if (!currentPage || !pageStartTime) return;
    
    const endTime = new Date();
    const duration = Math.round((endTime - pageStartTime) / 1000); // segundos
    
    // Solo enviar si la duración es mayor a 0 segundos
    if (duration <= 0) return;
    
    const payload = {
        domain: currentPage.domain,
        url: currentPage.url,
        title: currentPage.title,
        startTime: pageStartTime.toISOString(),
        endTime: endTime.toISOString(),
        duration: duration,
        browser: detectBrowser(currentPage.url)
    };
    
    console.log(`Enviando página: ${currentPage.domain} - ${duration}s`);
    const success = await sendEvent(payload);
    
    if (success) {
        console.log(`Página enviada: ${currentPage.domain} - ${duration}s`);
    } else {
        console.log(`Falló envío de: ${currentPage.domain}`);
    }
    
    return success;
}

// Detectar navegador desde la URL
function detectBrowser(url) {
    if (url.includes('chrome://') || url.includes('chrome-extension://')) return 'chrome.exe';
    if (url.includes('edge://') || url.includes('extension://')) return 'msedge.exe';
    if (url.includes('opera://')) return 'opera.exe';
    if (url.includes('firefox://')) return 'firefox.exe';
    return 'browser.exe';
}

// Sistema SIMPLIFICADO de detección de actividad - solo verifica ventanas con foco
async function checkBrowserActivity() {
    try {
        const windows = await chrome.windows.getAll({ windowTypes: ['normal', 'popup'] });
        const hasFocusedWindow = windows.some(window => window.focused);
        
        if (hasFocusedWindow && !isBrowserActive) {
            // Navegador acaba de ganar foco
            console.log("NAVEGADOR ACTIVO - Reactivando tracking");
            isBrowserActive = true;
            
            // Verificar página actual inmediatamente
            setTimeout(checkActivePage, 500);
            
        } else if (!hasFocusedWindow && isBrowserActive) {
            // Navegador acaba de perder foco
            console.log("NAVEGADOR EN SEGUNDO PLANO - Pausando tracking");
            isBrowserActive = false;
            
            // Enviar página actual antes de pausar
            if (currentPage) {
                console.log(" Enviando última página antes de pausar...");
                const success = await sendPageWithDuration();
                if (success) {
                    currentPage = null;
                    pageStartTime = null;
                }
            }
            
            // Limpiar intervalo de página
            if (pageInterval) {
                clearInterval(pageInterval);
                pageInterval = null;
            }
        }
        
        // Log del estado actual (solo si cambió)
        logActivityStatus();
        
    } catch (error) {
        console.error("Error verificando actividad:", error);
    }
}

// Log del estado de actividad
function logActivityStatus() {
    console.log(`Estado: ${isBrowserActive ? 'ACTIVO' : 'SEGUNDO PLANO'} | Página: ${currentPage?.domain || 'Ninguna'}`);
}

// Iniciar tracking de una nueva página
async function startTrackingPage(tab) {
    // Si el navegador no está activo, no hacer tracking
    if (!isBrowserActive) {
        console.log(" Ignorando - Navegador en segundo plano");
        return;
    }
    
    // Validar URL
    if (!tab || !isValidURL(tab.url)) {
        console.log(`Ignorando - URL no válida: ${tab?.url}`);
        return;
    }
    
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
    console.log(`Nueva página: ${currentPage.domain}`);

    // Reiniciar intervalo de 1 minuto
    if (pageInterval) clearInterval(pageInterval);
    pageInterval = setInterval(async () => {
        if (currentPage && isBrowserActive) {
            await sendPageWithDuration();
            // Reiniciar contador para el próximo minuto
            pageStartTime = new Date();
            console.log(`Minuto completado: ${currentPage.domain}`);
        }
    }, 60000);
}

// Verificar periódicamente si cambió la página activa
async function checkActivePage() {
    if (!isBrowserActive) {
        return;
    }
    
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url && isValidURL(tab.url)) {
            await startTrackingPage(tab);
        } else if (currentPage) {
            // Si no hay pestaña activa válida pero hay una página en tracking, detenerla
            console.log("No hay pestaña activa válida - deteniendo tracking");
            await sendPageWithDuration();
            currentPage = null;
            pageStartTime = null;
        }
    } catch (err) {
        console.error("Error checking active page:", err);
    }
}

// Función para encolar eventos con límite de tamaño
async function enqueueEvent(event) {
    try {
        const data = await chrome.storage.local.get({queue: []});
        let queue = data.queue || [];
        
        // Limpiar eventos muy viejos primero
        const now = Date.now();
        queue = queue.filter(ev => {
            const eventTime = new Date(ev.endTime || ev.startTime).getTime();
            return (now - eventTime) < MAX_EVENT_AGE_MS;
        });
        
        // Si aún excede el límite después de limpiar, remover los más viejos
        if (queue.length >= MAX_QUEUE_SIZE) {
            console.warn(`Cola llena (${queue.length}), removiendo eventos más antiguos`);
            queue = queue.slice(-Math.floor(MAX_QUEUE_SIZE * 0.8));
        }
        
        queue.push(event);
        await chrome.storage.local.set({queue: queue});
        console.log(`Evento encolado. Tamaño cola: ${queue.length}`);
        
    } catch (error) {
        console.error("Error encolando evento:", error);
    }
}

// Función para enviar evento al backend
async function sendEvent(event) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        console.log(`Enviando evento: ${event.domain} - ${event.duration}s`);
        
        const resp = await fetch(BACKEND_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(event),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
        }
        
        console.log("Evento enviado exitosamente");
        return true;
    } catch (err) {
        console.warn("Error enviando evento:", err.message);
        
        // Solo encolar si es un error de red/tiempo fuera
        if (err.name === 'TypeError' || err.name === 'AbortError') {
            await enqueueEvent(event);
            console.log("Evento guardado en cola para reintento");
        }
        return false;
    }
}

// Función para vaciar la cola de eventos pendientes
async function flushQueue() {
    if (!isBrowserActive) {
        console.log("Navegador en segundo plano - no se vacía cola");
        return;
    }
    
    const data = await chrome.storage.local.get({queue: []});
    let queue = data.queue || [];
    
    if (!queue.length) return;
    
    console.log(`Intentando enviar ${queue.length} eventos de la cola...`);
    
    const remaining = [];
    let successCount = 0;
    
    for (const ev of queue) {
        try {
            // Verificar si el evento es muy viejo antes de enviar
            const eventTime = new Date(ev.endTime || ev.startTime).getTime();
            const eventAge = Date.now() - eventTime;
            
            if (eventAge > MAX_EVENT_AGE_MS) {
                console.log(`Descartando evento viejo (${Math.round(eventAge/1000/60)} minutos)`);
                continue;
            }
            
            const ok = await sendEvent(ev);
            if (ok) {
                successCount++;
            } else {
                remaining.push(ev);
            }
        } catch (e) {
            console.error("Error enviando evento de cola:", e);
            remaining.push(ev);
        }
        
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    await chrome.storage.local.set({queue: remaining});
    console.log(`Cola procesada: ${successCount} exitosos, ${remaining.length} pendientes`);
}

// ========== LISTENERS SIMPLIFICADOS ==========

// Listeners para cambios de pestaña - SOLO si el navegador está activo
chrome.tabs.onActivated.addListener((activeInfo) => {
    if (!isBrowserActive) return;
    
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab && isValidURL(tab.url)) {
            startTrackingPage(tab);
        }
    });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (!isBrowserActive) return;
    
    if ((changeInfo.status === 'complete' || changeInfo.url) && isValidURL(tab.url)) {
        startTrackingPage(tab);
    }
});

// Listener SIMPLE para cambios de foco - solo marca el cambio principal
chrome.windows.onFocusChanged.addListener((windowId) => {
    // Pequeño delay para que el sistema actualice el estado de las ventanas
    setTimeout(checkBrowserActivity, 100);
});

// ========== INICIALIZACIÓN ==========

async function initializeExtension() {
    console.log("Iniciando extensión...");
    
    // Inicializar storage
    await chrome.storage.local.set({queue: []});
    
    // Verificar estado inicial
    await checkBrowserActivity();
    
    // Iniciar verificaciones periódicas
    checkInterval = setInterval(checkActivePage, CHECK_INTERVAL_MS);
    setInterval(flushQueue, RETRY_INTERVAL_MS);
    
    // Verificar actividad cada 2 segundos - MÁS FRECUENTE para mejor respuesta
    activityCheckInterval = setInterval(checkBrowserActivity, 2000);
    
    console.log("Extensión inicializada correctamente");
    logActivityStatus();
}

// Listeners de ciclo de vida
chrome.runtime.onStartup.addListener(() => {
    console.log("Runtime startup");
    initializeExtension();
});

chrome.runtime.onInstalled.addListener(() => {
    console.log("Extensión instalada/actualizada");
    initializeExtension();
});

// Limpiar recursos
chrome.runtime.onSuspend.addListener(() => {
    console.log("Suspension - limpiando recursos");
    if (pageInterval) clearInterval(pageInterval);
    if (checkInterval) clearInterval(checkInterval);
    if (activityCheckInterval) clearInterval(activityCheckInterval);
    
    if (currentPage && isBrowserActive) {
        sendPageWithDuration().catch(console.error);
    }
});

// Manejo de mensajes
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "flushQueue") {
        flushQueue()
            .then(() => sendResponse({ ok: true, message: "Cola enviada" }))
            .catch(() => sendResponse({ ok: false, message: "Error" }));
        return true;
    }
    
    if (message.action === "getStatus") {
        sendResponse({
            isBrowserActive: isBrowserActive,
            currentPage: currentPage?.domain,
            pageStartTime: pageStartTime
        });
        return true;
    }
    
    if (message.action === "forceActivityCheck") {
        checkBrowserActivity()
            .then(() => sendResponse({ 
                ok: true, 
                currentStatus: isBrowserActive,
                currentPage: currentPage?.domain 
            }));
        return true;
    }
});