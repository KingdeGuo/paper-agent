import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, IconButton, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, Grid,
  Alert, Snackbar, CircularProgress, Tabs, Tab, FormControl,
  InputLabel, Select, MenuItem, Card, CardContent,
} from '@mui/material';
import {
  Download as DownloadIcon, ContentCopy as CopyIcon,
  Search as SearchIcon, Upload as UploadIcon,
  AutoAwesome as AIIcon, Bookmark as BookmarkIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Citations = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bibtexResult, setBibtexResult] = useState(null);
  const [styles, setStyles] = useState([]);
  const [selectedStyle, setSelectedStyle] = useState('apa');
  const [notify, setNotify] = useState({ open: false, msg: '', severity: 'success' });
  const [doiQuery, setDoiQuery] = useState('');
  const [doiResult, setDoiResult] = useState(null);
  const [doiLoading, setDoiLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [bibtexDialog, setBibtexDialog] = useState(false);
  const [bibtexInput, setBibtexInput] = useState('');
  const [importLoading, setImportLoading] = useState(false);

  useEffect(() => { fetchDocuments(); fetchStyles(); }, []);

  const fetchDocuments = async () => {
    try {
      const data = await api.get('/documents');
      setDocuments(data.data || data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchStyles = async () => {
    try {
      const res = await api.get('/citations/styles');
      setStyles(res.data?.styles || []);
      setSelectedStyle(res.data?.default || 'apa');
    } catch (e) { /* ignore */ }
  };

  const handleExportBibtex = async (singleId = null) => {
    const ids = singleId ? [singleId] : selectedIds;
    if (ids.length === 0) return;
    try {
      let res;
      if (ids.length === 1) {
        res = await api.get(`/citations/export/${ids[0]}`, { params: { style: selectedStyle } });
      } else {
        res = await api.post('/citations/export-batch', { document_ids: ids, style: selectedStyle });
      }
      setBibtexResult(res.data);
    } catch (e) {
      setNotify({ open: true, msg: 'Export failed', severity: 'error' });
    }
  };

  const handleCopyBibtex = () => {
    if (!bibtexResult) return;
    const text = bibtexResult.bibtex || '';
    navigator.clipboard.writeText(text);
    setNotify({ open: true, msg: 'Copied to clipboard!', severity: 'success' });
  };

  const handleDownloadBibtex = () => {
    if (!bibtexResult) return;
    const text = bibtexResult.bibtex || '';
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'references.bib'; a.click();
    URL.revokeObjectURL(url);
  };

  const handleLookupDoi = async () => {
    if (!doiQuery.trim()) return;
    setDoiLoading(true); setDoiResult(null);
    try {
      const res = await api.get('/citations/lookup-doi', { params: { doi: doiQuery.trim() } });
      setDoiResult(res.data);
    } catch (e) {
      setDoiResult({ error: 'DOI not found' });
    }
    finally { setDoiLoading(false); }
  };

  const handleSearchCrossRef = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true); setSearchResults([]);
    try {
      const res = await api.get('/citations/search', { params: { query: searchQuery.trim(), limit: 20 } });
      setSearchResults(res.data?.results || []);
    } catch (e) { console.error(e); }
    finally { setSearchLoading(false); }
  };

  const handleImportBibtex = async () => {
    if (!bibtexInput.trim()) return;
    setImportLoading(true);
    try {
      const res = await api.post('/citations/import-bibtex', bibtexInput, {
        headers: { 'Content-Type': 'text/plain' }
      });
      setNotify({ open: true, msg: `Imported ${res.data?.imported || 0} entries`, severity: 'success' });
      setBibtexDialog(false);
      setBibtexInput('');
      fetchDocuments();
    } catch (e) {
      setNotify({ open: true, msg: 'Import failed', severity: 'error' });
    }
    finally { setImportLoading(false); }
  };

  const handleGenerateBibliography = async () => {
    if (selectedIds.length === 0) return;
    try {
      const res = await api.post('/citations/bibliography', selectedIds, { params: { style: selectedStyle } });
      setBibtexResult({ bibliography: res.data?.bibliography });
    } catch (e) {
      setNotify({ open: true, msg: 'Failed to generate bibliography', severity: 'error' });
    }
  };

  const renderBibtexResult = () => {
    if (!bibtexResult) return null;
    return (
      <Card variant="outlined" sx={{ mt: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2">Output</Typography>
            <Box>
              <IconButton size="small" onClick={handleCopyBibtex}><CopyIcon /></IconButton>
              <IconButton size="small" onClick={handleDownloadBibtex}><DownloadIcon /></IconButton>
            </Box>
          </Box>
          {bibtexResult.bibtex && (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 12, bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>{bibtexResult.bibtex}</Typography>
          )}
          {bibtexResult.formatted && (
            <>
              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Formatted ({selectedStyle.toUpperCase()}):</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>{bibtexResult.formatted}</Typography>
            </>
          )}
          {bibtexResult.bibliography && (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>{bibtexResult.bibliography}</Typography>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>Citations & Bibliography</Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="Export" />
        <Tab label="DOI Lookup" />
        <Tab label="Search Publications" />
        <Tab label="Import BibTeX" />
      </Tabs>

      {/* Tab 0: Export */}
      {tab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Citation Style</InputLabel>
              <Select value={selectedStyle} onChange={e => setSelectedStyle(e.target.value)} label="Citation Style">
                {styles.map(s => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
              </Select>
            </FormControl>
            <Button variant="contained" disabled={selectedIds.length === 0} onClick={() => handleExportBibtex()}>
              Export Selected ({selectedIds.length})
            </Button>
            <Button variant="outlined" disabled={selectedIds.length === 0} onClick={handleGenerateBibliography}>
              Generate Bibliography
            </Button>
            <Button variant="text" startIcon={<UploadIcon />} onClick={() => setBibtexDialog(true)}>
              Import BibTeX
            </Button>
          </Box>

          {loading ? <CircularProgress /> : (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <input type="checkbox" onChange={e => {
                        if (e.target.checked) setSelectedIds(documents.map(d => d.id));
                        else setSelectedIds([]);
                      }} />
                    </TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Authors</TableCell>
                    <TableCell>Year</TableCell>
                    <TableCell>Citation Key</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {documents.map(doc => (
                    <TableRow key={doc.id} hover selected={selectedIds.includes(doc.id)}>
                      <TableCell padding="checkbox">
                        <input type="checkbox" checked={selectedIds.includes(doc.id)}
                          onChange={() => setSelectedIds(prev => prev.includes(doc.id) ? prev.filter(i => i !== doc.id) : [...prev, doc.id])} />
                      </TableCell>
                      <TableCell>{doc.title || 'Untitled'}</TableCell>
                      <TableCell>{(doc.authors || []).slice(0, 2).join(', ')}{doc.authors?.length > 2 ? '...' : ''}</TableCell>
                      <TableCell>{doc.year || '-'}</TableCell>
                      <TableCell><Chip label={doc.citation_key || 'auto'} size="small" /></TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => handleExportBibtex(doc.id)}><DownloadIcon /></IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {renderBibtexResult()}
        </Box>
      )}

      {/* Tab 1: DOI Lookup */}
      {tab === 1 && (
        <Box sx={{ maxWidth: 700 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Enter a DOI (Digital Object Identifier) to automatically retrieve publication metadata.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField fullWidth size="small" placeholder="e.g. 10.1038/s41586-024-07155-5"
              value={doiQuery} onChange={e => setDoiQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLookupDoi()} />
            <Button variant="contained" onClick={handleLookupDoi} disabled={doiLoading}>
              {doiLoading ? <CircularProgress size={20} /> : 'Lookup'}
            </Button>
          </Box>
          {doiResult && (
            <Card variant="outlined">
              <CardContent>
                {doiResult.error ? (
                  <Alert severity="warning">DOI not found. Check the identifier and try again.</Alert>
                ) : (
                  <Grid container spacing={2}>
                    <Grid item xs={12}><Typography variant="h6">{doiResult.title}</Typography></Grid>
                    <Grid item xs={6}><Typography variant="caption">Authors</Typography><Typography>{(doiResult.authors || []).join('; ') || 'N/A'}</Typography></Grid>
                    <Grid item xs={6}><Typography variant="caption">Year</Typography><Typography>{doiResult.year || 'N/A'}</Typography></Grid>
                    <Grid item xs={6}><Typography variant="caption">Journal</Typography><Typography>{doiResult.journal || 'N/A'}</Typography></Grid>
                    <Grid item xs={3}><Typography variant="caption">Volume</Typography><Typography>{doiResult.volume || 'N/A'}</Typography></Grid>
                    <Grid item xs={3}><Typography variant="caption">Pages</Typography><Typography>{doiResult.pages || 'N/A'}</Typography></Grid>
                    <Grid item xs={12}><Typography variant="caption">DOI</Typography><Typography>{doiResult.doi}</Typography></Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab 2: Search */}
      {tab === 2 && (
        <Box sx={{ maxWidth: 800 }}>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField fullWidth size="small" placeholder="Search millions of publications..." value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearchCrossRef()} />
            <Button variant="contained" onClick={handleSearchCrossRef} disabled={searchLoading}>
              {searchLoading ? <CircularProgress size={20} /> : <SearchIcon />}
            </Button>
          </Box>
          {searchResults.map((r, i) => (
            <Card key={i} variant="outlined" sx={{ mb: 1 }}>
              <CardContent sx={{ py: 1.5 }}>
                <Typography variant="subtitle2">{r.title}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {(r.authors || []).slice(0, 5).join('; ')}{r.authors?.length > 5 ? '...' : ''} ({r.year || 'n.d.'})
                </Typography>
                {r.doi && <Chip label={r.doi} size="small" variant="outlined" sx={{ ml: 1 }} />}
              </CardContent>
            </Card>
          ))}
          {searchResults.length === 0 && searchQuery && !searchLoading && (
            <Typography color="text.secondary">No results found.</Typography>
          )}
        </Box>
      )}

      {/* Tab 3: Import */}
      {tab === 3 && (
        <Box sx={{ maxWidth: 700 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Paste your BibTeX entries below to import them into your library.
          </Typography>
          <TextField fullWidth multiline rows={10} placeholder="@article{key,&#10;  title = {{Title}},&#10;  author = {{Author}},&#10;  year = {2024}&#10;}"
            value={bibtexInput} onChange={e => setBibtexInput(e.target.value)} sx={{ mb: 2, fontFamily: 'monospace' }} />
          <Button variant="contained" onClick={handleImportBibtex} disabled={!bibtexInput.trim() || importLoading}>
            {importLoading ? <CircularProgress size={20} /> : 'Import BibTeX'}
          </Button>
        </Box>
      )}

      <Snackbar open={notify.open} autoHideDuration={4000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default Citations;
