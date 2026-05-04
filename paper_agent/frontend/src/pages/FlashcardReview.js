import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Button, Chip, CircularProgress, LinearProgress, Card, CardContent, Stack, IconButton, Grid, Snackbar, Alert } from '@mui/material';
import { FlipToFront as FlipIcon, CheckCircle as CorrectIcon, Cancel as WrongIcon, AutoAwesome as AIIcon, Refresh as RefreshIcon, Speed as SpeedIcon } from '@mui/icons-material';
import api from '../services/api';

const QUALITY_LABELS = ['Blackout', 'Wrong', 'Hard', 'OK', 'Easy', 'Perfect'];

const FlashcardReview = () => {
  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [sessionStats, setSessionStats] = useState({ reviewed: 0, correct: 0 });
  const [done, setDone] = useState(false);

  useEffect(() => { fetchDueCards(); fetchStats(); }, []);

  const fetchDueCards = async () => {
    setLoading(true);
    try { const res = await api.get('/flashcards/due', { params: { limit: 20 } }); setCards(res.data || []); setIndex(0); setFlipped(false); setDone(false); } catch (e) { }
    finally { setLoading(false); }
  };

  const fetchStats = async () => {
    try { const res = await api.get('/flashcards/stats'); setStats(res.data); } catch (e) {}
  };

  const handleReview = async (quality) => {
    if (!cards[index]) return;
    try {
      await api.post(`/flashcards/${cards[index].id}/review`, null, { params: { quality } });
      setSessionStats(prev => ({ reviewed: prev.reviewed + 1, correct: prev.correct + (quality >= 3 ? 1 : 0) }));
      setFlipped(false);
      if (index + 1 < cards.length) setIndex(index + 1);
      else { setDone(true); fetchStats(); }
    } catch (e) { console.error(e); }
  };

  const handleGenerateFlashcards = async () => {
    setLoading(true);
    try {
      const docsRes = await api.get('/documents', { params: { limit: 5 } });
      const docs = docsRes.data || [];
      for (const doc of docs.slice(0, 3)) {
        try { await api.post(`/flashcards/generate/${doc.id}`, null, { params: { count: 3 } }); } catch (e) {}
      }
      fetchDueCards();
    } catch (e) { }
    finally { setLoading(false); }
  };

  if (loading) return <Box textAlign="center" py={10}><CircularProgress /></Box>;

  if (cards.length === 0 && !done) {
    return (
      <Box textAlign="center" py={10} sx={{ opacity: 0.6 }}>
        <SpeedIcon sx={{ fontSize: 80, mb: 2, color: 'text.disabled' }} />
        <Typography variant="h5" gutterBottom>No Flashcards Due</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>All caught up! Generate flashcards from your papers.</Typography>
        <Button variant="contained" startIcon={<AIIcon />} onClick={handleGenerateFlashcards}>Generate from Recent Papers</Button>
        {stats && (
          <Paper sx={{ mt: 3, p: 2, maxWidth: 400, mx: 'auto' }}>
            <Typography variant="body2" color="text.secondary">
              {stats.total_cards} total cards · {stats.due_for_review} due · {stats.reviewed_today} reviewed today
              <br />Mastery: {stats.mastery_rate}% · Avg Ease: {stats.average_ease}
            </Typography>
            <LinearProgress variant="determinate" value={stats.mastery_rate || 0} sx={{ mt: 1, height: 6, borderRadius: 3 }} />
          </Paper>
        )}
      </Box>
    );
  }

  if (done) {
    return (
      <Box textAlign="center" py={10}>
        <Typography variant="h4" gutterBottom>🎉 Session Complete!</Typography>
        <Typography variant="h6" color="text.secondary">{sessionStats.reviewed} cards reviewed · {sessionStats.correct} correct</Typography>
        <Typography variant="body2" color="text.secondary">Accuracy: {sessionStats.reviewed > 0 ? Math.round(sessionStats.correct / sessionStats.reviewed * 100) : 0}%</Typography>
        <Button variant="contained" sx={{ mt: 3 }} onClick={fetchDueCards}>Review Again</Button>
      </Box>
    );
  }

  const card = cards[index];
  if (!card) return null;

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>🧠 Spaced Repetition</Typography>
        <Box>
          <Chip label={`${index + 1}/${cards.length}`} size="small" sx={{ mr: 1 }} />
          <Chip label={`${stats?.mastery_rate || 0}% mastery`} size="small" variant="outlined" />
        </Box>
      </Box>

      <LinearProgress variant="determinate" value={(index / cards.length) * 100} sx={{ mb: 3, height: 6, borderRadius: 3 }} />

      {/* Flashcard */}
      <Card sx={{ minHeight: 300, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        onClick={() => setFlipped(!flipped)}>
        <CardContent sx={{ textAlign: 'center', py: 6 }}>
          <IconButton sx={{ mb: 2 }}><FlipIcon /></IconButton>
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
            {flipped ? '💡 Answer' : '❓ Question'}
          </Typography>
          <Typography variant="body1" sx={{ fontSize: '1.2rem', lineHeight: 1.8, whiteSpace: 'pre-wrap', maxWidth: 500, mx: 'auto' }}>
            {flipped ? card.back : card.front}
          </Typography>
          {!flipped && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
              Click to reveal answer
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Quality Rating */}
      {flipped && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" align="center" gutterBottom>How well did you know this?</Typography>
          <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap">
            {QUALITY_LABELS.map((label, q) => (
              <Button key={q} variant={q < 3 ? 'outlined' : 'contained'}
                color={q < 2 ? 'error' : q < 3 ? 'warning' : q < 4 ? 'info' : 'success'}
                size="small" onClick={() => handleReview(q)} sx={{ minWidth: 80 }}>
                {label}
              </Button>
            ))}
          </Stack>
        </Box>
      )}

      {/* Stats */}
      <Paper sx={{ p: 1.5, mt: 2 }}>
        <Stack direction="row" spacing={3} justifyContent="center">
          <Typography variant="caption">Interval: {card.interval || 0}d</Typography>
          <Typography variant="caption">Repetitions: {card.repetitions || 0}</Typography>
          <Typography variant="caption">Ease: {card.ease || 250}%</Typography>
        </Stack>
      </Paper>
    </Box>
  );
};

export default FlashcardReview;
