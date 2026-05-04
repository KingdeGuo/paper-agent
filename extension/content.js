// Paper Agent Browser Extension - Content Script
// Detects paper metadata on academic publisher pages and sends to the extension popup.

(function () {
  const site = detectSite();
  if (!site) return;

  const metadata = extractMetadata(site);
  if (metadata && Object.keys(metadata).length > 0) {
    chrome.storage.local.set({ detectedPaper: { site, metadata, url: window.location.href, title: document.title } });
    showBadge();
  }

  function detectSite() {
    const host = window.location.hostname;
    if (host.includes('arxiv.org')) return 'arxiv';
    if (host.includes('scholar.google.com')) return 'google_scholar';
    if (host.includes('pubmed.ncbi.nlm.nih.gov')) return 'pubmed';
    if (host.includes('ieeexplore.ieee.org')) return 'ieee';
    if (host.includes('link.springer.com')) return 'springer';
    if (host.includes('dl.acm.org')) return 'acm';
    if (host.includes('sciencedirect.com')) return 'sciencedirect';
    if (host.includes('biorxiv.org') || host.includes('medrxiv.org')) return 'biorxiv';
    if (host.includes('openreview.net')) return 'openreview';
    return null;
  }

  function extractMetadata(site) {
    const meta = { title: '', authors: [], year: null, abstract: '', doi: '', url: window.location.href };

    // Try generic meta tags first
    meta.title = getMeta('citation_title') || getMeta('og:title') || getMeta('twitter:title') || document.title;

    const authorMeta = document.querySelectorAll('meta[name="citation_author"]');
    if (authorMeta.length) meta.authors = Array.from(authorMeta).map(m => m.content);

    const yearMeta = getMeta('citation_date') || getMeta('citation_publication_date');
    if (yearMeta) meta.year = yearMeta.match(/\d{4}/)?.[0] || null;

    meta.abstract = getMeta('citation_abstract') || getMeta('og:description') || getMeta('description');
    meta.doi = getMeta('citation_doi') || getMeta('DOI');

    // Site-specific extraction
    switch (site) {
      case 'arxiv': {
        const aid = window.location.pathname.match(/\/abs\/(\d+\.\d+)/)?.[1];
        if (aid) meta.arxiv_id = aid;
        const authorsEl = document.querySelector('.authors');
        if (authorsEl) meta.authors = authorsEl.textContent.replace('Authors:', '').trim().split(', ').map(a => a.trim());
        const abstractEl = document.querySelector('blockquote.abstract');
        if (abstractEl) meta.abstract = abstractEl.textContent.replace('Abstract:', '').trim();
        break;
      }
      case 'pubmed': {
        const pmid = window.location.pathname.match(/(\d+)/)?.[1];
        if (pmid) meta.pmid = pmid;
        break;
      }
      case 'ieee': {
        const doi = getMeta('citation_doi') || document.querySelector('.doi a')?.textContent?.trim();
        if (doi) meta.doi = doi;
        break;
      }
    }

    return meta;
  }

  function getMeta(name) {
    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return el?.content || null;
  }

  function showBadge() {
    // Visual indicator on the page that paper was detected
    const badge = document.createElement('div');
    badge.id = 'paper-agent-detected';
    badge.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;background:#2563eb;color:white;padding:8px 16px;border-radius:20px;font-size:13px;font-family:sans-serif;box-shadow:0 2px 8px rgba(0,0,0,0.2);cursor:pointer;display:none;';
    badge.textContent = '📚 Save to Paper Agent';
    badge.onclick = () => chrome.runtime.sendMessage({ action: 'openPopup' });
    document.body.appendChild(badge);

    setTimeout(() => { badge.style.display = 'block'; }, 500);
    setTimeout(() => { badge.style.display = 'none'; }, 8000);
  }
})();
