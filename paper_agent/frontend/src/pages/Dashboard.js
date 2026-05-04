import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  Description as DocumentIcon,
  TrendingUp as TrendingIcon,
  Search as SearchIcon,
  CheckCircle as CheckIcon,
  HourglassEmpty as PendingIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { systemAPI, searchAPI } from '../services/api';

const Dashboard = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsData, trendingData] = await Promise.all([
        systemAPI.getStats(),
        searchAPI.trending(5),
      ]);
      setStats(statsData);
      setTrending(trendingData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 2:
        return <CheckIcon color="success" />;
      case 1:
        return <PendingIcon color="warning" />;
      case 3:
        return <ErrorIcon color="error" />;
      default:
        return <PendingIcon color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 2:
        return 'success';
      case 1:
        return 'warning';
      case 3:
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {t('dashboard.title')}
      </Typography>

      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <DocumentIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    {t('dashboard.totalDocuments')}
                  </Typography>
                  <Typography variant="h4">
                    {stats?.documents?.total || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckIcon sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    {t('dashboard.processed')}
                  </Typography>
                  <Typography variant="h4">
                    {stats?.documents?.completed || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <PendingIcon sx={{ fontSize: 40, color: 'warning.main', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    {t('dashboard.processing')}
                  </Typography>
                  <Typography variant="h4">
                    {stats?.documents?.processing || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SearchIcon sx={{ fontSize: 40, color: 'info.main', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    {t('dashboard.vectorChunks')}
                  </Typography>
                  <Typography variant="h4">
                    {stats?.vector_db?.total_chunks || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('dashboard.processingStatus')}
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">{t('dashboard.completed')}</Typography>
                <Typography variant="body2">
                  {stats?.documents?.completed || 0} / {stats?.documents?.total || 0}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={
                  stats?.documents?.total
                    ? (stats.documents.completed / stats.documents.total) * 100
                    : 0
                }
                sx={{ mb: 2 }}
              />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">{t('dashboard.processing')}</Typography>
                <Typography variant="body2">{stats?.documents?.processing || 0}</Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">{t('dashboard.failed')}</Typography>
                <Typography variant="body2">{stats?.documents?.failed || 0}</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* System Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('dashboard.systemInfo')}
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>{t('dashboard.embeddingModel')}:</strong> {stats?.system?.embedding_model || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>{t('dashboard.llmProvider')}:</strong> {stats?.system?.llm_provider || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>{t('dashboard.llmModel')}:</strong> {stats?.system?.llm_model || 'N/A'}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Trending Documents */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <TrendingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              {t('dashboard.trendingDocuments')}
            </Typography>
            <List>
              {trending.map((item, index) => (
                <ListItem key={index} divider={index < trending.length - 1}>
                  <ListItemText
                    primary={item.document.title || item.document.filename}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          <strong>{t('dashboard.authors')}:</strong> {item.document.authors?.join(', ') || t('dashboard.unknown')}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          <strong>{t('dashboard.year')}:</strong> {item.document.year || t('dashboard.unknown')}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Chip
                            label={item.document.processed === 2 ? t('dashboard.completed') : t('dashboard.processing')}
                            color={getStatusColor(item.document.processed)}
                            size="small"
                          />
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;