import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Button, Chip, CircularProgress, Card, CardContent, TextField, Stack, Grid, Divider, Select, MenuItem, FormControl, InputLabel, Alert, Snackbar, Tabs, Tab } from '@mui/material';
import { AutoAwesome as AIIcon, SmartToy as AgentIcon, Hub as GraphIcon, Psychology as BrainIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const AgentConsole = () => {
  const [agents, setAgents] = useState([]);
  const [tab, setTab] = useState(0);
  const [topic, setTopic] = useState('');
  const [sectionType, setSectionType] = useState('related_work');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [notify, setNotify] = useState({ open: false, msg: '' });

  useEffect(() => { fetchAgents(); }, []);

  const fetchAgents = async () => {
    try { const res = await api.get('/agents'); setAgents(res.data?.agents || []); } catch (e) {}
  };

  const handleLiteratureReview = async () => {
    if (!topic.trim()) return;
    setLoading(true); setResult(null);
    try {
      const res = await api.post('/agents/literature-review', null, {
        params: { topic: topic.trim(), max_papers: 10, include_graph: true }
      });
      setResult({ type: 'literature_review', data: res.data });
    } catch (e) { setNotify({ open: true, msg: 'Agent task failed', severity: 'error' }); }
    finally { setLoading(false); }
  };

  const handleGapAnalysis = async () => {
    if (!topic.trim()) return;
    setLoading(true); setResult(null);
    try {
      const res = await api.post('/agents/gap-analysis', null, {
        params: { topic: topic.trim(), max_papers: 15 }
      });
      setResult({ type: 'gap_analysis', data: res.data });
    } catch (e) { setNotify({ open: true, msg: 'Gap analysis failed', severity: 'error' }); }
    finally { setLoading(false); }
  };

  const handleWriteSection = async () => {
    if (!topic.trim()) return;
    setLoading(true); setResult(null);
    try {
      const res = await api.post('/agents/write-section', null, {
        params: { section_type: sectionType, topic: topic.trim(), style: 'academic', max_papers: 8 }
      });
      setResult({ type: 'writing', data: res.data });
    } catch (e) { setNotify({ open: true, msg: 'Writing task failed', severity: 'error' }); }
    finally { setLoading(false); }
  };

  const copyResult = () => {
    const text = result?.data?.synthesis || result?.data?.analysis || result?.data?.content || '';
    navigator.clipboard.writeText(text);
    setNotify({ open: true, msg: 'Copied!' });
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>
        <AgentIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'secondary.main' }} />
        Research Agent Console
      </Typography>

      {/* Agent Status */}
      <Stack direction="row" spacing={1} sx={{ mb: 3 }} alignItems="center">
        <Typography variant="body2" color="text.secondary">Available Agents:</Typography>
        {agents.map((a, i) => (
          <Chip key={i} icon={<AgentIcon />} label={`${a.name} (${a.capabilities?.length || 0} caps)`} size="small" variant="outlined" color="secondary" />
        ))}
      </Stack>

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Task Configuration</Typography>

            <TextField fullWidth size="small" label="Research Topic" placeholder="e.g., Efficient transformer architectures"
              value={topic} onChange={e => setTopic(e.target.value)} sx={{ mb: 2 }} />

            <FormControl fullWidth size="small" sx={{ mb: 2 }}>
              <InputLabel>Section Type (Writing Agent)</InputLabel>
              <Select value={sectionType} onChange={e => setSectionType(e.target.value)} label="Section Type">
                <MenuItem value="related_work">Related Work</MenuItem>
                <MenuItem value="abstract">Abstract</MenuItem>
                <MenuItem value="introduction">Introduction</MenuItem>
                <MenuItem value="discussion">Discussion</MenuItem>
              </Select>
            </FormControl>

            <Stack spacing={1}>
              <Button variant="contained" startIcon={<GraphIcon />} onClick={handleLiteratureReview}
                disabled={loading || !topic.trim()}>
                {loading && tab === 0 ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
                Literature Review
              </Button>
              <Button variant="contained" color="secondary" startIcon={<BrainIcon />} onClick={handleGapAnalysis}
                disabled={loading || !topic.trim()}>
                Gap Analysis
              </Button>
              <Button variant="outlined" startIcon={<AIIcon />} onClick={handleWriteSection}
                disabled={loading || !topic.trim()}>
                Write {sectionType.replace('_', ' ')}
              </Button>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2.5, minHeight: 400 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Results</Typography>
              {result && <Button size="small" onClick={copyResult}>Copy</Button>}
            </Box>

            {!result && !loading && (
              <Box textAlign="center" py={8} sx={{ opacity: 0.5 }}>
                <AgentIcon sx={{ fontSize: 60, mb: 2 }} />
                <Typography>Configure a task and run an agent</Typography>
              </Box>
            )}

            {loading && <Box textAlign="center" py={6}><CircularProgress /><Typography variant="body2" mt={1}>Agent working...</Typography></Box>}

            {result && (
              <Box>
                {result.data?.papers_reviewed !== undefined && (
                  <Alert severity="success" sx={{ mb: 2 }}>Reviewed {result.data.papers_reviewed} papers</Alert>
                )}
                {result.data?.papers_analyzed !== undefined && (
                  <Alert severity="info" sx={{ mb: 2 }}>Analyzed {result.data.papers_analyzed} papers</Alert>
                )}
                {result.data?.papers_cited !== undefined && (
                  <Alert severity="info" sx={{ mb: 2 }}>Cited {result.data.papers_cited} papers</Alert>
                )}

                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                  <ReactMarkdown>
                    {result.data?.synthesis || result.data?.analysis || result.data?.content || JSON.stringify(result.data, null, 2)}
                  </ReactMarkdown>
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Snackbar open={notify.open} autoHideDuration={3000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity || 'info'}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentConsole;
