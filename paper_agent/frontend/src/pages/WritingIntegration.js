import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Paper, Card, CardContent,
  Chip, FormControl, InputLabel, Select, MenuItem,
  TextField, Snackbar, Alert, CircularProgress, Tabs, Tab,
  Grid, IconButton, Divider, Stack,
} from '@mui/material';
import {
  Download as DownloadIcon, ContentCopy as CopyIcon,
  AutoAwesome as AIIcon, Code as CodeIcon,
  Description as TexIcon, OpenInNew as LinkIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const WritingIntegration = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [style, setStyle] = useState('apa');
  const [bibResult, setBibResult] = useState(null);
  const [texResult, setTexResult] = useState(null);
  const [preamble, setPreamble] = useState('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [notify, setNotify] = useState({ open: false, msg: '', severity: 'success' });

  useEffect(() => {
    fetchDocuments();
    fetchPreamble();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents');
      setDocuments(res.data || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchPreamble = async () => {
    try {
      const res = await api.get('/overleaf/latex-preamble', { params: { style } });
      setPreamble(res.data?.preamble || '');
    } catch (e) { /* ignore */ }
  };

  useEffect(() => { if (tab === 1) fetchPreamble(); }, [style, tab]);

  const handleExportBib = async () => {
    if (selectedIds.length === 0) return;
    setExporting(true);
    try {
      const res = await api.get('/overleaf/bib', { params: { document_ids: selectedIds.join(',') } });
      setBibResult(res.data);
      downloadFile(res.data?.content || '', 'references.bib', 'text/plain');
      setNotify({ open: true, msg: `Exported ${res.data?.entry_count} references`, severity: 'success' });
    } catch (e) {
      setNotify({ open: true, msg: 'Export failed', severity: 'error' });
    }
    finally { setExporting(false); }
  };

  const handleExportOverleaf = async () => {
    if (selectedIds.length === 0) return;
    setExporting(true);
    try {
      const res = await api.post('/overleaf/export-for-overleaf', selectedIds, { params: { style } });
      const data = res.data;
      setTexResult(data);

      // Download both files
      if (data.bib_file?.content) downloadFile(data.bib_file.content, 'references.bib', 'text/plain');
      if (data.tex_file?.content) downloadFile(data.tex_file.content, 'main.tex', 'text/plain');
      setNotify({ open: true, msg: `Exported ${data.entry_count} papers for Overleaf`, severity: 'success' });
    } catch (e) {
      setNotify({ open: true, msg: 'Export failed', severity: 'error' });
    }
    finally { setExporting(false); }
  };

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async (text) => {
    await navigator.clipboard.writeText(text);
    setNotify({ open: true, msg: 'Copied to clipboard!', severity: 'success' });
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>
        <TexIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Writing Integration
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="Export to Overleaf" />
        <Tab label="LaTeX Preamble" />
        <Tab label="How to Use" />
      </Tabs>

      {tab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Citation Style</InputLabel>
              <Select value={style} onChange={e => setStyle(e.target.value)} label="Citation Style">
                {['apa', 'mla', 'chicago', 'ieee', 'harvard'].map(s => (
                  <MenuItem key={s} value={s}>{s.toUpperCase()}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button variant="outlined" startIcon={<DownloadIcon />}
              disabled={selectedIds.length === 0 || exporting} onClick={handleExportBib}>
              {exporting ? 'Exporting...' : `Export .bib (${selectedIds.length})`}
            </Button>
            <Button variant="contained" startIcon={<TexIcon />}
              disabled={selectedIds.length === 0 || exporting} onClick={handleExportOverleaf}>
              {exporting ? 'Exporting...' : 'Export for Overleaf'}
            </Button>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload <strong>references.bib</strong> and <strong>main.tex</strong> to your Overleaf project.
            Use <code>{'\\cite{key}'}</code> in your document.
          </Typography>

          {loading ? <CircularProgress /> : (
            <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
              {documents.map(doc => (
                <Box key={doc.id} sx={{
                  display: 'flex', alignItems: 'center', p: 1.5,
                  borderBottom: '1px solid', borderColor: 'divider',
                  bgcolor: selectedIds.includes(doc.id) ? 'action.selected' : 'transparent',
                  cursor: 'pointer',
                }} onClick={() => setSelectedIds(prev =>
                  prev.includes(doc.id) ? prev.filter(i => i !== doc.id) : [...prev, doc.id]
                )}>
                  <input type="checkbox" checked={selectedIds.includes(doc.id)} readOnly style={{ marginRight: 12 }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{doc.title || doc.filename}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(doc.authors || []).slice(0, 2).join(', ')} {doc.year ? `(${doc.year})` : ''}
                    </Typography>
                  </Box>
                  <Chip label={doc.processed === 2 ? 'Ready' : 'Processing'} size="small"
                    color={doc.processed === 2 ? 'success' : 'warning'} variant="outlined" />
                </Box>
              ))}
            </Paper>
          )}

          {bibResult && (
            <Card variant="outlined" sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Exported .bib content</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 12, bgcolor: 'grey.100', p: 2, borderRadius: 1, maxHeight: 300, overflow: 'auto' }}>
                  {bibResult.content?.slice(0, 2000)}
                  {(bibResult.content?.length || 0) > 2000 ? '...' : ''}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Citation Style</InputLabel>
              <Select value={style} onChange={e => setStyle(e.target.value)} label="Citation Style">
                {['apa', 'mla', 'chicago', 'ieee', 'harvard'].map(s => (
                  <MenuItem key={s} value={s}>{s.toUpperCase()}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <IconButton onClick={() => copyToClipboard(preamble)}><CopyIcon /></IconButton>
          </Box>
          <TextField multiline fullWidth minRows={12}
            value={preamble}
            sx={{ fontFamily: 'monospace', '& textarea': { fontSize: 13 } }}
            InputProps={{ readOnly: true }}
          />
          <Box sx={{ mt: 2, p: 2, bgcolor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.200' }}>
            <Typography variant="body2" color="text.secondary">
              <strong>Tip:</strong> Add the preamble to your Overleaf document, upload <code>references.bib</code>,
              and use <code>{'\\cite{key}'}</code> to cite papers from your Paper Agent library.
            </Typography>
          </Box>
        </Box>
      )}

      {tab === 2 && (
        <Grid container spacing={3}>
          {[
            {
              step: '1', title: 'Export References', icon: <DownloadIcon />,
              desc: 'Select papers from your library and export them as a .bib file. Choose your preferred citation style (APA, MLA, IEEE, etc.).',
            },
            {
              step: '2', title: 'Upload to Overleaf', icon: <LinkIcon />,
              desc: 'Open your Overleaf project and upload the downloaded references.bib file. Add the LaTeX preamble from the previous tab.',
            },
            {
              step: '3', title: 'Cite and Write', icon: <CodeIcon />,
              desc: 'Use \\cite{key} to cite papers in your document. Run \\printbibliography at the end to generate your reference list.',
            },
            {
              step: '4', title: 'Use the LaTeX Package', icon: <TexIcon />,
              desc: 'For enhanced integration, upload the paperagent.sty package to your Overleaf project. This adds custom commands like \\pacite{} and \\pabibliography.',
            },
          ].map((item, i) => (
            <Grid item xs={12} sm={6} key={i}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                    <Chip label={item.step} color="primary" size="small" sx={{ minWidth: 32, fontWeight: 'bold' }} />
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{item.title}</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{item.desc}</Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Snackbar open={notify.open} autoHideDuration={4000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default WritingIntegration;
