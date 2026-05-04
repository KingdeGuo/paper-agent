import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Paper, Chip, IconButton, CircularProgress,
  LinearProgress, Tabs, Tab, Grid, Card, CardContent, CardActions,
  Menu, MenuItem, ListItemIcon, ListItemText, TextField, Slider,
  Snackbar, Alert,
} from '@mui/material';
import {
  MenuBook as ReadingIcon, CheckCircle as ReadIcon,
  Schedule as ToReadIcon, PlayArrow as InProgressIcon,
  Delete as DeleteIcon, MoreVert as MoreIcon,
  BookmarkBorder as BookmarkIcon, Star as StarIcon,
  Notes as NotesIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const STATUS_CONFIG = {
  to_read: { label: 'To Read', icon: <ToReadIcon />, color: 'default' },
  reading: { label: 'Reading', icon: <InProgressIcon />, color: 'primary' },
  read: { label: 'Read', icon: <ReadIcon />, color: 'success' },
  skipped: { label: 'Skipped', icon: <DeleteIcon />, color: 'warning' },
  reference: { label: 'Reference', icon: <BookmarkIcon />, color: 'info' },
};

const ReadingList = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState('all');
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [notify, setNotify] = useState({ open: false, msg: '', severity: 'success' });
  const [anchorEl, setAnchorEl] = useState(null);
  const [activeDoc, setActiveDoc] = useState(null);

  useEffect(() => { fetchAll(); }, [tab]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const params = tab !== 'all' ? { status: tab } : {};
      const [entriesRes, statsRes] = await Promise.all([
        api.get('/reading', { params }),
        api.get('/reading/stats'),
      ]);
      setEntries(entriesRes.data || []);
      setStats(statsRes.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleStatusChange = async (docId, status) => {
    try {
      await api.put(`/reading/${docId}/status`, status, {
        headers: { 'Content-Type': 'text/plain' }
      });
      setNotify({ open: true, msg: `Marked as "${STATUS_CONFIG[status]?.label || status}"`, severity: 'success' });
      fetchAll();
    } catch (e) {
      setNotify({ open: true, msg: 'Failed to update status', severity: 'error' });
    }
    setAnchorEl(null);
  };

  const handleProgressChange = async (docId, progress) => {
    try {
      await api.put(`/reading/${docId}/progress`, null, {
        params: { progress }
      });
      fetchAll();
    } catch (e) { console.error(e); }
  };

  const handleRemove = async (docId) => {
    try {
      await api.delete(`/reading/${docId}`);
      setNotify({ open: true, msg: 'Removed from reading list', severity: 'info' });
      fetchAll();
    } catch (e) { console.error(e); }
  };

  const statusChip = (status) => {
    const cfg = STATUS_CONFIG[status] || { label: status, color: 'default' };
    return <Chip icon={cfg.icon} label={cfg.label} color={cfg.color} size="small" variant="outlined" />;
  };

  const progressColor = (p) => {
    if (p >= 1) return 'success';
    if (p >= 0.5) return 'primary';
    return 'warning';
  };

  const getCardForEntry = (entry, idx) => (
    <Grid item xs={12} sm={6} md={4} key={entry.id || idx}>
      <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            {statusChip(entry.status)}
            <IconButton size="small" onClick={(e) => { setAnchorEl(e.currentTarget); setActiveDoc(entry.document_id); }}>
              <MoreIcon />
            </IconButton>
          </Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', cursor: 'pointer' }}
            onClick={() => navigate(`/documents/${entry.document_id}`)}>
            {entry.title || entry.filename || 'Untitled'}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
            {(entry.authors || []).slice(0, 2).join(', ')}{entry.authors?.length > 2 ? '...' : ''} {entry.year ? `(${entry.year})` : ''}
          </Typography>
          {entry.status !== 'skipped' && entry.status !== 'reference' && (
            <Box sx={{ mt: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {Math.round(entry.progress * 100)}%
                </Typography>
                {entry.total_pages > 0 && (
                  <Typography variant="caption" color="text.secondary">
                    p.{entry.current_page || 0}/{entry.total_pages}
                  </Typography>
                )}
              </Box>
              <LinearProgress variant="determinate" value={entry.progress * 100}
                color={progressColor(entry.progress)} sx={{ height: 6, borderRadius: 3 }} />
            </Box>
          )}
          {entry.notes && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', fontStyle: 'italic' }}>
              "{entry.notes.slice(0, 100)}{entry.notes.length > 100 ? '...' : ''}"
            </Typography>
          )}
        </CardContent>
        <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 1 }}>
          {entry.priority > 0 && <Chip icon={<StarIcon />} label={entry.priority} size="small" color="warning" variant="outlined" />}
          <Typography variant="caption" color="text.secondary">
            {entry.date_added ? new Date(entry.date_added).toLocaleDateString() : ''}
          </Typography>
        </CardActions>
      </Card>
    </Grid>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>Reading List</Typography>
      </Box>

      {stats && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={3} textAlign="center">
            {[
              { label: 'Total', value: stats.total, color: 'text.primary' },
              { label: 'To Read', value: stats.to_read, color: 'warning.main' },
              { label: 'Reading', value: stats.reading, color: 'primary.main' },
              { label: 'Read', value: stats.read_count ?? stats.read, color: 'success.main' },
              { label: 'Avg Progress', value: `${Math.round(stats.avg_progress * 100)}%`, color: 'info.main' },
            ].map((s, i) => (
              <Grid item xs key={i}><Typography variant="h4" sx={{ color: s.color, fontWeight: 'bold' }}>{s.value}</Typography><Typography variant="caption">{s.label}</Typography></Grid>
            ))}
          </Grid>
        </Paper>
      )}

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab value="all" label="All" />
        {Object.entries(STATUS_CONFIG).map(([k, v]) => (
          <Tab key={k} value={k} icon={v.icon} iconPosition="start" label={v.label} />
        ))}
      </Tabs>

      {loading ? <Box textAlign="center" py={10}><CircularProgress /></Box> : (
        <Grid container spacing={2}>
          {entries.length === 0 ? (
            <Grid item xs={12}>
              <Box textAlign="center" py={10} sx={{ opacity: 0.5 }}>
                <ReadingIcon sx={{ fontSize: 60, mb: 2 }} />
                <Typography variant="h6">No papers in this list</Typography>
                <Typography variant="body2" color="text.secondary">Go to Documents to start building your reading list</Typography>
                <Button variant="contained" sx={{ mt: 2 }} onClick={() => navigate('/documents')}>Browse Documents</Button>
              </Box>
            </Grid>
          ) : entries.map((e, i) => getCardForEntry(e, i))}
        </Grid>
      )}

      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
        {Object.entries(STATUS_CONFIG).map(([k, v]) => (
          <MenuItem key={k} onClick={() => handleStatusChange(activeDoc, k)} dense>
            <ListItemIcon>{v.icon}</ListItemIcon>
            <ListItemText>{v.label}</ListItemText>
          </MenuItem>
        ))}
        <MenuItem onClick={() => { setAnchorEl(null); }} dense>
          <ListItemIcon><NotesIcon /></ListItemIcon>
          <TextField size="small" placeholder="Add note..." onKeyDown={e => { if (e.key === 'Enter') { handleStatusChange(activeDoc, 'reading'); } }} />
        </MenuItem>
        <MenuItem onClick={() => handleRemove(activeDoc)} dense>
          <ListItemIcon><DeleteIcon color="error" /></ListItemIcon>
          <ListItemText><Typography color="error">Remove</Typography></ListItemText>
        </MenuItem>
      </Menu>

      <Snackbar open={notify.open} autoHideDuration={3000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default ReadingList;
