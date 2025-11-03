// popup.js
document.getElementById('flush-btn').addEventListener('click', async () => {
  try {
    const response = await chrome.runtime.sendMessage({ action: "flushQueue" });
    document.getElementById('status-text').innerText =
      "funciona" + response.message;
  } catch (error) {
    document.getElementById('status-text').innerText =
      "Error al conectar con background";
    console.error(error);
  }
});
