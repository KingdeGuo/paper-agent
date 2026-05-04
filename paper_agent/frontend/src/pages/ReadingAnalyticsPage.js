import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Chip, CircularProgress, LinearProgress, Stack, Divider } from '@mui/material';
import { TrendingUp, MenuBook, Timer, Flag, LocalFireDepartment, Speed, People } from '@mui/icons-material';
import api from '../services/api';

const ReadingAnalyticsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/reading-analytics', { params: { days: 90 } })
      .then(res => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box textAlign="center" py={10}><CircularProgress /></Box>;
  if (!data) return <Typography>No data available</Typography>;

  const vol = data.volume || {};
  const status = data.reading_status || {};
  const pace = data.pace || {};
  const streaks = data.streaks || {};

  const StatCard = ({ icon, label, value, sub, color = 'primary.main' }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ width: 44, height: 44, borderRadius: 2, bgcolor: color, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>{icon}</Box>
          <Box><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="h5" sx={{ fontWeight: 'bold' }}>{value}</Typography>{sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}</Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>📊 Reading Analytics</Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<MenuBook />} label="Papers Read" value={status.read || 0} sub={`of ${status.total || 0} total`} color="#2563eb" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<Timer />} label="Minutes Read" value={vol.total_minutes || 0} sub={`${pace.minutes_per_week || 0}/wk`} color="#7c3aed" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<Flag />} label="Completion" value={`${status.completion_rate || 0}%`} sub="of reading list" color="#16a34a" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<LocalFireDepartment />} label="Current Streak" value={`${streaks.current_streak || 0}d`} sub={`Best: ${streaks.longest_streak || 0}d`} color="#ea580c" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<Speed />} label="Reading Pace" value={`${pace.papers_per_week || 0}/wk`} sub={`${pace.pages_per_week || 0} pages`} color="#0891b2" /></Grid>
        <Grid item xs={6} sm={4} md={2}><StatCard icon={<People />} label="Authors" value={(data.top_authors || []).length} sub="in your library" color="#d946ef" /></Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Reading Progress */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Reading Progress</Typography>
            <Stack spacing={1.5}>
              {[
                { label: 'Read', value: status.read || 0, color: 'success.main' },
                { label: 'Reading', value: status.reading || 0, color: 'primary.main' },
                { label: 'To Read', value: status.to_read || 0, color: 'warning.main' },
                { label: 'Skipped', value: status.skipped || 0, color: 'grey.400' },
              ].map((item, i) => (
                <Box key={i}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">{item.label}</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{item.value}</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={(item.value / Math.max(status.total || 1, 1)) * 100}
                    sx={{ height: 8, borderRadius: 4, mt: 0.5, bgcolor: 'grey.100,', '& .MuiLinearProgress-bar': { bgcolor: item.color } }} />
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>

        {/* Top Authors */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Most Read Authors</Typography>
            {(data.top_authors || []).length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>No author data yet.</Typography>
            ) : (
              <Stack spacing={1}>
                {(data.top_authors || []).slice(0, 10).map((a, i) => (
                  <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">{a.author}</Typography>
                    <Chip label={`${a.count} papers`} size="small" variant="outlined" />
                  </Box>
                ))}
              </Stack>
            )}
          </Paper>
        </Grid>

        {/* Year Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Papers by Year</Typography>
            <Stack spacing={0.5}>
              {(data.year_distribution || []).slice(-15).map((y, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" sx={{ minWidth: 30, fontWeight: 600 }}>{y.year}</Typography>
                  <LinearProgress variant="determinate" value={Math.min((y.count / 10) * 100, 100)}
                    sx={{ flex: 1, height: 12, borderRadius: 3 }} />
                  <Typography variant="caption" sx={{ minWidth: 20 }}>{y.count}</Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>

        {/* Daily Breakdown */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2.5, maxHeight: 350, overflow: 'auto' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Recent Reading Days</Typography>
            {(vol.daily_breakdown || []).slice(-14).reverse().map((d, i) => (
              <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Typography variant="caption">{d.date}</Typography>
                <Typography variant="caption">{d.sessions} sessions · {d.minutes}min · {d.pages}pgs</Typography>
              </Box>
            ))}
            {(vol.daily_breakdown || []).length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>Log reading sessions to see your daily breakdown.</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ReadingAnalyticsPage;
