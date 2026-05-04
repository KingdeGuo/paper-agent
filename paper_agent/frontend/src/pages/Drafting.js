import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Button, Paper, TextField, Grid, 
  Card, CardContent, CircularProgress, Alert, Divider,
  IconButton, Tooltip
} from '@mui/material';
import { 
  HistoryEdu as DraftingIcon,
  Functions as FormulaIcon,
  ContentCopy as CopyIcon,
  AutoAwesome as MagicIcon,
  LibraryBooks as LibraryIcon
} from '@mui/icons-material';
import api from '../services/api';

const Drafting = () => {
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [allDocs, setAllDocs] = useState([]);
  const [topic, setTopic] = useState('');
  const [latexResult, setLatexResult] = useState('');
  const [formula, setFormula] = useState('');
  const [formulaExplanation, setFormulaExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('review'); // 'review' or 'formula'

  useEffect(() => {
    fetchDocs();
  }, []);

  const fetchDocs = async () => {
    try {
      const response = await api.get('/documents');
      setAllDocs(response.data);
    } catch (err) {
      console.error("Fetch failed", err);
    }
  };

  const handleGenerateReview = async () => {
    if (selectedDocs.length === 0 || !topic) {
      alert("Please select papers and enter a focus topic.");
      return;
    }
    setLoading(true);
    try {
      const response = await api.post('/drafting/related-work', {
        doc_ids: selectedDocs.map(d => d.id),
        focus_topic: topic
      });
      setLatexResult(response.data.content);
    } catch (err) {
      console.error("Drafting failed", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecodeFormula = async () => {
    if (!formula) return;
    setLoading(true);
    try {
      const response = await api.post('/drafting/decode-formula', {
        formula: formula,
        context: "Scientific paper context"
      });
      setFormulaExplanation(response.data.explanation);
    } catch (err) {
      console.error("Decoding failed", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = (doc) => {
    if (selectedDocs.find(d => d.id === doc.id)) {
      setSelectedDocs(selectedDocs.filter(d => d.id !== doc.id));
    } else {
      setSelectedDocs([...selectedDocs, doc]);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center' }}>
        <DraftingIcon sx={{ mr: 2, color: 'primary.main' }} />
        Drafting Bridge
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Automate the most tedious parts of research: Literature reviews and complex formula decoding.
      </Typography>

      <Box sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Button 
          variant={mode === 'review' ? 'contained' : 'text'} 
          onClick={() => setMode('review')}
          startIcon={<LibraryIcon />}
          sx={{ mr: 2, mb: 1 }}
        >
          Related Work Generator
        </Button>
        <Button 
          variant={mode === 'formula' ? 'contained' : 'text'} 
          onClick={() => setMode('formula')}
          startIcon={<FormulaIcon />}
          sx={{ mb: 1 }}
        >
          Formula Decoder
        </Button>
      </Box>

      {mode === 'review' ? (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: '70vh', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>Select Reference Papers ({selectedDocs.length})</Typography>
              {allDocs.map((doc) => (
                <Box 
                  key={doc.id} 
                  onClick={() => toggleDoc(doc)}
                  sx={{ 
                    p: 1.5, mb: 1, borderRadius: 1, cursor: 'pointer',
                    bgcolor: selectedDocs.find(d => d.id === doc.id) ? 'primary.light' : 'transparent',
                    border: '1px solid',
                    borderColor: 'divider',
                    '&:hover': { bgcolor: 'grey.100' }
                  }}
                >
                  <Typography variant="body2" fontWeight="bold">{doc.title}</Typography>
                  <Typography variant="caption">{doc.authors?.join(', ')}</Typography>
                </Box>
              ))}
            </Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Focus Topic / Research Goal"
              placeholder="e.g., Efficiency of Sparse Transformers in Long-context tasks"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button 
              variant="contained" 
              fullWidth 
              startIcon={<MagicIcon />} 
              onClick={handleGenerateReview}
              disabled={loading || selectedDocs.length === 0}
            >
              Generate LaTeX Literature Review
            </Button>

            {loading && (
              <Box sx={{ textAlign: 'center', py: 10 }}>
                <CircularProgress />
                <Typography sx={{ mt: 2 }}>Synthesizing papers and drafting LaTeX...</Typography>
              </Box>
            )}

            {latexResult && (
              <Box sx={{ mt: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6">Generated Content (LaTeX)</Typography>
                  <IconButton onClick={() => navigator.clipboard.writeText(latexResult)}>
                    <CopyIcon />
                  </IconButton>
                </Box>
                <Paper sx={{ p: 2, bgcolor: 'grey.900', color: 'common.white', fontFamily: 'monospace', maxHeight: '50vh', overflow: 'auto' }}>
                  <pre style={{ whiteSpace: 'pre-wrap' }}>{latexResult}</pre>
                </Paper>
              </Box>
            )}
          </Grid>
        </Grid>
      ) : (
        <Box sx={{ maxWidth: 800, mx: 'auto' }}>
          <Typography variant="h6" gutterBottom>Formula Contextual Explainer</Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Paste LaTeX Formula"
            placeholder="\mathcal{L} = -\sum_{i=1}^N y_i \log(\hat{y}_i)"
            value={formula}
            onChange={(e) => setFormula(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button 
            variant="contained" 
            fullWidth 
            onClick={handleDecodeFormula}
            disabled={loading || !formula}
          >
            Explain Intuition
          </Button>

          {loading && <CircularProgress sx={{ display: 'block', mx: 'auto', mt: 4 }} />}

          {formulaExplanation && (
            <Card sx={{ mt: 4, bgcolor: 'primary.50' }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom>Intuition & Breakdown</Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{formulaExplanation}</Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
};

export default Drafting;
