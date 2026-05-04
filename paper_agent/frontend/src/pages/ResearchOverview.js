import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Chip, CircularProgress, LinearProgress, Stack, Divider, Button } from '@mui/material';
import { TrendingUp, MenuBook, Schedule, CheckCircle, Speed, LocalFireDepartment, AutoAwesome as AIIcon, Psychology, Forum, Hub } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const ResearchOverview = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState(null);
  const [memory, setMemory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/stats/full').catch(() => ({ data: {} })),
      api.get('/research/reading-history', { params: { days: 30 } }).catch(() => ({ data: {} })),
      api.get('/memory/preview').catch(() => ({ data: {} })),
    ]).then(([s, h, m]) => {
      setStats(s.data); setHistory(h.data); setMemory(m.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Box textAlign="center" py={10}><CircularProgress /></Box>;

  const docs = stats?.documents || {};
  const read = stats?.reading || {};
  const sess = history?.totals || {};
  const memSec = memory?.sections || [];

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>📊 Research Overview</Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { icon: <MenuBook />, label: 'Papers', value: docs.total || 0, color: '#2563eb' },
          { icon: <CheckCircle />, label: 'Read', value: read.read || 0, sub: `${read.read_count || 0} total`, color: '#16a34a' },
          { icon: <Schedule />, label: 'To Read', value: read.to_read || 0, color: '#ea580c' },
          { icon: <TrendingUp />, label: 'Sessions', value: sess.reading_sessions || 0, color: '#7c3aed' },
          { icon: <Speed />, label: 'Minutes', value: sess.total_minutes || 0, color: '#0891b2' },
          { icon: <LocalFireDepartment />, label: 'Avg/Day', value: `${sess.avg_daily_minutes || 0}m`, color: '#d946ef' },
        ].map((s, i) => (
          <Grid item xs={4} sm={2} key={i}>
            <Card sx={{ textAlign: 'center' }}>
              <CardContent sx={{ py: 1.5 }}>
                <Box sx={{ color: s.color, mb: 0.5 }}>{s.icon}</Box>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{s.value}</Typography>
                <Typography variant="caption" color="text.secondary">{s.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Activity */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>📖 Recent Reading</Typography>
            {(!history?.papers_read || history.papers_read.length === 0) ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', py: 4, textAlign: 'center' }}>
                No papers read yet this period. Start reading!
              </Typography>
            ) : (
              <Stack spacing={0.5}>
                {history.papers_read.slice(0, 8).map((p, i) => (
                  <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.3, cursor: 'pointer' }}
                    onClick={() => navigate(`/documents/${p.id}`)}>
                    <Typography variant="body2" noWrap sx={{ maxWidth: '70%' }}>{p.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{p.date}</Typography>
                  </Box>
                ))}
              </Stack>
            )}
          </Paper>
        </Grid>

        {/* Memory Snippets */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>🧠 Research Memory</Typography>
              <Button size="small" onClick={() => navigate('/settings')}>Edit</Button>
            </Box>
            {memSec.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', py: 4, textAlign: 'center' }}>
                Memory not yet initialized. Write to RESEARCH_MEMORY.md
              </Typography>
            ) : memSec.slice(0, 3).map((s, i) => (
              <Box key={i} sx={{ mb: 1 }}>
                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'primary.main' }}>{s.title}</Typography>
                <Typography variant="caption" color="text.secondary" display="block" noWrap>{s.content}</Typography>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>⚡ Quick Actions</Typography>
            <Stack spacing={1}>
              {[
                { label: 'Ask My Library', path: '/ask', icon: <AIIcon fontSize="small" /> },
                { label: 'GraphRAG Query', path: '/graphrag', icon: <Hub fontSize="small" /> },
                { label: 'AI Agents', path: '/agents', icon: <Psychology fontSize="small" /> },
                { label: 'Scholar Insights', path: '/insights', icon: <Forum fontSize="small" /> },
                { label: 'Research Toolkit', path: '/research-tools', icon: <Hub fontSize="small" /> },
              ].map((a, i) => (
                <Button key={i} variant="outlined" size="small" startIcon={a.icon}
                  onClick={() => navigate(a.path)} sx={{ justifyContent: 'flex-start' }}>
                  {a.label}
                </Button>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ResearchOverview;
