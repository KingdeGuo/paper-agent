import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, TextField, Button, Card, CardContent, Chip, CircularProgress, Grid, Stack, Tabs, Tab, Divider, IconButton } from '@mui/material';
import { EditNote as JournalIcon, Save as SaveIcon, AutoAwesome as AIIcon, CalendarMonth as DateIcon, TrendingUp as WeeklyIcon } from '@mui/icons-material';
import api from '../services/api';

const ResearchJournalPage = () => {
  const [tab, setTab] = useState(0);
  const [today, setToday] = useState('');
  const [entries, setEntries] = useState([]);
  const [weeklyReview, setWeeklyReview] = useState(null);
  const [content, setContent] = useState('');
  const [mood, setMood] = useState('');
  const [goalsToday, setGoalsToday] = useState('');
  const [goalsTomorrow, setGoalsTomorrow] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const d = new Date().toISOString().split('T')[0];
    setToday(d);
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const [entriesRes, weeklyRes] = await Promise.all([
        api.get('/journal', { params: { days: 30 } }),
        api.get('/journal/weekly-review').catch(() => ({ data: null })),
      ]);
      setEntries(entriesRes.data || []);
      setWeeklyReview(weeklyRes.data);
    } catch (e) {}
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    if (!content.trim()) return;
    setSaving(true);
    try {
      await api.post('/journal', null, { params: { date: today, content, mood: mood || undefined, goals_today: goalsToday || undefined, goals_tomorrow: goalsTomorrow || undefined } });
      fetchEntries();
    } catch (e) {}
    finally { setSaving(false); }
  };

  const todayEntry = entries.find(e => e.date === today);

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto' }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}><JournalIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Research Journal</Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Today's Entry" />
        <Tab label="History" />
        <Tab label="Weekly Review" />
      </Tabs>

      {tab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}><DateIcon sx={{ mr: 0.5, verticalAlign: 'middle' }} />{today}</Typography>
          {todayEntry && (
            <Card variant="outlined" sx={{ mb: 2, bgcolor: 'success.50' }}>
              <CardContent sx={{ py: 1.5 }}>
                <Typography variant="body2">📖 {todayEntry.papers_read} papers · ⏱️ {todayEntry.minutes_spent} min</Typography>
                {todayEntry.mood && <Typography variant="body2">😊 Mood: {todayEntry.mood}</Typography>}
              </CardContent>
            </Card>
          )}

          <TextField fullWidth multiline rows={5} placeholder="What did you work on today? Any research breakthroughs or challenges?"
            value={content} onChange={e => setContent(e.target.value)} sx={{ mb: 2 }} />

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={4}>
              <TextField fullWidth size="small" label="Mood" placeholder="e.g., productive, frustrated, inspired"
                value={mood} onChange={e => setMood(e.target.value)} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField fullWidth size="small" label="Today's Goals" placeholder="What did you accomplish?"
                value={goalsToday} onChange={e => setGoalsToday(e.target.value)} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField fullWidth size="small" label="Tomorrow's Goals" placeholder="What's next?"
                value={goalsTomorrow} onChange={e => setGoalsTomorrow(e.target.value)} />
            </Grid>
          </Grid>

          <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSave} disabled={saving || !content.trim()}>
            {saving ? <CircularProgress size={20} /> : 'Save Entry'}
          </Button>
        </Paper>
      )}

      {tab === 1 && (
        <Stack spacing={1.5}>
          {entries.length === 0 && <Typography color="text.secondary" sx={{ textAlign: 'center', py: 5, fontStyle: 'italic' }}>No journal entries yet.</Typography>}
          {entries.map((e, i) => (
            <Card key={i} variant="outlined">
              <CardContent sx={{ py: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{e.date}</Typography>
                  <Stack direction="row" spacing={0.5}>
                    <Chip label={`${e.papers_read || 0} papers`} size="small" />
                    <Chip label={`${e.minutes_spent || 0} min`} size="small" variant="outlined" />
                    {e.mood && <Chip label={e.mood} size="small" variant="outlined" />}
                  </Stack>
                </Box>
                <Typography variant="body2" color="text.secondary">{(e.content || '').slice(0, 200)}</Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {tab === 2 && (
        <Paper sx={{ p: 3 }}>
          {weeklyReview ? (
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                <WeeklyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Week Ending {weeklyReview.week_ending}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}><Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>{weeklyReview.entries}</Typography><Typography variant="caption">Entries</Typography></Grid>
                <Grid item xs={4}><Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>{weeklyReview.total_papers_read}</Typography><Typography variant="caption">Papers Read</Typography></Grid>
                <Grid item xs={4}><Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>{weeklyReview.total_minutes}</Typography><Typography variant="caption">Minutes</Typography></Grid>
              </Grid>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>Daily Breakdown</Typography>
              {(weeklyReview.daily_entries || []).map((d, i) => (
                <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                  <Typography variant="body2">{d.date}</Typography>
                  <Typography variant="body2" color="text.secondary">{d.papers_read} papers · {d.minutes}min {d.mood ? `· ${d.mood}` : ''}</Typography>
                </Box>
              ))}
            </Box>
          ) : (
            <Box textAlign="center" py={5} sx={{ opacity: 0.5 }}>
              <Typography variant="h6">No Weekly Data Yet</Typography>
              <Typography variant="body2" color="text.secondary">Write journal entries throughout the week to see your review.</Typography>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default ResearchJournalPage;
