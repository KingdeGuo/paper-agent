import React, { useState } from 'react';
import { Box, Typography, TextField, Button, Paper, Chip, CircularProgress, Card, CardContent, Stack, Divider, Grid, Alert, Snackbar } from '@mui/material';
import { AutoAwesome as AIIcon, Hub as GraphIcon, TravelExplore as ExploreIcon, ContentCopy as CopyIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const GraphRAGPage = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [documentId, setDocumentId] = useState('');
  const [exploreResult, setExploreResult] = useState(null);
  const [exploreLoading, setExploreLoading] = useState(false);
  const [tab, setTab] = useState('ask');
  const [notify, setNotify] = useState({ open: false, msg: '' });

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true); setResult(null);
    try {
      const res = await api.post('/graphrag/ask', null, { params: { question: question.trim(), max_depth: 2 } });
      setResult(res.data);
    } catch (e) { setNotify({ open: true, msg: 'GraphRAG query failed', severity: 'error' }); }
    finally { setLoading(false); }
  };

  const handleExplore = async () => {
    if (!documentId.trim()) return;
    setExploreLoading(true); setExploreResult(null);
    try {
      const res = await api.post('/graphrag/explore', null, { params: { document_id: documentId.trim(), depth: 2 } });
      setExploreResult(res.data);
    } catch (e) { setNotify({ open: true, msg: 'Explore failed', severity: 'error' }); }
    finally { setExploreLoading(false); }
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>
        <GraphIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'secondary.main' }} />
        GraphRAG — Graph-Based Research Intelligence
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Combines knowledge graph traversal with vector search for deeper, context-aware retrieval.
        Traverses citation links and semantic relationships to find connected research.
      </Typography>

      <Grid container spacing={3}>
        {/* Ask */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2.5, mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Ask with GraphRAG</Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <TextField fullWidth size="small" placeholder="Ask a research question... (e.g., 'What are the main approaches to efficient transformers?')"
                value={question} onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAsk()} />
              <Button variant="contained" onClick={handleAsk} disabled={loading || !question.trim()}>
                {loading ? <CircularProgress size={20} /> : 'Ask'}
              </Button>
            </Box>

            {loading && <Box textAlign="center" py={4}><CircularProgress /><Typography variant="body2" mt={1}>Traversing citation graph...</Typography></Box>}

            {result && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Found {result.total_sources} sources from {result.graph_nodes_explored} graph nodes explored
                </Alert>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, mb: 2 }}>
                  <ReactMarkdown>{result.answer}</ReactMarkdown>
                </Typography>

                {result.sources?.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>Sources:</Typography>
                    <Stack spacing={0.5}>
                      {result.sources.map((s, i) => (
                        <Chip key={i} label={`${s.title?.slice(0, 50)} (score: ${s.relevance_score?.toFixed(3)})`}
                          size="small" variant={s.in_graph ? 'filled' : 'outlined'} color={s.in_graph ? 'secondary' : 'default'}
                          onClick={() => window.open(`/documents/${s.document_id}`, '_blank')} sx={{ cursor: 'pointer', justifyContent: 'flex-start' }} />
                      ))}
                    </Stack>
                  </>
                )}

                {result.graph_traversed?.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>Graph Traversal Path:</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {result.graph_traversed.map(n => `${n.title} (depth ${n.depth})`).join(' → ')}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Explore */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2.5, mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
              <ExploreIcon sx={{ mr: 0.5, verticalAlign: 'middle' }} /> Explore Paper Neighborhood
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <TextField fullWidth size="small" placeholder="Document ID" value={documentId} onChange={e => setDocumentId(e.target.value)} />
              <Button variant="outlined" onClick={handleExplore} disabled={exploreLoading || !documentId.trim()}>
                {exploreLoading ? <CircularProgress size={20} /> : 'Explore'}
              </Button>
            </Box>

            {exploreResult && (
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{exploreResult.center_paper?.title}</Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                  {exploreResult.direct_count} direct · {exploreResult.indirect_count} indirect connections
                </Typography>
                <Divider sx={{ my: 1 }} />
                {exploreResult.direct_connections?.map((n, i) => (
                  <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.3 }}>
                    <Typography variant="caption">{n.title?.slice(0, 40)}</Typography>
                    <Chip label="direct" size="small" variant="outlined" />
                  </Box>
                ))}
              </Box>
            )}
          </Paper>

          {/* Stats card */}
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>How GraphRAG Works</Typography>
              <Stack spacing={0.5}>
                <Typography variant="caption">1️⃣ Vector search finds seed papers</Typography>
                <Typography variant="caption">2️⃣ Graph traversal follows citation + keyword links</Typography>
                <Typography variant="caption">3️⃣ Scores combine vector similarity + graph proximity</Typography>
                <Typography variant="caption">4️⃣ LLM synthesizes answer with source attribution</Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar open={notify.open} autoHideDuration={4000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity || 'info'}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default GraphRAGPage;
