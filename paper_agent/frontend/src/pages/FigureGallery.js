import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, CardMedia, CardActions, Chip, Button, CircularProgress, TextField, Dialog, DialogTitle, DialogContent, IconButton, Stack, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { AutoAwesome as AIIcon, Image as ImageIcon, TableChart as TableIcon, Download as DownloadIcon, Search as SearchIcon, FilterList as FilterIcon } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const FigureGallery = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [figures, setFigures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFigure, setSelectedFigure] = useState(null);
  const [description, setDescription] = useState('');
  const [describing, setDescribing] = useState(false);
  const [viewMode, setViewMode] = useState('gallery');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => { fetchFigures(); }, [id]);

  const fetchFigures = async () => {
    setLoading(true);
    try {
      const url = id ? `/figures/${id}` : '/figures/gallery';
      const res = await api.get(url);
      setFigures(res.data || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleDescribe = async (figureId) => {
    setDescribing(true);
    try {
      const res = await api.get(`/figures/describe/${figureId}`);
      setDescription(res.data?.description || '');
    } catch (e) { setDescription('Description unavailable'); }
    finally { setDescribing(false); }
  };

  const handleExtract = async (docId) => {
    try {
      await api.post(`/figures/extract/${docId}`);
      fetchFigures();
    } catch (e) { console.error(e); }
  };

  const openFigureDialog = (fig) => {
    setSelectedFigure(fig);
    setDescription('');
  };

  const filteredFigures = searchQuery
    ? figures.filter(f => (f.caption || '').toLowerCase().includes(searchQuery.toLowerCase()))
    : figures;

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          <ImageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Figure Gallery
          {id && <Chip label="Paper view" size="small" sx={{ ml: 1 }} />}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField size="small" placeholder="Search figures..." value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            InputProps={{ startAdornment: <SearchIcon fontSize="small" sx={{ mr: 0.5 }} /> }} />
          {!id && (
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>View</InputLabel>
              <Select value={viewMode} onChange={e => setViewMode(e.target.value)} label="View">
                <MenuItem value="gallery">Gallery</MenuItem>
                <MenuItem value="grid">Grid</MenuItem>
              </Select>
            </FormControl>
          )}
        </Box>
      </Box>

      {loading ? <Box textAlign="center" py={10}><CircularProgress /></Box> : (
        filteredFigures.length === 0 ? (
          <Box textAlign="center" py={10} sx={{ opacity: 0.5 }}>
            <ImageIcon sx={{ fontSize: 80, mb: 2, color: 'text.disabled' }} />
            <Typography variant="h6">No figures extracted yet</Typography>
            <Typography variant="body2" color="text.secondary">
              {id ? 'Extract figures from this paper to visualize key results.' : 'Upload papers and extract figures to build your gallery.'}
            </Typography>
            {id && <Button variant="contained" sx={{ mt: 2 }} onClick={() => handleExtract(id)}>Extract Figures</Button>}
          </Box>
        ) : (
          <Grid container spacing={2}>
            {filteredFigures.map((fig, i) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={fig.id || i}>
                <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { boxShadow: 3 } }}
                  onClick={() => openFigureDialog(fig)}>
                  <CardMedia
                    component="img"
                    height="180"
                    image={`${API_BASE}/figures/image/${fig.id}`}
                    alt={fig.caption || 'Figure'}
                    sx={{ objectFit: 'contain', bgcolor: 'grey.100', p: 1 }}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="caption" color="text.secondary" display="block" noWrap>
                      {fig.doc_title || 'Paper'} · Page {fig.page}
                    </Typography>
                    <Typography variant="body2" noWrap sx={{ mt: 0.5 }}>
                      {fig.caption || 'No caption'}
                    </Typography>
                    <Chip label={`${fig.width}×${fig.height}`} size="small" variant="outlined" sx={{ mt: 0.5 }} />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )
      )}

      {/* Figure Detail Dialog */}
      <Dialog open={Boolean(selectedFigure)} onClose={() => setSelectedFigure(null)} maxWidth="lg" fullWidth>
        {selectedFigure && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">Figure — Page {selectedFigure.page}</Typography>
                <Box>
                  <IconButton onClick={() => handleDescribe(selectedFigure.id)} disabled={describing}>
                    {describing ? <CircularProgress size={20} /> : <AIIcon />}
                  </IconButton>
                  <IconButton href={`${API_BASE}/figures/image/${selectedFigure.id}`} target="_blank">
                    <DownloadIcon />
                  </IconButton>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <Box component="img" src={`${API_BASE}/figures/image/${selectedFigure.id}`}
                  alt={selectedFigure.caption || 'Figure'}
                  sx={{ maxWidth: '100%', maxHeight: '60vh', objectFit: 'contain' }}
                  onError={(e) => { e.target.style.display = 'none'; }} />
              </Box>
              {selectedFigure.caption && (
                <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary', mb: 1 }}>
                  {selectedFigure.caption}
                </Typography>
              )}
              {description && (
                <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AIIcon fontSize="small" /> AI Description
                  </Typography>
                  <Typography variant="body2">
                    <ReactMarkdown>{description}</ReactMarkdown>
                  </Typography>
                </Paper>
              )}
              <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                <Chip label={`${selectedFigure.width}×${selectedFigure.height}px`} size="small" variant="outlined" />
                <Chip label={`${(selectedFigure.size_bytes / 1024).toFixed(1)} KB`} size="small" variant="outlined" />
                <Chip label={selectedFigure.format || 'png'} size="small" variant="outlined" />
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default FigureGallery;
