import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Grid,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Snackbar,
} from '@mui/material';
import { 
  Search as SearchIcon, 
  CloudDownload as ImportIcon,
  Description as DocIcon,
  Language as ArxivIcon
} from '@mui/icons-material';
import { searchAPI, arxivAPI } from '../services/api';

const Search = () => {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [arxivResults, setArxivResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trending, setTrending] = useState([]);
  const [tabValue, setTabValue] = useState(0);
  const [importing, setImporting] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  useEffect(() => {
    fetchTrending();
  }, []);

  const fetchTrending = async () => {
    try {
      const data = await searchAPI.trending(10);
      setTrending(data);
    } catch (err) {
      console.error('Error fetching trending documents:', err);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      if (tabValue === 0) {
        const data = await searchAPI.simpleSearch(query);
        setResults(data);
      } else {
        const data = await arxivAPI.search(query, 20);
        setArxivResults(data.papers || []);
      }
    } catch (err) {
      setError(t('errors.searchFailed', { message: err.message }));
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (paper) => {
    const id = paper.arxiv_id;
    setImporting(prev => ({ ...prev, [id]: true }));
    
    try {
      const response = await arxivAPI.importPaper(id);
      setSnackbar({ open: true, message: response.message || t('documents.uploadSuccess') });
    } catch (err) {
      setError(t('errors.uploadFailed', { message: err.message }));
    } finally {
      setImporting(prev => ({ ...prev, [id]: false }));
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          {t('search.title')}
        </Typography>
        <Chip 
          label="AI Discovery" 
          color="secondary" 
          size="small" 
          sx={{ ml: 2, fontWeight: 'bold' }} 
        />
      </Box>

      <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={(e, v) => setTabValue(v)}
          sx={{ borderBottom: 1, borderColor: 'divider', px: 2, pt: 1 }}
        >
          <Tab icon={<DocIcon />} label={t('search.simpleSearch')} iconPosition="start" />
          <Tab icon={<ArxivIcon />} label="arXiv Global" iconPosition="start" />
        </Tabs>
        
        <CardContent sx={{ pt: 3 }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder={tabValue === 0 ? t('search.placeholder') : "Search millions of papers on arXiv..."}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              sx={{ bgcolor: 'background.paper' }}
            />
            <Button
              variant="contained"
              size="large"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              sx={{ px: 4, fontWeight: 'bold' }}
            >
              {t('common.confirm')}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {loading && (
        <Box sx={{ mb: 4 }}>
          <LinearProgress sx={{ borderRadius: 1, height: 6 }} />
          <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary', textAlign: 'center' }}>
            {t('search.searching')}
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
          {error}
        </Alert>
      )}

      {/* Local Search Results */}
      {tabValue === 0 && results.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
            {t('search.results')} ({results.length})
          </Typography>
          <List>
            {results.map((result, index) => (
              <Card key={index} sx={{ mb: 2, borderRadius: 2, '&:hover': { boxShadow: 4, transition: '0.3s' } }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                      {result.title || result.filename}
                    </Typography>
                    <Chip
                      label={result.processed === 2 ? t('documents.processingStatus.completed') : (result.processed === 3 ? t('documents.processingStatus.failed') : t('documents.processingStatus.pending'))}
                      size="small"
                      color={result.processed === 2 ? 'success' : (result.processed === 3 ? 'error' : 'default')}
                      variant="tonal"
                    />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
                    {result.authors && result.authors.length > 0 && (
                      <Chip label={result.authors.join(', ')} size="small" variant="outlined" />
                    )}
                    {result.year && (
                      <Chip label={result.year.toString()} size="small" color="primary" variant="outlined" />
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {result.abstract || t('documentDetail.noDescription')}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </List>
        </Box>
      )}

      {/* arXiv Search Results */}
      {tabValue === 1 && arxivResults.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
            Found on arXiv ({arxivResults.length})
          </Typography>
          <Grid container spacing={2}>
            {arxivResults.map((paper, index) => (
              <Grid item xs={12} key={index}>
                <Card sx={{ borderRadius: 2, '&:hover': { boxShadow: 4, transition: '0.3s' } }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                          {paper.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
                          <Chip label={paper.arxiv_id} size="small" color="secondary" sx={{ fontWeight: 'bold' }} />
                          {paper.authors?.slice(0, 3).map((author, i) => (
                            <Chip key={i} label={author} size="small" variant="outlined" />
                          ))}
                          {paper.year && (
                            <Chip label={paper.year} size="small" color="primary" variant="outlined" />
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                          {paper.abstract}
                        </Typography>
                      </Box>
                      <Tooltip title="Import into Library">
                        <IconButton 
                          color="primary" 
                          onClick={() => handleImport(paper)}
                          disabled={importing[paper.arxiv_id]}
                          sx={{ bgcolor: 'primary.light', '&:hover': { bgcolor: 'primary.main', color: 'white' }, ml: 2 }}
                        >
                          {importing[paper.arxiv_id] ? <CircularProgress size={24} /> : <ImportIcon />}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Recommendations / Trending */}
      {!query && !loading && tabValue === 0 && trending.length > 0 && (
        <Box>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium', mb: 3 }}>
            {t('search.recommendations')}
          </Typography>
          <Grid container spacing={3}>
            {trending.map((item, index) => {
              const doc = item.document || item;
              return (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <Card sx={{ height: '100%', borderRadius: 2, '&:hover': { transform: 'translateY(-4px)', boxShadow: 6, transition: '0.3s' } }}>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', height: 48, overflow: 'hidden' }}>
                        {doc.title || doc.filename || t('documents.noName')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {doc.authors?.join(', ') || t('documents.unknown')}
                      </Typography>
                      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                        <Chip label={doc.year || 'N/A'} size="small" color="primary" variant="tonal" />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {!query && !loading && results.length === 0 && arxivResults.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8, opacity: 0.6 }}>
          <SearchIcon sx={{ fontSize: 64, mb: 2, color: 'text.disabled' }} />
          <Typography variant="body1" color="text.secondary">
            {t('search.contentPlaceholder')}
          </Typography>
        </Box>
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </Box>
  );
};

export default Search;
