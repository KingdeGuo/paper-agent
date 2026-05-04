import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Tabs, Tab, TextField, Button, Chip, CircularProgress, Grid, Card, CardContent, Stack, Divider, IconButton, Tooltip, Snackbar, Alert } from '@mui/material';
import { ContentCopy as CopyIcon, PlayArrow as RunIcon, Code as CodeIcon, Description as DocIcon, AutoAwesome as AIIcon } from '@mui/icons-material';
import api from '../services/api';

const API_GROUPS = [
  { id: 'documents', label: '📄 Documents', endpoints: [
    { method: 'POST', path: '/documents/upload', desc: 'Upload PDF', body: 'multipart/form-data' },
    { method: 'GET', path: '/documents', desc: 'List documents', params: '?skip=0&limit=100' },
    { method: 'GET', path: '/documents/:id', desc: 'Get document' },
    { method: 'DELETE', path: '/documents/:id', desc: 'Delete document' },
    { method: 'GET', path: '/documents/:id/download', desc: 'Download PDF' },
  ]},
  { id: 'search', label: '🔍 Search', endpoints: [
    { method: 'GET', path: '/search/simple', desc: 'Simple search', params: '?q=transformer' },
    { method: 'POST', path: '/search/', desc: 'Semantic search', body: '{"query":"..."}' },
    { method: 'GET', path: '/search/trending', desc: 'Trending papers' },
    { method: 'GET', path: '/search-unified', desc: 'Unified search', params: '?q=transformer&sources=papers,discussions,codex,glossary,tags' },
    { method: 'GET', path: '/multi-search', desc: 'Multi-source search', params: '?q=attention&sources=arxiv,pubmed,crossref,local' },
  ]},
  { id: 'citations', label: '🔗 Citations', endpoints: [
    { method: 'GET', path: '/citations/export/:id', desc: 'Export BibTeX' },
    { method: 'POST', path: '/citations/export-batch', desc: 'Batch export', body: '["id1","id2"]' },
    { method: 'POST', path: '/citations/import-bibtex', desc: 'Import BibTeX', body: '"@article{...}"' },
    { method: 'GET', path: '/citations/search', desc: 'Search publications', params: '?q=transformer' },
    { method: 'GET', path: '/citations/lookup-doi', desc: 'DOI lookup', params: '?doi=10.1038/...' },
  ]},
  { id: 'reading', label: '📖 Reading', endpoints: [
    { method: 'GET', path: '/reading', desc: 'Get reading list', params: '?status=to_read' },
    { method: 'PUT', path: '/reading/:id/status', desc: 'Set reading status', body: '"reading"' },
    { method: 'PUT', path: '/reading/:id/progress', desc: 'Update progress', params: '?progress=0.5' },
    { method: 'GET', path: '/reading/stats', desc: 'Reading statistics' },
  ]},
  { id: 'ask', label: '🤖 Ask AI', endpoints: [
    { method: 'POST', path: '/ask/', desc: 'Ask about library', body: '{"question":"...","limit":8}' },
    { method: 'GET', path: '/assistant/agenda', desc: 'Daily research agenda' },
    { method: 'GET', path: '/assistant/weekly-briefing', desc: 'Weekly briefing' },
    { method: 'GET', path: '/assistant/research-directions', desc: 'Research directions' },
  ]},
  { id: 'chat', label: '💬 Chat', endpoints: [
    { method: 'POST', path: '/chat/sessions', desc: 'Create session' },
    { method: 'GET', path: '/chat/sessions', desc: 'List sessions' },
    { method: 'POST', path: '/chat/sessions/:id/ask', desc: 'Ask in session', params: '?question=...' },
    { method: 'GET', path: '/chat/sessions/:id/messages', desc: 'Get chat history' },
  ]},
  { id: 'flashcards', label: '🧠 Flashcards', endpoints: [
    { method: 'GET', path: '/flashcards/due', desc: 'Due flashcards' },
    { method: 'POST', path: '/flashcards/generate/:id', desc: 'Generate flashcards', params: '?count=5' },
    { method: 'POST', path: '/flashcards/:id/review', desc: 'Review flashcard', params: '?quality=3' },
    { method: 'GET', path: '/flashcards/stats', desc: 'Flashcard statistics' },
  ]},
  { id: 'analytics', label: '📊 Analytics', endpoints: [
    { method: 'GET', path: '/reading-analytics', desc: 'Reading analytics', params: '?days=90' },
    { method: 'GET', path: '/stats/full', desc: 'Full system stats' },
    { method: 'GET', path: '/system-health', desc: 'System health' },
    { method: 'GET', path: '/data-quality/report', desc: 'Data quality report' },
  ]},
  { id: 'impact', label: '📈 Impact', endpoints: [
    { method: 'GET', path: '/impact/:id', desc: 'Paper impact metrics' },
    { method: 'GET', path: '/impact/overview', desc: 'Library impact overview' },
  ]},
  { id: 'workspace', label: '👥 Workspace', endpoints: [
    { method: 'POST', path: '/workspaces', desc: 'Create workspace' },
    { method: 'GET', path: '/workspaces', desc: 'List workspaces' },
    { method: 'POST', path: '/workspaces/:id/invite', desc: 'Invite member' },
    { method: 'GET', path: '/workspaces/:id/digest', desc: 'Team digest' },
  ]},
  { id: 'conferences', label: '🎯 Conferences', endpoints: [
    { method: 'GET', path: '/conferences/venues', desc: 'List venues' },
    { method: 'POST', path: '/conferences/track', desc: 'Track conference' },
    { method: 'GET', path: '/conferences/tracked', desc: 'Tracked conferences' },
  ]},
];

const ApiDocs = () => {
  const [groupIdx, setGroupIdx] = useState(0);
  const [endpointIdx, setEndpointIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notify, setNotify] = useState({ open: false, msg: '' });
  const [methodFilter, setMethodFilter] = useState('all');

  const group = API_GROUPS[groupIdx];
  const ep = group?.endpoints[endpointIdx];

  const handleTryIt = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      let path = ep.path.replace(/:id/g, '12345678-1234-1234-1234-123456789012');
      if (ep.params) path += ep.params;
      let res;
      if (ep.method === 'GET') {
        res = await api.get(path);
      } else if (ep.method === 'POST') {
        res = await api.post(path, ep.body ? JSON.parse(ep.body.replace(/'/g, '"')) : {});
      } else if (ep.method === 'PUT') {
        res = await api.put(path, ep.body ? JSON.parse(ep.body.replace(/'/g, '"')) : {});
      } else if (ep.method === 'DELETE') {
        res = await api.delete(path);
      }
      setResult(res.data);
    } catch (e) {
      setError(e.message);
      setResult(e.response?.data);
    }
    finally { setLoading(false); }
  };

  const copyToClipboard = async (text) => {
    await navigator.clipboard.writeText(text);
    setNotify({ open: true, msg: 'Copied!' });
  };

  const buildCurl = () => {
    const path = ep.path.replace(/:id/g, '{id}');
    let curl = `curl -X ${ep.method} http://localhost:8000/api${path}`;
    if (ep.params) curl += ep.params;
    curl += " \\\n  -H 'Authorization: Bearer <token>'";
    if (ep.body) {
      curl += " \\\n  -H 'Content-Type: application/json'";
      curl += ` \\\n  -d '${ep.body}'`;
    }
    return curl;
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 140px)' }}>
      {/* Sidebar */}
      <Paper sx={{ width: 220, p: 1.5, overflow: 'auto', flexShrink: 0 }}>
        {API_GROUPS.map((g, i) => (
          <Box key={i}>
            <Button fullWidth variant={groupIdx === i ? 'contained' : 'text'} size="small"
              onClick={() => { setGroupIdx(i); setEndpointIdx(0); setResult(null); }}
              sx={{ justifyContent: 'flex-start', textTransform: 'none', mb: 0.3 }}>
              {g.label}
            </Button>
            {groupIdx === i && (
              <Stack spacing={0.2} sx={{ ml: 2, mb: 1 }}>
                {g.endpoints.map((ep, j) => (
                  <Button key={j} fullWidth size="small" variant="text"
                    onClick={() => { setEndpointIdx(j); setResult(null); }}
                    sx={{ justifyContent: 'flex-start', textTransform: 'none', fontSize: 12,
                      bgcolor: endpointIdx === j ? 'action.selected' : 'transparent' }}>
                    <Chip label={ep.method} size="small" color={ep.method === 'GET' ? 'success' : ep.method === 'POST' ? 'primary' : ep.method === 'PUT' ? 'warning' : 'error'}
                      variant="outlined" sx={{ mr: 0.5, height: 18, fontSize: 10 }} />
                    {ep.desc}
                  </Button>
                ))}
              </Stack>
            )}
          </Box>
        ))}
      </Paper>

      {/* Main */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {ep && (
          <>
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent sx={{ py: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label={ep.method} color={ep.method === 'GET' ? 'success' : ep.method === 'POST' ? 'primary' : ep.method === 'PUT' ? 'warning' : 'error'} size="small" />
                    <Typography variant="h6" sx={{ fontWeight: 'bold', fontFamily: 'monospace' }}>{ep.path}</Typography>
                    <Chip label={ep.desc} size="small" variant="outlined" />
                  </Box>
                  <Box>
                    <Tooltip title="Copy curl"><IconButton size="small" onClick={() => copyToClipboard(buildCurl())}><CopyIcon /></IconButton></Tooltip>
                    <Tooltip title="Try it"><IconButton size="small" onClick={handleTryIt}><RunIcon /></IconButton></Tooltip>
                  </Box>
                </Box>
                {ep.params && <Typography variant="caption" color="text.secondary">Params: {ep.params}</Typography>}
              </CardContent>
            </Card>

            {/* Code Example */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2, position: 'relative' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><CodeIcon fontSize="small" /> curl Example</Typography>
                <IconButton size="small" onClick={() => copyToClipboard(buildCurl())}><CopyIcon fontSize="small" /></IconButton>
              </Box>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: 12, whiteSpace: 'pre-wrap', bgcolor: 'grey.900', color: 'greenyellow', p: 2, borderRadius: 1 }}>
                {buildCurl()}
              </Typography>
            </Paper>

            {/* Try It Result */}
            {(loading || result || error) && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Response</Typography>
                {loading ? <CircularProgress size={20} /> : (
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: 12, whiteSpace: 'pre-wrap', bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
                    {error ? `Error: ${error}` : JSON.stringify(result, null, 2)}
                  </Typography>
                )}
              </Paper>
            )}
          </>
        )}

        {/* Overview */}
        {!ep && (
          <Box textAlign="center" py={10} sx={{ opacity: 0.6 }}>
            <DocIcon sx={{ fontSize: 80, mb: 2, color: 'primary.light' }} />
            <Typography variant="h5" gutterBottom>Interactive API Documentation</Typography>
            <Typography variant="body2" color="text.secondary">
              Select an API group and endpoint to explore. Each endpoint includes a curl example and a "Try It" button.
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              57 routes · Full CRUD · Streaming support
            </Typography>
          </Box>
        )}
      </Box>

      <Snackbar open={notify.open} autoHideDuration={2000} onClose={() => setNotify({ open: false })} message={notify.msg} />
    </Box>
  );
};

export default ApiDocs;
