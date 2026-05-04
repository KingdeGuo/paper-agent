# Paper Agent Browser Extension

One-click import of academic papers into your Paper Agent library.

## Supported Sites

- arXiv.org (abs + PDF pages)
- PubMed
- IEEE Xplore
- Springer Link
- ACM Digital Library
- ScienceDirect
- bioRxiv / medRxiv
- OpenReview
- Google Scholar (partial)

## Installation

### Chrome / Edge / Brave

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` directory

### Firefox

1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on**
3. Select `manifest.json`

## Usage

1. Navigate to any supported paper page
2. Click the Paper Agent icon in your toolbar
3. Review the detected metadata
4. Click **Save to Library**
5. The paper appears in your Paper Agent documents

## Configuration

Click the extension's **Settings** button to configure:
- Server URL (your Paper Agent backend)
- Frontend URL
- API token (if authentication is enabled)
- Auto-import behavior
