import React, { useState } from 'react';
import { Box, Typography, Paper, Tabs, Tab, TextField, Button, Chip, CircularProgress, Card, CardContent, Stack, Grid, Select, MenuItem, FormControl, InputLabel, Snackbar, Alert, Divider } from '@mui/material';
import { Code as CodeIcon, Functions as MathIcon, CheckCircle as CheckIcon, Science as LabIcon, Description as DocIcon, BarChart as ChartIcon, RateReview as ReviewIcon, EmojiObjects as PatentIcon, AccountBalance as GrantIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const TOOLS = [
  { id: 'code', label: 'Code Gen', icon: <CodeIcon /> },
  { id: 'math', label: 'Expression Check', icon: <MathIcon /> },
  { id: 'data', label: 'Data Check', icon: <CheckIcon /> },
  { id: 'experiment', label: 'Experiment', icon: <LabIcon /> },
  { id: 'format', label: 'Format', icon: <DocIcon /> },
  { id: 'figure', label: 'Figure Code', icon: <ChartIcon /> },
  { id: 'review', label: 'Review Response', icon: <ReviewIcon /> },
  { id: 'patent', label: 'Patent', icon: <PatentIcon /> },
  { id: 'grant', label: 'Grant', icon: <GrantIcon /> },
];

const DownstreamTools = () => {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [notify, setNotify] = useState({ open: false, msg: '' });
  const [formData, setFormData] = useState({});

  const handleField = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  const handleSubmit = async () => {
    setLoading(true); setResult(null);
    try {
      const tool = TOOLS[tab];
      let endpoint = '', params = {};
      switch (tool.id) {
        case 'code': endpoint = '/downstream/generate-code'; params = { paper_text: formData.text, language: formData.language || 'python', task: formData.task || 'implement main algorithm' }; break;
        case 'math': endpoint = '/downstream/validate-expression'; params = { expression: formData.expression, context: formData.context || '' }; break;
        case 'data': endpoint = '/downstream/check-data'; params = { data_claims: formData.claims }; break;
        case 'experiment': endpoint = '/downstream/design-experiment'; params = { methodology: formData.methodology }; break;
        case 'format': endpoint = '/downstream/format-manuscript'; params = { content: formData.content, template: formData.template || 'arxiv', title: formData.title || '' }; break;
        case 'figure': endpoint = '/downstream/generate-figure'; params = { data_description: formData.data_desc, chart_type: formData.chart_type || 'matplotlib', style: formData.style || 'publication' }; break;
        case 'review': endpoint = '/downstream/review-response'; params = { reviewer_comments: formData.comments, paper_summary: formData.summary || '', tone: formData.tone || 'professional' }; break;
        case 'patent': endpoint = '/downstream/patent-ideas'; params = { paper_text: formData.text }; break;
        case 'grant': endpoint = '/downstream/grant-proposal'; params = { topic: formData.topic, funding_agency: formData.agency || 'NSF' }; break;
      }
      const res = await api.post(endpoint, params, { headers: { 'Content-Type': 'application/json' } });
      setResult(res.data);
    } catch (e) { setNotify({ open: true, msg: 'Tool failed', severity: 'error' }); }
    finally { setLoading(false); }
  };

  const copyResult = () => {
    const text = result?.code || result?.analysis || result?.proposal || result?.responses || result?.design || result?.latex || JSON.stringify(result, null, 2);
    navigator.clipboard.writeText(text);
    setNotify({ open: true, msg: 'Copied!' });
  };

  const renderInput = () => {
    switch (TOOLS[tab].id) {
      case 'code': return (
        <>
          <TextField fullWidth multiline rows={6} label="Paper text / methodology" value={formData.text || ''} onChange={e => handleField('text', e.target.value)} sx={{ mb: 2 }} />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={4}><FormControl fullWidth size="small"><InputLabel>Language</InputLabel><Select value={formData.language || 'python'} onChange={e => handleField('language', e.target.value)} label="Language"><MenuItem value="python">Python</MenuItem><MenuItem value="julia">Julia</MenuItem><MenuItem value="r">R</MenuItem><MenuItem value="matlab">MATLAB</MenuItem></Select></FormControl></Grid>
            <Grid item xs={8}><TextField fullWidth size="small" label="Task" value={formData.task || ''} onChange={e => handleField('task', e.target.value)} /></Grid>
          </Grid>
        </>
      );
      case 'math': return (<TextField fullWidth multiline rows={4} label="Mathematical expression / derivation" value={formData.expression || ''} onChange={e => handleField('expression', e.target.value)} sx={{ mb: 2 }} />);
      case 'data': return (<TextField fullWidth multiline rows={4} label="Data claims to verify" value={formData.claims || ''} onChange={e => handleField('claims', e.target.value)} sx={{ mb: 2 }} />);
      case 'experiment': return (<TextField fullWidth multiline rows={5} label="Methodology description" value={formData.methodology || ''} onChange={e => handleField('methodology', e.target.value)} sx={{ mb: 2 }} />);
      case 'format': return (<><TextField fullWidth multiline rows={5} label="Manuscript content" value={formData.content || ''} onChange={e => handleField('content', e.target.value)} sx={{ mb: 2 }} /><FormControl fullWidth size="small" sx={{ mb: 2 }}><InputLabel>Template</InputLabel><Select value={formData.template || 'arxiv'} onChange={e => handleField('template', e.target.value)} label="Template"><MenuItem value="arxiv">arXiv</MenuItem><MenuItem value="neurips">NeurIPS</MenuItem><MenuItem value="icml">ICML</MenuItem><MenuItem value="acl">ACL</MenuItem><MenuItem value="ieee">IEEE</MenuItem></Select></FormControl></>);
      case 'figure': return (<><TextField fullWidth multiline rows={4} label="Data / chart description" value={formData.data_desc || ''} onChange={e => handleField('data_desc', e.target.value)} sx={{ mb: 2 }} /><Grid container spacing={2}><Grid item xs={6}><FormControl fullWidth size="small"><InputLabel>Chart Type</InputLabel><Select value={formData.chart_type || 'matplotlib'} onChange={e => handleField('chart_type', e.target.value)} label="Chart Type"><MenuItem value="matplotlib">Matplotlib</MenuItem><MenuItem value="seaborn">Seaborn</MenuItem><MenuItem value="plotly">Plotly</MenuItem></Select></FormControl></Grid><Grid item xs={6}><FormControl fullWidth size="small"><InputLabel>Style</InputLabel><Select value={formData.style || 'publication'} onChange={e => handleField('style', e.target.value)} label="Style"><MenuItem value="publication">Publication</MenuItem><MenuItem value="presentation">Presentation</MenuItem><MenuItem value="poster">Poster</MenuItem></Select></FormControl></Grid></Grid></>);
      case 'review': return (<><TextField fullWidth multiline rows={5} label="Reviewer comments" value={formData.comments || ''} onChange={e => handleField('comments', e.target.value)} sx={{ mb: 2 }} /><FormControl fullWidth size="small" sx={{ mb: 2 }}><InputLabel>Tone</InputLabel><Select value={formData.tone || 'professional'} onChange={e => handleField('tone', e.target.value)} label="Tone"><MenuItem value="professional">Professional</MenuItem><MenuItem value="detailed">Detailed</MenuItem><MenuItem value="concise">Concise</MenuItem></Select></FormControl></>);
      case 'patent': return (<TextField fullWidth multiline rows={5} label="Paper text" value={formData.text || ''} onChange={e => handleField('text', e.target.value)} sx={{ mb: 2 }} />);
      case 'grant': return (<><TextField fullWidth label="Research topic" value={formData.topic || ''} onChange={e => handleField('topic', e.target.value)} sx={{ mb: 2 }} /><FormControl fullWidth size="small"><InputLabel>Funding Agency</InputLabel><Select value={formData.agency || 'NSF'} onChange={e => handleField('agency', e.target.value)} label="Funding Agency"><MenuItem value="NSF">NSF</MenuItem><MenuItem value="NIH">NIH</MenuItem><MenuItem value="ERC">ERC</MenuItem><MenuItem value="horizon">Horizon Europe</MenuItem></Select></FormControl></>);
      default: return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>📐 Research Toolkit</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        From papers to actions: generate code, validate math, check data, design experiments, format manuscripts, respond to reviewers.
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} variant="scrollable" scrollButtons="auto" sx={{ mb: 2 }}>
        {TOOLS.map((t, i) => <Tab key={i} icon={t.icon} label={t.label} iconPosition="start" />)}
      </Tabs>

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>{TOOLS[tab].label}</Typography>
            {renderInput()}
            <Button variant="contained" fullWidth onClick={handleSubmit} disabled={loading}>
              {loading ? <CircularProgress size={20} /> : `Run ${TOOLS[tab].label}`}
            </Button>
          </Paper>
        </Grid>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2.5, minHeight: 400 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Output</Typography>
              {result && <Button size="small" onClick={copyResult}>Copy</Button>}
            </Box>
            {!result && !loading && <Typography color="text.secondary" sx={{ fontStyle: 'italic', textAlign: 'center', py: 8 }}>Run a tool to see output.</Typography>}
            {loading && <Box textAlign="center" py={8}><CircularProgress /></Box>}
            {result && (
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: result?.code ? 'monospace' : 'inherit', fontSize: result?.code ? 13 : 'inherit' }}>
                <ReactMarkdown>{result?.code || result?.analysis || result?.proposal || result?.responses || result?.design || result?.latex || result?.proposal || JSON.stringify(result, null, 2)}</ReactMarkdown>
              </Typography>
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

export default DownstreamTools;
