import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, Card, CardContent, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip, Button,
  CircularProgress, Stack, Divider, Alert, LinearProgress,
} from '@mui/material';
import {
  Security as SecurityIcon, People as UsersIcon,
  HealthAndSafety as HealthIcon, Storage as StorageIcon,
  Refresh as RefreshIcon, Warning as WarningIcon,
} from '@mui/icons-material';
import api from '../services/api';

const Admin = () => {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [h, s] = await Promise.all([
        api.get('/health').catch(() => ({ data: { status: 'unknown' } })),
        api.get('/stats/full').catch(() => ({ data: {} })),
      ]);
      setHealth(h.data || h);
      setStats(s.data || s);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  if (loading) return <Box sx={{ mt: 3 }}><LinearProgress /></Box>;

  const docStats = stats?.documents || {};
  const reading = stats?.reading || {};
  const vec = stats?.vector_db || {};

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon /> Admin Panel
        </Typography>
        <Button startIcon={<RefreshIcon />} onClick={fetchAll}>Refresh</Button>
      </Box>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <HealthIcon sx={{ color: health?.status === 'healthy' ? 'success.main' : 'warning.main', fontSize: 36 }} />
                <Box><Typography variant="caption" color="text.secondary">System Status</Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: health?.status === 'healthy' ? 'success.main' : 'warning.main' }}>
                    {health?.status || 'Unknown'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">v{health?.version || '2.0'}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Stack spacing={0.5}>
              <Typography variant="caption" color="text.secondary"><StorageIcon sx={{ mr: 0.5, fontSize: 14 }} />Documents</Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{docStats.total || 0} total</Typography>
              <Typography variant="caption">{docStats.completed || 0} processed · {docStats.pending || 0} pending</Typography>
            </Stack>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Stack spacing={0.5}>
              <Typography variant="caption" color="text.secondary"><UsersIcon sx={{ mr: 0.5, fontSize: 14 }} />Reading</Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{reading.read_count || 0} read</Typography>
              <Typography variant="caption">{reading.to_read || 0} to read · {reading.reading || 0} in progress</Typography>
            </Stack>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Stack spacing={0.5}>
              <Typography variant="caption" color="text.secondary"><StorageIcon sx={{ mr: 0.5, fontSize: 14 }} />Vector DB</Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{vec.total_chunks || 0} chunks</Typography>
              <Typography variant="caption">Model: {vec.model || 'N/A'} · {vec.dimension || '-'}d</Typography>
            </Stack>
          </CardContent></Card>
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Route Registry</Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Route</TableCell>
                    <TableCell>Tag</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[
                    '/api/documents', '/api/search', '/api/summary', '/api/users',
                    '/api/knowledge', '/api/review', '/api/arxiv', '/api/notebooks',
                    '/api/discovery', '/api/zotero', '/api/drafting', '/api/annotations',
                    '/api/citations', '/api/reading', '/api/ask', '/api/collab',
                    '/api/digest', '/api/overleaf', '/api/stats', '/api/searches',
                    '/api/import', '/api/bibtex',
                  ].map((route, i) => (
                    <TableRow key={i}>
                      <TableCell><Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: 12 }}>{route}</Typography></TableCell>
                      <TableCell><Chip label={route.split('/').pop() || route} size="small" variant="outlined" /></TableCell>
                      <TableCell><Chip label="Active" size="small" color="success" /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>System Configuration</Typography>
            <Stack spacing={1.5}>
              {[
                { label: 'API Version', value: health?.version || '2.0.0' },
                { label: 'Python', value: '3.12' },
                { label: 'Frontend', value: 'React 18 + MUI 5' },
                { label: 'Vector DB', value: `ChromaDB (${vec.model || 'all-MiniLM-L6-v2'})` },
                { label: 'Database', value: 'SQLite / PostgreSQL' },
                { label: 'Cache', value: 'Redis (optional)' },
                { label: 'Storage', value: 'Local / MinIO / S3' },
                { label: 'Auth', value: 'JWT + PBKDF2-SHA256' },
                { label: 'Total Routes', value: '22 registered' },
              ].map((item, i) => (
                <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">{item.label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{item.value}</Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Admin;
