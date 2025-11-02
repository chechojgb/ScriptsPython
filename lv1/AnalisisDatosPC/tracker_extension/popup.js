// popup.js
document.getElementById('flush-btn').addEventListener('click', async () => {
  await chrome.runtime.sendMessage({action: "flushQueue"});
  document.getElementById('status-text').innerText = "Estado: cola enviada (intento)";
});

// Listener para mensajes (si quieres exponer flush desde background)
chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  console.log("popup received message", msg);
});
