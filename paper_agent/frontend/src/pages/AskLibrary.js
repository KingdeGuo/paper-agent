import React, { useState, useRef, useEffect } from 'react';
import {
  Box, Typography, TextField, Button, Paper, Chip, CircularProgress,
  Card, CardContent, IconButton, Avatar, Stack, Divider, Alert,
} from '@mui/material';
import {
  Send as SendIcon, AutoAwesome as AIIcon, SmartToy as BotIcon,
  Person as PersonIcon, ContentCopy as CopyIcon, OpenInNew as LinkIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const AskLibrary = () => {
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState([]);
  const [streamingText, setStreamingText] = useState('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleAsk = async () => {
    if (!question.trim() || loading) return;

    const userMsg = { role: 'user', content: question.trim() };
    setMessages(prev => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);
    setStreamingText('');
    setSources([]);

    try {
      const res = await api.post('/ask/', { question: userMsg.content, limit: 8, threshold: 0.6 });
      const data = res.data;
      setSources(data.sources || []);
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, sources: data.sources || [] }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error searching your library. Please try again.', sources: [] }]);
    }
    finally { setLoading(false); setStreamingText(''); }
  };

  const handleStreamAsk = async () => {
    if (!question.trim() || loading) return;

    const userMsg = { role: 'user', content: question.trim() };
    setMessages(prev => [...prev, userMsg]);
    const q = question.trim();
    setQuestion('');
    setLoading(true);
    setStreamingText('');
    setSources([]);

    try {
      const token = localStorage.getItem('token');
      const resp = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ question: q, limit: 8, threshold: 0.6 }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let msgSources = [];
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'sources') { msgSources = data.sources || []; setSources(msgSources); }
            else if (data.type === 'chunk') { fullText += data.content; setStreamingText(fullText); }
            else if (data.type === 'done') {
              setMessages(prev => [...prev, { role: 'assistant', content: fullText, sources: msgSources }]);
              setStreamingText('');
            }
          } catch (e) { /* skip malformed */ }
        }
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Streaming failed. Try a simpler question.', sources: [] }]);
    }
    finally { setLoading(false); setStreamingText(''); }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleStreamAsk(); } };

  return (
    <Box sx={{ display: 'flex', gap: 3, height: 'calc(100vh - 140px)' }}>
      {/* Chat Area */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
          <AIIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Ask My Library
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Ask questions in natural language. The AI searches across your entire library and synthesizes answers with citations.
        </Typography>

        <Box sx={{ flex: 1, overflow: 'auto', mb: 2, px: 1 }}>
          {messages.length === 0 && !loading && (
            <Box textAlign="center" py={10} sx={{ opacity: 0.6 }}>
              <BotIcon sx={{ fontSize: 80, mb: 2, color: 'primary.light' }} />
              <Typography variant="h6" color="text.secondary">What would you like to know?</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Try: "What are the main methods used in my papers on transformer efficiency?"
              </Typography>
              <Stack direction="row" spacing={1} justifyContent="center" sx={{ mt: 2 }}>
                {[
                  'What methodology do my papers use?',
                  'Are there contradictions in my library?',
                  'Summarize key findings on attention mechanisms',
                ].map((s, i) => (
                  <Chip key={i} label={s} variant="outlined" size="small" onClick={() => { setQuestion(s); }} sx={{ cursor: 'pointer' }} />
                ))}
              </Stack>
            </Box>
          )}

          {messages.map((msg, i) => (
            <Box key={i} sx={{ mb: 2, display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <Card variant={msg.role === 'user' ? 'elevation' : 'outlined'}
                sx={{ maxWidth: '85%', bgcolor: msg.role === 'user' ? 'primary.main' : 'background.paper', color: msg.role === 'user' ? 'white' : 'text.primary', borderRadius: 3 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  {msg.role === 'user' ? (
                    <Typography variant="body2">{msg.content}</Typography>
                  ) : (
                    <>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{msg.content}</Typography>
                      {msg.sources?.length > 0 && (
                        <Box sx={{ mt: 1.5, pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                          <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>Sources:</Typography>
                          <Stack direction="row" spacing={0.5} flexWrap="wrap">
                            {msg.sources.map((s, j) => (
                              <Chip key={j} label={s.title?.slice(0, 30) + (s.title?.length > 30 ? '...' : '')}
                                size="small" variant="outlined" onClick={() => navigate(`/documents/${s.document_id}`)}
                                sx={{ cursor: 'pointer', mb: 0.5 }} />
                            ))}
                          </Stack>
                        </Box>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </Box>
          ))}

          {streamingText && (
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-start' }}>
              <Card variant="outlined" sx={{ maxWidth: '85%', borderRadius: 3 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{streamingText}</Typography>
                  {sources.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>Searching sources: </Typography>
                      {sources.map((s, j) => (
                        <Chip key={j} label={s.title?.slice(0, 20)} size="small" variant="outlined" sx={{ ml: 0.5 }} />
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}
          {loading && !streamingText && <Box textAlign="center" py={2}><CircularProgress size={24} /><Typography variant="caption" ml={1}>Searching your library...</Typography></Box>}
          <div ref={chatEndRef} />
        </Box>

        <Paper elevation={3} sx={{ p: 2, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField fullWidth size="small" placeholder="Ask a question about your research library..."
              value={question} onChange={e => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown} disabled={loading}
              multiline maxRows={3} />
            <IconButton color="primary" onClick={handleStreamAsk} disabled={!question.trim() || loading}>
              {loading ? <CircularProgress size={24} /> : <SendIcon />}
            </IconButton>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default AskLibrary;
