// Paper Agent Browser Extension - Options Page
document.addEventListener('DOMContentLoaded', () => {
  const serverUrl = document.getElementById('serverUrl');
  const frontendUrl = document.getElementById('frontendUrl');
  const token = document.getElementById('token');
  const autoImport = document.getElementById('autoImport');
  const saveBtn = document.getElementById('saveBtn');
  const saved = document.getElementById('saved');

  chrome.storage.sync.get({
    serverUrl: 'http://localhost:8000',
    frontendUrl: 'http://localhost:3000',
    token: '',
    autoImport: 'ask',
  }, (data) => {
    serverUrl.value = data.serverUrl;
    frontendUrl.value = data.frontendUrl;
    token.value = data.token;
    autoImport.value = data.autoImport;
  });

  saveBtn.addEventListener('click', () => {
    chrome.storage.sync.set({
      serverUrl: serverUrl.value,
      frontendUrl: frontendUrl.value,
      token: token.value,
      autoImport: autoImport.value,
    }, () => {
      saved.style.display = 'block';
      setTimeout(() => { saved.style.display = 'none'; }, 3000);
    });
  });
});
