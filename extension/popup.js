// Paper Agent Browser Extension - Popup Script
document.addEventListener('DOMContentLoaded', () => {
  const serverUrl = document.getElementById('serverUrl');
  const statusDiv = document.getElementById('status');
  const paperCard = document.getElementById('paperCard');
  const paperTitle = document.getElementById('paperTitle');
  const paperAuthors = document.getElementById('paperAuthors');
  const paperYear = document.getElementById('paperYear');
  const paperTags = document.getElementById('paperTags');
  const paperAbstract = document.getElementById('paperAbstract');
  const saveBtn = document.getElementById('saveBtn');
  const optionsBtn = document.getElementById('optionsBtn');
  const openLibrary = document.getElementById('openLibrary');

  // Load saved server URL
  chrome.storage.sync.get({ serverUrl: 'http://localhost:8000' }, (data) => {
    serverUrl.value = data.serverUrl;
  });

  serverUrl.addEventListener('change', () => {
    chrome.storage.sync.set({ serverUrl: serverUrl.value });
  });

  // Get detected paper from content script
  chrome.storage.local.get('detectedPaper', (data) => {
    const paper = data.detectedPaper;
    if (!paper) {
      showStatus('info', 'Navigate to a paper page on arXiv, PubMed, IEEE, Springer, etc.');
      paperCard.style.display = 'none';
      return;
    }
    const m = paper.metadata;
    paperTitle.textContent = m.title || paper.title || 'Unknown Paper';
    paperAuthors.textContent = m.authors?.length ? m.authors.join(', ') : 'Authors unknown';
    paperYear.textContent = m.year ? `(${m.year})` : '';
    paperAbstract.textContent = m.abstract ? m.abstract.slice(0, 200) + '...' : '';
    if (m.arxiv_id) paperTags.innerHTML = `<span class="tag">arXiv:${m.arxiv_id}</span>`;
    if (m.doi) paperTags.innerHTML += `<span class="tag">DOI: ${m.doi}</span>`;
    if (m.pmid) paperTags.innerHTML += `<span class="tag">PMID: ${m.pmid}</span>`;
    if (paper.site) paperTags.innerHTML += `<span class="tag">${paper.site}</span>`;
    paperCard.style.display = 'block';
    saveBtn.disabled = false;
  });

  saveBtn.addEventListener('click', async () => {
    const paper = (await chrome.storage.local.get('detectedPaper')).detectedPaper;
    if (!paper) return;

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span>Saving...';

    try {
      const url = `${serverUrl.value}/api/documents/upload`;
      const formData = new FormData();

      // Try to download PDF
      let pdfBlob = null;
      try {
        const pdfUrl = paper.metadata.arxiv_id
          ? `https://arxiv.org/pdf/${paper.metadata.arxiv_id}`
          : paper.metadata.pdf_url;
        if (pdfUrl) {
          const pdfResp = await fetch(pdfUrl);
          if (pdfResp.ok) pdfBlob = await pdfResp.blob();
        }
      } catch (e) { /* PDF download optional */ }

      if (pdfBlob) {
        const filename = `${paper.metadata.arxiv_id || paper.metadata.doi || 'paper'}.pdf`;
        formData.append('file', pdfBlob, filename);
      } else {
        // Create a placeholder
        const placeholder = new Blob(['No PDF available'], { type: 'text/plain' });
        formData.append('file', placeholder, 'paper.txt');
      }

      if (paper.metadata.title) formData.append('title', paper.metadata.title);
      if (paper.metadata.authors?.length) formData.append('authors', paper.metadata.authors.join(', '));
      if (paper.metadata.year) formData.append('year', paper.metadata.year.toString());
      if (paper.metadata.keywords?.length) formData.append('keywords', paper.metadata.keywords.join(', '));

      const token = (await chrome.storage.sync.get('token')).token;
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const resp = await fetch(url, { method: 'POST', headers, body: formData });
      const result = await resp.json();

      if (resp.ok) {
        showStatus('success', '✅ Paper saved to your library!');
        saveBtn.textContent = '✓ Saved';
        chrome.storage.local.remove('detectedPaper');
      } else {
        showStatus('error', `Save failed: ${result.detail || 'Unknown error'}`);
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save to Library';
      }
    } catch (e) {
      showStatus('error', `Connection error: ${e.message}. Check your server URL.`);
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save to Library';
    }
  });

  optionsBtn.addEventListener('click', () => chrome.runtime.openOptionsPage());
  openLibrary.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: serverUrl.value.replace(':8000', ':3000') || 'http://localhost:3000' });
  });

  function showStatus(type, msg) {
    statusDiv.innerHTML = `<div class="${type}">${msg}</div>`;
    setTimeout(() => { statusDiv.innerHTML = ''; }, 5000);
  }
});
