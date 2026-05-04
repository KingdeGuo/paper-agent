import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Chip, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress, Alert, Stack, Divider, IconButton, Select, MenuItem, FormControl, InputLabel, LinearProgress } from '@mui/material';
import { CalendarMonth as CalendarIcon, Add as AddIcon, Delete as DeleteIcon, Launch as LinkIcon, EventBusy as UrgentIcon, CheckCircle as SubmittedIcon, Edit as EditIcon } from '@mui/icons-material';
import api from '../services/api';

const ConferenceTrackerPage = () => {
  const [tracked, setTracked] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState(false);
  const [venueId, setVenueId] = useState('');
  const [deadline, setDeadline] = useState('');
  const [venues, setVenues] = useState([]);
  const [notify, setNotify] = useState({ open: false, msg: '' });

  useEffect(() => { fetchAll(); fetchVenues(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [t, s] = await Promise.all([
        api.get('/conferences/tracked'),
        api.get('/conferences/submissions'),
      ]);
      setTracked(t.data || []);
      setSubmissions(s.data || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchVenues = async () => {
    try { const res = await api.get('/conferences/venues'); setVenues(res.data?.venues || []); } catch (e) {}
  };

  const handleAddTrack = async () => {
    if (!venueId) return;
    try {
      await api.post('/conferences/track', null, { params: { venue_id: venueId, submission_deadline: deadline || undefined } });
      setDialog(false); setVenueId(''); setDeadline('');
      fetchAll();
    } catch (e) { console.error(e); }
  };

  const handleDelete = async (id) => {
    try { await api.delete(`/conferences/tracked/${id}`); fetchAll(); } catch (e) {}
  };

  const urgencyColor = (u) => {
    if (u === 'critical') return 'error';
    if (u === 'upcoming') return 'warning';
    if (u === 'past') return 'default';
    return 'success';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}><CalendarIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Conference Tracker</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialog(true)}>Track Conference</Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <Grid container spacing={3}>
          {/* Tracked Conferences */}
          <Grid item xs={12} md={8}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>Tracked Deadlines</Typography>
            {tracked.length === 0 ? (
              <Paper sx={{ p: 5, textAlign: 'center', opacity: 0.5 }}>
                <Typography>No conferences tracked yet. Add your first venue!</Typography>
              </Paper>
            ) : (
              <Stack spacing={1.5}>
                {tracked.map((t, i) => (
                  <Card key={i} variant="outlined" sx={{
                    borderLeft: 4,
                    borderLeftColor: t.urgency === 'critical' ? 'error.main' : t.urgency === 'upcoming' ? 'warning.main' : t.urgency === 'past' ? 'grey.400' : 'success.main',
                  }}>
                    <CardContent sx={{ py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{t.venue_name}</Typography>
                        <Typography variant="caption" color="text.secondary">{t.field} · {t.submission_count} submission(s)</Typography>
                        {t.days_until_deadline !== null && (
                          <Box sx={{ mt: 0.5 }}>
                            <Chip
                              icon={t.urgency === 'critical' ? <UrgentIcon /> : null}
                              label={t.days_until_deadline < 0 ? `Past by ${Math.abs(t.days_until_deadline)}d` : `${t.days_until_deadline}d remaining`}
                              size="small" color={urgencyColor(t.urgency)} variant="outlined"
                            />
                          </Box>
                        )}
                      </Box>
                      <Box>
                        {t.url && <IconButton size="small" href={t.url} target="_blank"><LinkIcon /></IconButton>}
                        <IconButton size="small" onClick={() => handleDelete(t.id)}><DeleteIcon /></IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Grid>

          {/* Submissions */}
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>My Submissions</Typography>
            {submissions.length === 0 ? (
              <Paper sx={{ p: 3, textAlign: 'center', opacity: 0.5 }}>
                <Typography variant="body2">No submissions logged.</Typography>
              </Paper>
            ) : (
              <Stack spacing={1}>
                {submissions.map((s, i) => (
                  <Card key={i} variant="outlined">
                    <CardContent sx={{ py: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>{s.title || 'Untitled'}</Typography>
                      <Typography variant="caption" color="text.secondary">{s.venue_name || 'Venue'} · {s.status}</Typography>
                      {s.decision && <Chip label={s.decision} size="small" color={s.decision === 'accepted' ? 'success' : 'error'} variant="outlined" sx={{ ml: 1 }} />}
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Grid>

          {/* Venues List */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Available Venues</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {venues.map((v, i) => (
                  <Chip key={i} label={`${v.name} (${v.field})`} size="small" variant="outlined"
                    onClick={() => { setVenueId(v.id); setDialog(true); }} sx={{ cursor: 'pointer', mb: 0.5 }} />
                ))}
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      )}

      <Dialog open={dialog} onClose={() => setDialog(false)}>
        <DialogTitle>Track Conference</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <FormControl fullWidth margin="dense">
            <InputLabel>Venue</InputLabel>
            <Select value={venueId} onChange={e => setVenueId(e.target.value)} label="Venue">
              {venues.map((v, i) => <MenuItem key={i} value={v.id}>{v.name} ({v.field})</MenuItem>)}
            </Select>
          </FormControl>
          <TextField fullWidth margin="dense" label="Submission Deadline" type="date" value={deadline}
            onChange={e => setDeadline(e.target.value)} InputLabelProps={{ shrink: true }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddTrack}>Track</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConferenceTrackerPage;
