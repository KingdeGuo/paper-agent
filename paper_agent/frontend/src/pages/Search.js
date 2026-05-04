import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box, Typography, TextField, Button, Card, CardContent, Chip,
  List, ListItem, ListItemText,   LinearProgress, Grid, Alert,
  Tabs, Tab, IconButton, Tooltip, Snackbar, Drawer, Stack,
  Dialog, DialogTitle, DialogContent, DialogActions, Divider,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon, CloudDownload as ImportIcon,
  Description as DocIcon, Language as ArxivIcon,
  Bookmark as SaveIcon, BookmarkBorder as SaveBorderIcon,
  History as HistoryIcon, DeleteSweep as ClearIcon,
  TrendingUp as TrendingIcon, OpenInNew as OpenIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import { searchAPI, arxivAPI } from '../services/api';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

const Search = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [arxivResults, setArxivResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trending, setTrending] = useState([]);
  const [tabValue, setTabValue] = useState(0);
  const [importing, setImporting] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const [savedSearches, setSavedSearches] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [saveDialog, setSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [showPanel, setShowPanel] = useState(false);

  useEffect(() => { fetchTrending(); fetchSavedSearches(); fetchHistory(); }, []);

  const fetchTrending = async () => {
    try { const data = await searchAPI.trending(10); setTrending(data); } catch (e) {}
  };
  const fetchSavedSearches = async () => {
    try { const res = await api.get('/searches/saved'); setSavedSearches(res.data || []); } catch (e) {}
  };
  const fetchHistory = async () => {
    try { const res = await api.get('/searches/history'); setSearchHistory(res.data || []); } catch (e) {}
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(null);
    try {
      if (tabValue === 0) {
        const data = await searchAPI.simpleSearch(query);
        setResults(Array.isArray(data) ? data : data.results || []);
      } else {
        const data = await arxivAPI.search(query, 20);
        setArxivResults(data.papers || []);
      }
      await api.post('/searches/history', null, { params: { query: query.trim() } });
      fetchHistory();
    } catch (err) {
      setError(t('errors.searchFailed', { message: err.message }));
    } finally { setLoading(false); }
  };

  const handleSaveSearch = async () => {
    if (!saveName.trim()) return;
    try {
      await api.post('/searches/save', null, { params: { name: saveName, query: query.trim(), result_count: results.length } });
      setSaveDialog(false); setSaveName(''); fetchSavedSearches();
      setSnackbar({ open: true, message: 'Search saved!' });
    } catch (e) { console.error(e); }
  };

  const handleReRunSearch = (q) => { setQuery(q); setTimeout(() => handleSearch(), 100); };

  const handleImport = async (paper) => {
    const id = paper.arxiv_id;
    setImporting(prev => ({ ...prev, [id]: true }));
    try {
      const response = await arxivAPI.importPaper(id);
      setSnackbar({ open: true, message: response.message || t('documents.uploadSuccess') });
    } catch (err) {
      setError(t('errors.uploadFailed', { message: err.message }));
    } finally { setImporting(prev => ({ ...prev, [id]: false })); }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      {/* Main Search Area */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>{t('search.title')}</Typography>
          <Chip label="AI Discovery" color="secondary" size="small" sx={{ fontWeight: 'bold' }} />
          <Box sx={{ flex: 1 }} />
          <Button size="small" startIcon={<HistoryIcon />} onClick={() => setShowPanel(!showPanel)}>
            {showPanel ? 'Hide' : 'History'}
          </Button>
        </Box>

        <Card sx={{ mb: 2, borderRadius: 2, boxShadow: 3 }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}
            sx={{ borderBottom: 1, borderColor: 'divider', px: 2, pt: 1 }}>
            <Tab icon={<DocIcon />} label={t('search.simpleSearch')} iconPosition="start" />
            <Tab icon={<ArxivIcon />} label="arXiv Global" iconPosition="start" />
          </Tabs>
          <CardContent sx={{ pt: 3 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField fullWidth variant="outlined" size="medium"
                placeholder={tabValue === 0 ? t('search.placeholder') : "Search millions of papers on arXiv..."}
                value={query} onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
              <Button variant="contained" size="large" startIcon={<SearchIcon />}
                onClick={handleSearch} disabled={loading || !query.trim()} sx={{ px: 4, fontWeight: 'bold' }}>
                {t('common.confirm')}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Save Search Button */}
        {results.length > 0 && (
          <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
            <Button size="small" startIcon={<SaveBorderIcon />} onClick={() => setSaveDialog(true)}>Save Search</Button>
            {savedSearches.length > 0 && (
              <Stack direction="row" spacing={0.5} alignItems="center">
                {savedSearches.slice(0, 3).map(s => (
                  <Chip key={s.id} icon={<SaveIcon />} label={s.name} size="small"
                    onClick={() => handleReRunSearch(s.query)} variant="outlined" />
                ))}
              </Stack>
            )}
          </Box>
        )}

        {loading && <Box sx={{ mb: 2 }}><LinearProgress sx={{ borderRadius: 1, height: 6 }} /></Box>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {/* Local Results */}
        {tabValue === 0 && results.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>{t('search.results')} ({results.length})</Typography>
            <List disablePadding>
              {results.map((result, i) => (
                <Card key={i} sx={{ mb: 1.5, cursor: 'pointer' }} onClick={() => navigate(`/documents/${result.id}`)}>
                  <CardContent sx={{ py: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{result.title || result.filename}</Typography>
                      <Chip label={result.processed === 2 ? 'Completed' : result.processed === 3 ? 'Failed' : 'Pending'}
                        size="small" color={result.processed === 2 ? 'success' : result.processed === 3 ? 'error' : 'default'} variant="outlined" />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                      {result.authors?.length > 0 && <Chip label={result.authors.slice(0, 2).join(', ')} size="small" variant="outlined" />}
                      {result.year && <Chip label={result.year} size="small" color="primary" variant="outlined" />}
                      {result.score && <Chip label={`${(result.score * 100).toFixed(0)}% match`} size="small" color="secondary" variant="outlined" />}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </List>
          </Box>
        )}

        {/* arXiv Results */}
        {tabValue === 1 && arxivResults.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>Found on arXiv ({arxivResults.length})</Typography>
            <Grid container spacing={1.5}>
              {arxivResults.map((paper, i) => (
                <Grid item xs={12} key={i}>
                  <Card sx={{ borderRadius: 2 }}>
                    <CardContent sx={{ py: 1.5 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{paper.title}</Typography>
                          <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                            <Chip label={paper.arxiv_id} size="small" color="secondary" />
                            {paper.authors?.slice(0, 2).map((a, j) => <Chip key={j} label={a} size="small" variant="outlined" />)}
                            {paper.year && <Chip label={paper.year} size="small" color="primary" variant="outlined" />}
                          </Box>
                        </Box>
                        <IconButton color="primary" onClick={() => handleImport(paper)}
                          disabled={importing[paper.arxiv_id]} size="small">
                          {importing[paper.arxiv_id] ? <CircularProgress size={20} /> : <ImportIcon />}
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Trending / Empty */}
        {!query && !loading && tabValue === 0 && results.length === 0 && (
          trending.length > 0 ? (
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingIcon /> {t('search.recommendations')}
              </Typography>
              <Grid container spacing={2}>
                {trending.map((item, i) => {
                  const doc = item.document || item;
                  return (
                    <Grid item xs={12} sm={6} md={4} key={i}>
                      <Card sx={{ cursor: 'pointer' }} onClick={() => navigate(`/documents/${doc.id}`)}>
                        <CardContent>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5, height: 40, overflow: 'hidden' }}>{doc.title || doc.filename}</Typography>
                          <Typography variant="caption" color="text.secondary" display="block">{(doc.authors || []).slice(0, 2).join(', ')}</Typography>
                          <Chip label={doc.year || 'N/A'} size="small" color="primary" variant="outlined" sx={{ mt: 1 }} />
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 8, opacity: 0.6 }}>
              <SearchIcon sx={{ fontSize: 64, mb: 2, color: 'text.disabled' }} />
              <Typography color="text.secondary">{t('search.contentPlaceholder')}</Typography>
            </Box>
          )
        )}

        <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar({ ...snackbar, open: false })} message={snackbar.message} />
      </Box>

      {/* Side Panel: Saved + History */}
      <Drawer anchor="right" open={showPanel} onClose={() => setShowPanel(false)} variant="persistent"
        sx={{ '& .MuiDrawer-paper': { width: 320, p: 2, position: 'static' }, display: showPanel ? 'block' : 'none' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <SaveIcon /> Saved Searches
        </Typography>
        {savedSearches.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>No saved searches yet.</Typography>
        ) : (
          <Stack spacing={1} sx={{ mb: 3 }}>
            {savedSearches.map(s => (
              <Card key={s.id} variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => handleReRunSearch(s.query)}>
                <CardContent sx={{ py: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{s.name}</Typography>
                  <Typography variant="caption" color="text.secondary">"{s.query.slice(0, 50)}" · {s.result_count} results</Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}

        <Divider sx={{ mb: 2 }} />
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'space-between' }}>
          <span><HistoryIcon sx={{ mr: 0.5 }} /> Search History</span>
          <IconButton size="small" onClick={async () => { await api.delete('/searches/history'); fetchHistory(); }}><ClearIcon /></IconButton>
        </Typography>
        {searchHistory.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>No search history yet.</Typography>
        ) : (
          <List dense disablePadding>
            {searchHistory.slice(0, 15).map((h, i) => (
              <ListItem key={i} disablePadding sx={{ cursor: 'pointer' }} onClick={() => handleReRunSearch(h.query)}>
                <ListItemText primary={<Typography variant="body2">{h.query}</Typography>}
                  secondary={`${h.result_count} results · ${h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}`} />
              </ListItem>
            ))}
          </List>
        )}
      </Drawer>

      {/* Save Dialog */}
      <Dialog open={saveDialog} onClose={() => setSaveDialog(false)}>
        <DialogTitle>Save Search</DialogTitle>
        <DialogContent>
          <TextField autoFocus fullWidth margin="dense" label="Search Name" value={saveName}
            onChange={e => setSaveName(e.target.value)} placeholder="e.g. Transformer efficiency papers"
            helperText={`Query: "${query}"`} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveSearch}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Search;
