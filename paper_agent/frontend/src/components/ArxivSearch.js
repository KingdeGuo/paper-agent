import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Search, OpenInNew, GetApp } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { arxivAPI } from '../services/api';

const ArxivSearch = ({ onImport }) => {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [searchType, setSearchType] = useState('keyword');
  const [author, setAuthor] = useState('');
  const [category, setCategory] = useState('cs.AI');
  const [maxResults, setMaxResults] = useState(10);

  const handleSearch = async () => {
    if (!query && searchType !== 'daily') {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let data;
      switch (searchType) {
        case 'keyword':
          data = await arxivAPI.search(query, maxResults);
          break;
        case 'author':
          data = await arxivAPI.searchByAuthor(query, maxResults);
          break;
        case 'title':
          data = await arxivAPI.searchByTitle(query, Math.min(maxResults, 5));
          break;
        case 'category':
          data = await arxivAPI.searchByCategory(query || category, maxResults);
          break;
        case 'daily':
          data = await arxivAPI.getDailyPapers(query || 'cs.AI', maxResults);
          break;
        default:
          data = await arxivAPI.search(query, maxResults);
      }
      setResults(data.papers || []);
    } catch (err) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (arxivId) => {
    if (!onImport) return;
    try {
      await onImport(arxivId);
    } catch (err) {
      setError(err.message || 'Import failed');
    }
  };

  const formatAuthors = (authors) => {
    if (!authors || authors.length === 0) return 'Unknown';
    if (authors.length <= 3) return authors.join(', ');
    return `${authors.slice(0, 3).join(', '}...`;
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        arXiv Search
      </Typography>

      <Stack direction="row" spacing={2} mb={2}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Search Type</InputLabel>
          <Select
            value={searchType}
            label="Search Type"
            onChange={(e) => setSearchType(e.target.value)}
          >
            <MenuItem value="keyword">Keyword</MenuItem>
            <MenuItem value="author">Author</MenuItem>
            <MenuItem value="title">Title</MenuItem>
            <MenuItem value="category">Category</MenuItem>
            <MenuItem value="daily">Daily Papers</MenuItem>
          </Select>
        </FormControl>

        <TextField
          size="small"
          label={
            searchType === 'daily' ? 'Category (e.g., cs.AI)' :
            searchType === 'author' ? 'Author Name' :
            searchType === 'category' ? 'Category (e.g., cs.AI)' :
            'Search Query'
          }
          value={searchType === 'daily' ? category : query}
          onChange={(e) => {
            if (searchType === 'daily' || searchType === 'category') {
              setCategory(e.target.value);
            } else {
              setQuery(e.target.value);
            }
          }}
          onKeyPress={(e) => {
            if (e.key === 'Enter') handleSearch();
          }}
          sx={{ flexGrow: 1 }}
        />

        <TextField
          size="small"
          label="Max Results"
          type="number"
          value={maxResults}
          onChange={(e) => setMaxResults(parseInt(e.target.value) || 10)}
          sx={{ width: 100 }}
        />

        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={loading || (!query && searchType !== 'daily')}
          startIcon={loading ? <CircularProgress size={20} /> : <Search />}
        >
          Search
        </Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {results.length > 0 && (
        <List>
          {results.map((paper, index) => (
            <ListItem key={paper.arxiv_id || index} divider>
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    {paper.title || 'Untitled'}
                    {paper.year && (
                      <Chip label={paper.year} size="small" sx={{ ml: 1 }} />
                    )}
                  </Typography>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {formatAuthors(paper.authors)}
                    </Typography>
                    {paper.abstract && (
                      <Typography variant="body2" sx={{ mt: 1, display: '-webkit-ox', WebkitLineClamp: 3, overflow: 'hidden' }}>
                        {paper.abstract}
                      </Typography>
                    )}
                    <Stack direction="row" spacing={1} mt={1}>
                      {paper.categories?.map((cat) => (
                        <Chip key={cat} label={cat} size="small" />
                      ))}
                      {paper.pdf_url && (
                        <IconButton
                          size="small"
                          href={paper.pdf_url}
                          target="_blank"
                          title="Open PDF"
                        >
                          <OpenInNew fontSize="small" />
                        </IconButton>
                      )}
                      {paper.arxiv_url && (
                        <IconButton
                          size="small"
                          href={paper.arxiv_url}
                          target="_blank"
                          title="View on arXiv"
                        >
                          <OpenInNew fontSize="small" />
                        </IconButton>
                      )}
                    </Stack>
                  </Box>
                }
              />
              {onImport && paper.arxiv_id && (
                <ListItemSecondaryAction>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => handleImport(paper.arxiv_id)}
                  >
                    Import
                  </Button>
                </ListItemSecondaryAction>
              )}
            </ListItem>
          ))}
        </List>
      )}

      {!loading && results.length === 0 && query && (
        <Alert severity="info">
          No papers found. Try a different query.
        </Alert>
      )}
    </Paper>
  );
};

export default ArxivSearch;
