import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, TextField, Button, Paper, Chip, CircularProgress, IconButton, Stack, Drawer, List, ListItem, ListItemText, Divider, Alert, Avatar } from '@mui/material';
import { Send as SendIcon, SmartToy as BotIcon, Person as PersonIcon, Add as AddIcon, Delete as DeleteIcon, Chat as ChatIcon } from '@mui/icons-material';
import api from '../services/api';

const ResearchChat = () => {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const chatEndRef = useRef(null);

  useEffect(() => { fetchSessions(); }, []);

  useEffect(() => {
    if (activeSession) fetchMessages(activeSession.id);
  }, [activeSession]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const fetchSessions = async () => {
    try { const res = await api.get('/chat/sessions'); setSessions(res.data || []);
      if (!activeSession && res.data?.length > 0) setActiveSession(res.data[0]);
    } catch (e) {}
  };

  const fetchMessages = async (sid) => {
    try { const res = await api.get(`/chat/sessions/${sid}/messages`); setMessages(res.data || []); } catch (e) { setMessages([]); }
  };

  const handleNewSession = async () => {
    try { const res = await api.post('/chat/sessions', null, { params: { title: `Research Chat ${sessions.length + 1}` } });
      setActiveSession(res.data); fetchSessions();
    } catch (e) {}
  };

  const handleDeleteSession = async (sid) => {
    try { await api.delete(`/chat/sessions/${sid}`); if (activeSession?.id === sid) setActiveSession(null); fetchSessions(); } catch (e) {}
  };

  const handleSend = async () => {
    if (!input.trim() || !activeSession) return;
    const q = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setLoading(true);
    try {
      const res = await api.post(`/chat/sessions/${activeSession.id}/ask`, null, { params: { question: q } });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data?.answer || '', sources: res.data?.sources || [] }]);
      fetchSessions();
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
    }
    finally { setLoading(false); }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 150px)', gap: 2 }}>
      {/* Session Sidebar */}
      <Drawer variant="persistent" open={sidebarOpen} sx={{ '& .MuiDrawer-paper': { width: 280, position: 'static', p: 2, boxSizing: 'border-box' } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>💬 Chats</Typography>
          <IconButton size="small" onClick={handleNewSession}><AddIcon /></IconButton>
        </Box>
        {sessions.length === 0 && <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>No chats yet. Start one!</Typography>}
        <List dense>
          {sessions.map(s => (
            <ListItem key={s.id} button selected={activeSession?.id === s.id}
              onClick={() => setActiveSession(s)}
              secondaryAction={<IconButton edge="end" size="small" onClick={() => handleDeleteSession(s.id)}><DeleteIcon fontSize="small" /></IconButton>}>
              <ListItemText primary={s.title} secondary={`${s.message_count || 0} messages`} primaryTypographyProps={{ variant: 'body2', noWrap: true }} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Chat Area */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {activeSession ? (
          <>
            <Box sx={{ flex: 1, overflow: 'auto', px: 2, py: 1 }}>
              {messages.length === 0 && !loading && (
                <Box textAlign="center" py={10} sx={{ opacity: 0.6 }}>
                  <BotIcon sx={{ fontSize: 80, mb: 2, color: 'primary.light' }} />
                  <Typography variant="h6" color="text.secondary">Ask anything about your research</Typography>
                  <Typography variant="body2" color="text.secondary">Search papers, get summaries, compare findings, explore ideas.</Typography>
                </Box>
              )}
              {messages.map((msg, i) => (
                <Box key={i} sx={{ mb: 2, display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  <Paper elevation={msg.role === 'user' ? 2 : 0} sx={{
                    maxWidth: '80%', p: 2, borderRadius: 3,
                    bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.50',
                    color: msg.role === 'user' ? 'white' : 'text.primary',
                    border: msg.role === 'user' ? 'none' : '1px solid',
                    borderColor: 'divider',
                  }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{msg.content}</Typography>
                    {msg.sources?.length > 0 && (
                      <Box sx={{ mt: 1.5, pt: 1, borderTop: '1px solid', borderColor: msg.role === 'user' ? 'rgba(255,255,255,0.3)' : 'divider' }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5, opacity: 0.8 }}>Sources:</Typography>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap">
                          {msg.sources.map((s, j) => (
                            <Chip key={j} label={s.title?.slice(0, 25) + (s.title?.length > 25 ? '...' : '')} size="small" variant="outlined"
                              onClick={() => window.open(`/documents/${s.document_id}`, '_blank')} sx={{ cursor: 'pointer', mb: 0.3 }} />
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </Paper>
                </Box>
              ))}
              {loading && <Box textAlign="center" py={2}><CircularProgress size={24} /><Typography variant="caption" ml={1}>Thinking...</Typography></Box>}
              <div ref={chatEndRef} />
            </Box>
            <Paper elevation={3} sx={{ p: 2, borderRadius: 3 }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField fullWidth size="small" placeholder="Ask about your papers, search for insights, compare findings..."
                  value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown} disabled={loading} multiline maxRows={3} />
                <IconButton color="primary" onClick={handleSend} disabled={!input.trim() || loading}>
                  {loading ? <CircularProgress size={24} /> : <SendIcon />}
                </IconButton>
              </Box>
            </Paper>
          </>
        ) : (
          <Box textAlign="center" py={15} sx={{ opacity: 0.5 }}>
            <ChatIcon sx={{ fontSize: 80, mb: 2, color: 'text.disabled' }} />
            <Typography variant="h6" color="text.secondary">Start a Research Chat</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Create a new chat session to begin.</Typography>
            <Button variant="contained" sx={{ mt: 2 }} onClick={handleNewSession}>New Chat</Button>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ResearchChat;
