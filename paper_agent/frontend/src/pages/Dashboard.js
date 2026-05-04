import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Paper, Card, CardContent, Grid, Chip, Button, TextField, Stack, Divider, IconButton, LinearProgress, Tooltip, Badge } from '@mui/material';
import {
  Search as SearchIcon, Description as DocIcon, AutoAwesome as AIIcon, Hub as GraphIcon,
  SmartToy as AgentIcon, Science as DiscoveryIcon, HistoryEdu as DraftIcon,
  MenuBook as ReadingIcon, Book as NotebookIcon, CollectionsBookmark as CitationIcon,
  AccountTree as TreeIcon, Psychology as FlashIcon, Event as ConfIcon,
  EditNote as JournalIcon, Chat as ChatIcon, BarChart as AnalyticsIcon,
  FormatQuote as QuoteIcon, Image as ImageIcon, Code as CodeIcon,
  Functions as MathIcon, CheckCircle as CheckIcon, Science as LabIcon,
  EmojiObjects as PatentIcon, AccountBalance as GrantIcon, RateReview as ReviewIcon,
  School as OnboardIcon, Dashboard as DashIcon, Settings as SettingsIcon,
} from '@mui/icons-material';
import api from '../services/api';

// ─── Feature Registry — drives both navigation and launchpad ───
const FEATURES = [
  { category: '📖 Reading', items: [
    { path: '/documents', icon: <DocIcon />, label: 'Library', desc: 'Upload, manage, search papers', color: '#2563eb' },
    { path: '/reading', icon: <ReadingIcon />, label: 'Reading List', desc: 'Track what to read and what you\'ve read', color: '#16a34a' },
    { path: '/flashcards', icon: <FlashIcon />, label: 'Flashcards', desc: 'Spaced repetition for paper recall', color: '#7c3aed' },
    { path: '/journal', icon: <JournalIcon />, label: 'Journal', desc: 'Daily research diary', color: '#0891b2' },
  ]},
  { category: '🔍 Discovery', items: [
    { path: '/search', icon: <SearchIcon />, label: 'Search', desc: 'Local + arXiv + multi-source search', color: '#2563eb' },
    { path: '/ask', icon: <AIIcon />, label: 'Ask AI', desc: 'Natural language questions about your library', color: '#7c3aed' },
    { path: '/research-chat', icon: <ChatIcon />, label: 'Research Chat', desc: 'Persistent context-aware conversations', color: '#0891b2' },
    { path: '/graphrag', icon: <GraphIcon />, label: 'GraphRAG', desc: 'Graph-based research intelligence', color: '#ea580c' },
    { path: '/citation-chain', icon: <QuoteIcon />, label: 'Citation Chain', desc: 'Follow citations forward and backward', color: '#d946ef' },
  ]},
  { category: '🧠 Analysis', items: [
    { path: '/knowledge', icon: <TreeIcon />, label: 'Knowledge Graph', desc: 'Visual paper relationships', color: '#2563eb' },
    { path: '/literature-tree', icon: <TreeIcon />, label: 'Literature Tree', desc: 'Organize papers by topic', color: '#16a34a' },
    { path: '/discovery', icon: <DiscoveryIcon />, label: 'Discovery', desc: 'Contradictions, gaps, trends', color: '#7c3aed' },
    { path: '/agents', icon: <AgentIcon />, label: 'AI Agents', desc: 'Autonomous research assistants', color: '#ea580c' },
    { path: '/analytics', icon: <AnalyticsIcon />, label: 'Analytics', desc: 'Reading habits and research trends', color: '#0891b2' },
  ]},
  { category: '✍️ Writing', items: [
    { path: '/drafting', icon: <DraftIcon />, label: 'Drafting', desc: 'Related work, formula decoding', color: '#2563eb' },
    { path: '/writing', icon: <CodeIcon />, label: 'Writing Tools', desc: 'Overleaf, LaTeX, BibTeX export', color: '#16a34a' },
    { path: '/citations', icon: <CitationIcon />, label: 'Citations', desc: 'BibTeX, DOI lookup, bibliography', color: '#7c3aed' },
    { path: '/research-tools', icon: <LabIcon />, label: 'Research Toolkit', desc: 'Code gen, expr validation, figure gen', color: '#d946ef' },
  ]},
  { category: '📊 Publishing', items: [
    { path: '/conferences', icon: <ConfIcon />, label: 'Conferences', desc: 'Track CFP deadlines', color: '#2563eb' },
    { path: '/figures', icon: <ImageIcon />, label: 'Figures', desc: 'Extracted figures and tables', color: '#16a34a' },
    { path: '/digest', icon: <AnalyticsIcon />, label: 'Digest', desc: 'Weekly research digests', color: '#0891b2' },
    { path: '/notebooks', icon: <NotebookIcon />, label: 'Notebooks', desc: 'Research notes and threads', color: '#7c3aed' },
  ]},
  { category: '👥 Collaborate', items: [
    { path: '/zotero', icon: <DocIcon />, label: 'Zotero', desc: 'Import from Zotero library', color: '#2563eb' },
    { path: '/notebooks', icon: <NotebookIcon />, label: 'Collections', desc: 'Shared paper collections', color: '#16a34a' },
  ]},
];

const Dashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get('/stats/full').then(r => setStats(r.data)).catch(() => {});
  }, []);

  const docs = stats?.documents || {};
  const reading = stats?.reading || {};
  const filteredCategory = FEATURES.map(cat => ({
    ...cat,
    items: cat.items.filter(f =>
      f.label.toLowerCase().includes(search.toLowerCase()) ||
      f.desc.toLowerCase().includes(search.toLowerCase())
    ),
  })).filter(cat => cat.items.length > 0);

  return (
    <Box>
      {/* Search */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 3 }}>
        <TextField fullWidth variant="outlined" placeholder="Search features... (e.g., 'flashcards', 'citation', 'graph')"
          value={search} onChange={e => setSearch(e.target.value)}
          InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} /> }} />
      </Paper>

      {/* Stats Bar */}
      {stats && (
        <Paper sx={{ p: 2, mb: 3, borderRadius: 2 }}>
          <Grid container spacing={2} textAlign="center">
            <Grid item xs={3} sm={2}>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>{docs.total || 0}</Typography>
              <Typography variant="caption">Papers</Typography>
            </Grid>
            <Grid item xs={3} sm={2}>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'success.main' }}>{reading.read || 0}</Typography>
              <Typography variant="caption">Read</Typography>
            </Grid>
            <Grid item xs={3} sm={2}>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'warning.main' }}>{reading.to_read || 0}</Typography>
              <Typography variant="caption">To Read</Typography>
            </Grid>
            <Grid item xs={3} sm={2}>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'info.main' }}>{reading.reading || 0}</Typography>
              <Typography variant="caption">Reading</Typography>
            </Grid>
            <Grid item xs={6} sm={2}>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'secondary.main' }}>{Math.round(reading.avg_progress * 100) || 0}%</Typography>
              <Typography variant="caption">Progress</Typography>
            </Grid>
            <Grid item xs={6} sm={2}>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>73</Typography>
              <Typography variant="caption">API Modules</Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Feature Launchpad */}
      {filteredCategory.map((cat, ci) => (
        <Box key={ci} sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
            {cat.category}
            <Chip label={`${cat.items.length}`} size="small" variant="outlined" />
          </Typography>
          <Grid container spacing={1.5}>
            {cat.items.map((f, fi) => (
              <Grid item xs={6} sm={4} md={3} lg={2} key={fi}>
                <Card sx={{
                  cursor: 'pointer', '&:hover': { transform: 'translateY(-2px)', boxShadow: 4, transition: '0.2s' },
                  borderLeft: 3, borderLeftColor: f.color,
                }} onClick={() => navigate(f.path)}>
                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Box sx={{ color: f.color }}>{f.icon}</Box>
                      <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.85rem' }}>{f.label}</Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', lineHeight: 1.2, display: 'block' }}>
                      {f.desc}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      ))}
    </Box>
  );
};

export default Dashboard;
