import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, TextField, Button, Card, CardContent, Chip, IconButton, CircularProgress, Tabs, Tab, Stack, Divider, Alert, Snackbar } from '@mui/material';
import { AutoAwesome as AIIcon, ThumbUp as UpvoteIcon, Chat as DiscussIcon, Psychology as InsightIcon, QuestionAnswer as QAIcon } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

const ScholarInsights = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [discussions, setDiscussions] = useState({ threads: [] });
  const [synthesis, setSynthesis] = useState(null);
  const [newContent, setNewContent] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [notify, setNotify] = useState({ open: false, msg: '' });

  useEffect(() => { if (id) fetchData(); }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [discRes, synRes] = await Promise.all([
        api.get(`/discussions/${id}`),
        api.get(`/perspectives/${id}/synthesize`),
      ]);
      setDiscussions(discRes.data || { threads: [] });
      setSynthesis(synRes.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleAddDiscussion = async () => {
    if (!newContent.trim()) return;
    try {
      await api.post(`/discussions/${id}`, null, { params: {
        content: newContent, title: newTitle || newContent.slice(0, 50),
        discussion_type: tab === 0 ? 'insight' : tab === 1 ? 'critique' : 'question',
        is_question: tab === 2,
      }});
      setNewContent(''); setNewTitle('');
      setNotify({ open: true, msg: 'Perspective shared!' });
      fetchData();
    } catch (e) { setNotify({ open: true, msg: 'Failed to share' }); }
  };

  const handleUpvote = async (discId) => {
    try { await api.post(`/discussions/${discId}/vote`); fetchData(); } catch (e) {}
  };

  if (!id) return <Box textAlign="center" py={10}>Select a paper to view scholar insights.</Box>;

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
        <InsightIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Scholar Perspectives
      </Typography>

      {loading ? <CircularProgress /> : (
        <Box>
          {/* AI Synthesis Card */}
          {synthesis?.synthesis && (
            <Card variant="outlined" sx={{ mb: 3, bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AIIcon /> AI Perspective Synthesis
                </Typography>
                <Typography variant="body2" sx={{ lineHeight: 1.7 }}>
                  <ReactMarkdown>{synthesis.synthesis}</ReactMarkdown>
                </Typography>
                <Typography variant="caption" sx={{ mt: 1, display: 'block', opacity: 0.7 }}>
                  Synthesized from {synthesis.discussion_count} discussions and {synthesis.annotation_count} annotations
                </Typography>
              </CardContent>
            </Card>
          )}

          <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
            <Tab icon={<InsightIcon />} label="Insights" />
            <Tab icon={<DiscussIcon />} label="Critiques" />
            <Tab icon={<QAIcon />} label="Questions" />
          </Tabs>

          {/* Add New */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <TextField fullWidth size="small" placeholder={tab === 0 ? "Share an insight about this paper..." : tab === 1 ? "Add a critique or methodology note..." : "Ask a question about this paper..."}
              value={newContent} onChange={e => setNewContent(e.target.value)} multiline rows={2} sx={{ mb: 1 }} />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField size="small" placeholder="Title (optional)" value={newTitle} onChange={e => setNewTitle(e.target.value)} sx={{ flex: 1 }} />
              <Button variant="contained" size="small" onClick={handleAddDiscussion} disabled={!newContent.trim()}>Share</Button>
            </Box>
          </Paper>

          {/* Discussion Threads */}
          <Stack spacing={1.5}>
            {discussions.threads?.length === 0 && <Typography color="text.secondary" sx={{ textAlign: 'center', py: 5, fontStyle: 'italic' }}>No discussions yet. Be the first to share your perspective!</Typography>}
            {discussions.threads.map((thread, i) => (
              <Card key={i} variant="outlined">
                <CardContent sx={{ py: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>{thread.title}</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{thread.content}</Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Chip label={thread.type} size="small" variant="outlined" />
                        {thread.is_question && <Chip label="Question" size="small" color="primary" variant="outlined" />}
                        {thread.tags?.map((t, j) => <Chip key={j} label={t} size="small" variant="outlined" />)}
                      </Box>
                    </Box>
                    <IconButton size="small" onClick={() => handleUpvote(thread.id)}>
                      <UpvoteIcon fontSize="small" /> {thread.upvotes || 0}
                    </IconButton>
                  </Box>
                  {thread.replies?.length > 0 && (
                    <Box sx={{ ml: 4, mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      {thread.replies.map((r, j) => (
                        <Typography key={j} variant="caption" display="block" sx={{ mb: 0.5 }}>↳ {r.content}</Typography>
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}

      <Snackbar open={notify.open} autoHideDuration={3000} onClose={() => setNotify({ open: false })} message={notify.msg} />
    </Box>
  );
};

export default ScholarInsights;
