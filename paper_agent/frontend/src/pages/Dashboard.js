import React, { useState, useEffect } from 'react';
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
        仪表板
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
                    总文献数
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
                    已处理
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
                    处理中
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
                    向量块
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
              处理状态
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">已完成</Typography>
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
                <Typography variant="body2">处理中</Typography>
                <Typography variant="body2">{stats?.documents?.processing || 0}</Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">失败</Typography>
                <Typography variant="body2">{stats?.documents?.failed || 0}</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* System Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              系统信息
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>嵌入模型:</strong> {stats?.system?.embedding_model || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>LLM提供商:</strong> {stats?.system?.llm_provider || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>LLM模型:</strong> {stats?.system?.llm_model || 'N/A'}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Trending Documents */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <TrendingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              热门文献
            </Typography>
            <List>
              {trending.map((item, index) => (
                <ListItem key={index} divider={index < trending.length - 1}>
                  <ListItemText
                    primary={item.document.title || item.document.filename}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          作者: {item.document.authors?.join(', ') || '未知'}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          年份: {item.document.year || '未知'}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Chip
                            label={item.document.processed === 2 ? '已处理' : '处理中'}
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
