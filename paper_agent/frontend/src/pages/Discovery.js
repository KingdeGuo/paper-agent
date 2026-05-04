import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Button, Paper, Grid, Card, CardContent, 
  Chip, Divider, CircularProgress, Alert, Stepper, Step, StepLabel,
  List, ListItem, ListItemText, ListItemIcon
} from '@mui/material';
import { 
  Science as ScienceIcon, 
  Compare as CompareIcon, 
  Lightbulb as InsightIcon,
  Timeline as ThreadIcon,
  Warning as WarningIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import api from '../services/api';
import { useLocation } from 'react-router-dom';

const Discovery = () => {
  const location = useLocation();
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [discoveryType, setDiscoveryType] = useState(null); // 'contradiction' or 'gap'
  const [results, setResults] = useState(null);
  const [allDocs, setAllDocs] = useState([]);

  useEffect(() => {
    fetchDocs();
  }, []);

  const fetchDocs = async () => {
    try {
      const response = await api.get('/documents');
      setAllDocs(response.data);
      
      // Auto-select if passed from documents page
      if (location.state?.selectedIds) {
        const preselected = response.data.filter(d => location.state.selectedIds.includes(d.id));
        setSelectedDocs(preselected);
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  };

  const handleDiscovery = async (type) => {
    if (selectedDocs.length < 2) {
      alert("Please select at least 2 papers for synthesis.");
      return;
    }
    
    setLoading(true);
    setDiscoveryType(type);
    setResults(null);
    
    try {
      const endpoint = type === 'contradiction' ? '/discovery/contradictions' : '/discovery/gaps';
      const response = await api.post(endpoint, selectedDocs.map(d => d.id));
      setResults(response.data);
    } catch (err) {
      console.error("Discovery failed", err);
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

  const handleExport = (res) => {
    const blob = new Blob([res.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `distilled_${res.type}_${new Date().getTime()}.md`;
    a.click();
  };

  const handleSaveToNotebook = async (res) => {
    try {
      const nbRes = await api.get('/notebooks');
      if (nbRes.data.length === 0) {
        alert("Please create a notebook first.");
        return;
      }
      
      const entry = {
        notebook_id: nbRes.data[0].id,
        type: res.type,
        content: res.content,
        metadata: { source: 'discovery', docs: selectedDocs.map(d => d.id) }
      };
      
      await api.post('/notebooks/entries', entry);
      alert("Saved to " + nbRes.data[0].title);
    } catch (err) {
      console.error("Save failed", err);
    }
  };

  const handleStartThread = async (res) => {
    try {
      const threadRes = await api.post('/discovery/threads', {
        goal: `Deep dive into: ${res.content.substring(0, 100)}...`,
        doc_ids: selectedDocs.map(d => d.id)
      });
      alert("Research Thread started! ID: " + threadRes.data.id);
    } catch (err) {
      console.error("Thread start failed", err);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
        <ScienceIcon sx={{ mr: 2, color: 'primary.main' }} />
        Knowledge Distillery
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Deep semantic synthesis: Connect dots across multiple papers, find contradictions, and generate new research hypotheses.
      </Typography>

      <Grid container spacing={3}>
        {/* Paper Selection */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '70vh', overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>Select Papers ({selectedDocs.length})</Typography>
            <List>
              {allDocs.map((doc) => (
                <ListItem 
                  button 
                  key={doc.id} 
                  onClick={() => toggleDoc(doc)}
                  selected={selectedDocs.find(d => d.id === doc.id)}
                  sx={{ mb: 1, borderRadius: 1 }}
                >
                  <ListItemText 
                    primary={doc.title} 
                    secondary={`${doc.year || 'N/A'} - ${doc.authors?.join(', ') || 'Unknown'}`}
                    primaryTypographyProps={{ variant: 'body2', fontWeight: selectedDocs.find(d => d.id === doc.id) ? 'bold' : 'normal' }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Action & Results */}
        <Grid item xs={12} md={8}>
          <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
            <Button 
              variant="contained" 
              startIcon={<WarningIcon />}
              onClick={() => handleDiscovery('contradiction')}
              disabled={loading || selectedDocs.length < 2}
              color="warning"
            >
              Find Contradictions
            </Button>
            <Button 
              variant="contained" 
              startIcon={<InsightIcon />}
              onClick={() => handleDiscovery('gap')}
              disabled={loading || selectedDocs.length < 2}
              color="secondary"
            >
              Generate Hypotheses
            </Button>
          </Box>

          {loading && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 10 }}>
              <CircularProgress size={60} />
              <Typography sx={{ mt: 2 }}>AI is distilling knowledge from {selectedDocs.length} papers...</Typography>
            </Box>
          )}

          {!loading && results && (
            <Box>
              <Alert severity="info" sx={{ mb: 3 }}>
                Synthesis complete. Based on the {selectedDocs.length} selected documents.
              </Alert>
              
              {results.map((res, idx) => (
                <Card key={idx} sx={{ mb: 3, borderLeft: '5px solid', borderColor: discoveryType === 'contradiction' ? 'warning.main' : 'secondary.main' }}>
                  <CardContent>
                    <Typography variant="h6" color={discoveryType === 'contradiction' ? 'warning.main' : 'secondary.main'} gutterBottom>
                      {res.type === 'contradiction' ? 'Potential Conflict Detected' : 'New Research Hypothesis'}
                    </Typography>
                    <Box sx={{ whiteSpace: 'pre-wrap', bgcolor: 'grey.50', p: 2, borderRadius: 1, fontFamily: 'monospace' }}>
                      {res.content}
                    </Box>
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                      <Button size="small" startIcon={<DownloadIcon />} onClick={() => handleExport(res)}>Export MD</Button>
                      <Button size="small" startIcon={<ThreadIcon />} onClick={() => handleStartThread(res)}>Start Thread</Button>
                      <Button size="small" variant="outlined" onClick={() => handleSaveToNotebook(res)}>Save to Notebook</Button>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}

          {!loading && !results && (
            <Box sx={{ textAlign: 'center', py: 10, opacity: 0.5 }}>
              <CompareIcon sx={{ fontSize: 80, mb: 2 }} />
              <Typography variant="h6">Select at least 2 papers to start distillation</Typography>
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default Discovery;
