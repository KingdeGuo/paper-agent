import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Grid, Paper, Typography, Box, Card, CardContent, LinearProgress,
  List, ListItem, ListItemText, Chip, Button, Stack, Divider,
  CircularProgress, IconButton,
} from '@mui/material';
import {
  Description as DocumentIcon, TrendingUp as TrendingIcon,
  Search as SearchIcon, CheckCircle as CheckIcon,
  HourglassEmpty as PendingIcon, Error as ErrorIcon,
  MenuBook as ReadingIcon, Schedule as ToReadIcon,
  AutoAwesome as AIIcon, Refresh as RefreshIcon,
  History as ActivityIcon, ArrowForward as ArrowIcon,
  LibraryBooks as LibraryIcon,
} from '@mui/icons-material';
import { systemAPI, searchAPI } from '../services/api';
import api from '../services/api';

const Dashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [fullStats, setFullStats] = useState(null);
  const [insight, setInsight] = useState(null);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [insightLoading, setInsightLoading] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    fetchInsight();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsData, trendingData] = await Promise.all([
        api.get('/stats/full').catch(() => systemAPI.getStats()),
        searchAPI.trending(5).catch(() => []),
      ]);
      setFullStats(statsData.data || statsData);
      setTrending(Array.isArray(trendingData) ? trendingData : trendingData.data || []);
    } catch (e) { console.error('Dashboard fetch error:', e); }
    finally { setLoading(false); }
  };

  const fetchInsight = async () => {
    setInsightLoading(true);
    try {
      const res = await api.get('/stats/quick-insight');
      setInsight(res.data?.insight || null);
    } catch (e) { /* skip */ }
    finally { setInsightLoading(false); }
  };

  const docs = fullStats?.documents || {};
  const reading = fullStats?.reading || {};
  const activity = fullStats?.activity || [];

  const StatCard = ({ icon, label, value, color = 'primary.main', onClick }) => (
    <Card sx={{ cursor: onClick ? 'pointer' : 'default' }} onClick={onClick}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: color, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>{icon}</Box>
          <Box>
            <Typography variant="caption" color="text.secondary">{label}</Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{value}</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) return <Box sx={{ mt: 3 }}><LinearProgress /></Box>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>{t('dashboard.title')}</Typography>
        <Button size="small" startIcon={<RefreshIcon />} onClick={fetchDashboardData}>Refresh</Button>
      </Box>

      <Grid container spacing={2.5}>
        {/* Document Stats */}
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<DocumentIcon />} label="Total Papers" value={docs.total || 0} color="#2563eb" onClick={() => navigate('/documents')} /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<CheckIcon />} label="Completed" value={docs.completed || 0} color="#16a34a" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<PendingIcon />} label="Processing" value={docs.processing || 0} color="#ea580c" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<SearchIcon />} label="Vector Chunks" value={fullStats?.vector_db?.total_chunks || 0} color="#7c3aed" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<ToReadIcon />} label="To Read" value={reading.to_read || 0} color="#f59e0b" onClick={() => navigate('/reading')} /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<ReadingIcon />} label="Reading" value={reading.reading || 0} color="#2563eb" onClick={() => navigate('/reading')} /></Grid>

        {/* AI Insight */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}><AIIcon color="secondary" /> AI Insight</Typography>
              <IconButton size="small" onClick={fetchInsight}><RefreshIcon fontSize="small" /></IconButton>
            </Box>
            {insightLoading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 2 }}><CircularProgress size={16} /><Typography variant="body2" color="text.secondary">Analyzing your library...</Typography></Box>
            ) : (
              <Typography variant="body2" sx={{ lineHeight: 1.7, fontStyle: insight ? 'normal' : 'italic', color: insight ? 'text.primary' : 'text.secondary' }}>
                {insight || 'Upload papers to get AI-powered insights about your research library.'}
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* System Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1.5 }}>System Information</Typography>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><Typography variant="body2" color="text.secondary">Embedding Model</Typography><Typography variant="body2" sx={{ fontWeight: 500 }}>{fullStats?.vector_db?.model || 'N/A'}</Typography></Box>
              <Divider />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><Typography variant="body2" color="text.secondary">Vector Dimension</Typography><Typography variant="body2" sx={{ fontWeight: 500 }}>{fullStats?.vector_db?.dimension || 'N/A'}</Typography></Box>
              <Divider />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><Typography variant="body2" color="text.secondary">Documents</Typography><Typography variant="body2" sx={{ fontWeight: 500 }}>{docs.total || 0} ({docs.completed || 0} processed)</Typography></Box>
              <Divider />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><Typography variant="body2" color="text.secondary">Reading Progress</Typography><Typography variant="body2" sx={{ fontWeight: 500 }}>{Math.round(reading.avg_progress * 100) || 0}% avg</Typography></Box>
            </Stack>
          </Paper>
        </Grid>

        {/* Processing Status */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1.5 }}>Processing Status</Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}><Typography variant="body2">Completed</Typography><Typography variant="body2" sx={{ fontWeight: 600 }}>{docs.completed || 0} / {docs.total || 0}</Typography></Box>
            <LinearProgress variant="determinate" value={docs.total ? ((docs.completed || 0) / docs.total) * 100 : 0} sx={{ mb: 1.5, height: 8, borderRadius: 4 }} />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Box><Typography variant="caption" color="text.secondary">Pending</Typography><Typography variant="body2">{docs.pending || 0}</Typography></Box>
              <Box><Typography variant="caption" color="text.secondary">Processing</Typography><Typography variant="body2">{docs.processing || 0}</Typography></Box>
              <Box><Typography variant="caption" color="text.secondary">Failed</Typography><Typography variant="body2">{docs.failed || 0}</Typography></Box>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}><ActivityIcon fontSize="small" /> Recent Activity</Typography>
            {activity.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>No recent activity</Typography>
            ) : (
              <List dense disablePadding>
                {activity.slice(0, 5).map((a, i) => (
                  <ListItem key={i} disablePadding sx={{ mb: 0.5 }}>
                    <ListItemText primary={
                      <Typography variant="body2" noWrap>{a.description || a.type}</Typography>
                    } secondary={<Typography variant="caption" color="text.secondary">{a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}</Typography>} />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1.5 }}>Quick Actions</Typography>
            <Stack spacing={1}>
              <Button variant="outlined" size="small" startIcon={<LibraryIcon />} onClick={() => navigate('/documents')} fullWidth>Browse Documents</Button>
              <Button variant="outlined" size="small" startIcon={<SearchIcon />} onClick={() => navigate('/search')} fullWidth>Search Library</Button>
              <Button variant="outlined" size="small" startIcon={<ReadingIcon />} onClick={() => navigate('/reading')} fullWidth>Reading List</Button>
              <Button variant="outlined" size="small" startIcon={<AIIcon />} onClick={() => navigate('/ask')} fullWidth>Ask AI</Button>
            </Stack>
          </Paper>
        </Grid>

        {/* Recent Documents */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Recent Documents</Typography>
              <Button size="small" endIcon={<ArrowIcon />} onClick={() => navigate('/documents')}>View All</Button>
            </Box>
            {(!fullStats?.recent_docs || fullStats.recent_docs.length === 0) ? (
              <Box textAlign="center" py={4} sx={{ opacity: 0.5 }}>
                <DocumentIcon sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="body2" color="text.secondary">No documents yet. Upload your first paper!</Typography>
              </Box>
            ) : (
              <Grid container spacing={1.5}>
                {fullStats.recent_docs.map((doc, i) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={i}>
                    <Card variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => navigate(`/documents/${doc.id}`)}>
                      <CardContent sx={{ py: 1.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }} noWrap>{doc.title || 'Untitled'}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block" noWrap>{(doc.authors || []).slice(0, 2).join(', ')}{doc.authors?.length > 2 ? ' et al.' : ''}</Typography>
                        <Box sx={{ mt: 0.5 }}>
                          <Chip label={doc.processed === 2 ? 'Completed' : doc.processed === 1 ? 'Processing' : 'Pending'} size="small" color={doc.processed === 2 ? 'success' : doc.processed === 1 ? 'warning' : 'default'} variant="outlined" />
                          {doc.year && <Chip label={doc.year} size="small" variant="outlined" sx={{ ml: 0.5 }} />}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
