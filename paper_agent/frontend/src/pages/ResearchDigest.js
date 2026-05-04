import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Paper, Card, CardContent,
  CircularProgress, Chip, Divider, Grid, Alert, Tabs, Tab,
  IconButton, Stack,
} from '@mui/material';
import {
  AutoAwesome as AIIcon, Download as DownloadIcon,
  Refresh as RefreshIcon, Article as ArticleIcon,
  CalendarMonth as CalendarIcon, History as HistoryIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const ResearchDigest = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [digests, setDigests] = useState([]);
  const [currentDigest, setCurrentDigest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { fetchDigests(); }, []);

  const fetchDigests = async () => {
    setLoading(true);
    try {
      const res = await api.get('/digest/');
      setDigests(res.data || []);
    } catch (e) { setError('Failed to load digests'); }
    finally { setLoading(false); }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await api.post('/digest/generate', null, { params: { days: 7 } });
      setCurrentDigest(res.data);
      setTab(0);
      fetchDigests();
    } catch (e) {
      setError(e.response?.data?.detail || 'Generation failed. Add more documents first.');
    }
    finally { setGenerating(false); }
  };

  const handleViewDigest = async (digestId) => {
    try {
      const res = await api.get(`/digest/${digestId}`);
      setCurrentDigest(res.data);
      setTab(0);
    } catch (e) { console.error(e); }
  };

  const handleExportMarkdown = () => {
    if (!currentDigest) return;
    let md = `# ${currentDigest.title}\n\n`;
    md += `${currentDigest.summary}\n\n---\n\n`;
    for (const section of (currentDigest.sections || [])) {
      md += `## ${section.title}\n\n${section.content}\n\n---\n\n`;
    }
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `digest-${Date.now()}.md`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          <AIIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Research Digest
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {currentDigest && (
            <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportMarkdown}>Export</Button>
          )}
          <Button variant="contained" onClick={handleGenerate} disabled={generating}>
            {generating ? <><CircularProgress size={16} sx={{ mr: 1 }} />Generating...</> : 'Generate Now'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="warning" sx={{ mb: 2 }}>{error}</Alert>}

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Current Digest" />
        <Tab icon={<HistoryIcon />} label="History" />
      </Tabs>

      {tab === 0 && (
        currentDigest ? (
          <Box>
            <Card variant="outlined" sx={{ mb: 3, bgcolor: 'primary.dark', color: 'white' }}>
              <CardContent>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{currentDigest.title}</Typography>
                <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>{currentDigest.summary}</Typography>
                <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                  <Chip icon={<CalendarIcon />} label={`${currentDigest.period_start?.slice(0, 10) || ''} to ${currentDigest.period_end?.slice(0, 10) || ''}`} size="small" variant="outlined" sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)' }} />
                  <Chip icon={<ArticleIcon />} label={`${currentDigest.document_ids?.length || 0} papers`} size="small" variant="outlined" sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)' }} />
                </Stack>
              </CardContent>
            </Card>

            {(currentDigest.sections || []).map((section, i) => (
              <Card key={i} variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>{section.title}</Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box className="markdown-body">
                    <ReactMarkdown>{section.content}</ReactMarkdown>
                  </Box>
                </CardContent>
              </Card>
            ))}

            {currentDigest.document_ids?.length > 0 && (
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>Papers in this Digest</Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {currentDigest.document_ids.map((did, i) => (
                      <Chip key={i} label={did.slice(0, 8)} component="a" href={`#/documents/${did}`}
                        onClick={() => navigate(`/documents/${did}`)} variant="outlined" size="small" sx={{ cursor: 'pointer' }} />
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Box>
        ) : (
          <Box textAlign="center" py={10} sx={{ opacity: 0.6 }}>
            <AIIcon sx={{ fontSize: 80, mb: 2, color: 'primary.light' }} />
            <Typography variant="h6" color="text.secondary">No digest generated yet</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Generate a research digest to get an AI-powered overview of your library.
            </Typography>
            <Button variant="contained" sx={{ mt: 2 }} onClick={handleGenerate} disabled={generating}>
              {generating ? 'Generating...' : 'Generate Your First Digest'}
            </Button>
          </Box>
        )
      )}

      {tab === 1 && (
        loading ? <Box textAlign="center" py={5}><CircularProgress /></Box> : (
          <Grid container spacing={2}>
            {digests.length === 0 ? (
              <Grid item xs={12}><Typography color="text.secondary">No digests yet. Generate one first.</Typography></Grid>
            ) : digests.map((d, i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Card variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => handleViewDigest(d.id)}>
                  <CardContent>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{d.title || 'Research Digest'}</Typography>
                    <Typography variant="caption" color="text.secondary" display="block">{d.summary?.slice(0, 100)}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''} · {d.document_ids?.length || 0} papers
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )
      )}
    </Box>
  );
};

export default ResearchDigest;
