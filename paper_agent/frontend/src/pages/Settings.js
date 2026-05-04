import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, TextField, Button, Card, CardContent,
  Divider, Switch, FormControlLabel, Select, MenuItem, FormControl,
  InputLabel, Snackbar, Alert, CircularProgress, Dialog, DialogTitle,
  DialogContent, DialogActions, Chip, Stack, Avatar, IconButton,
} from '@mui/material';
import {
  Person as PersonIcon, Key as KeyIcon, DarkMode as ThemeIcon,
  Language as LangIcon, Delete as DeleteIcon, Add as AddIcon,
  ContentCopy as CopyIcon, Visibility as ViewIcon,
  VisibilityOff as HideIcon, Security as SecurityIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const Settings = () => {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const [tab, setTab] = useState('profile');
  const [profile, setProfile] = useState({ username: '', email: '', full_name: '' });
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [showKey, setShowKey] = useState({});
  const [saving, setSaving] = useState(false);
  const [notify, setNotify] = useState({ open: false, msg: '', severity: 'success' });
  const [keyDialog, setKeyDialog] = useState(false);

  useEffect(() => {
    setProfile({ username: user?.username || '', email: user?.email || '', full_name: user?.full_name || '' });
    fetchApiKeys();
  }, [user]);

  const fetchApiKeys = async () => {
    try {
      const res = await api.get('/users/api-keys');
      setApiKeys(res.data || []);
    } catch (e) { /* ignore */ }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await api.put('/users/me', profile);
      setNotify({ open: true, msg: 'Profile updated', severity: 'success' });
    } catch (e) {
      setNotify({ open: true, msg: 'Failed to save', severity: 'error' });
    }
    finally { setSaving(false); }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) return;
    try {
      const res = await api.post('/users/api-keys', { name: newKeyName });
      setNewKeyResult(res.data);
      setNewKeyName('');
      fetchApiKeys();
    } catch (e) {
      setNotify({ open: true, msg: 'Failed to create API key', severity: 'error' });
    }
  };

  const handleDeleteApiKey = async (keyId) => {
    try {
      await api.delete(`/users/api-keys/${keyId}`);
      setNotify({ open: true, msg: 'API key deleted', severity: 'info' });
      fetchApiKeys();
    } catch (e) { console.error(e); }
  };

  const handleLanguageChange = (lang) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('i18nextLng', lang);
  };

  const TabButton = ({ value, label, icon }) => (
    <Button
      fullWidth variant={tab === value ? 'contained' : 'text'}
      startIcon={icon} onClick={() => setTab(value)}
      sx={{ justifyContent: 'flex-start', mb: 0.5, textTransform: 'none' }}
    >{label}</Button>
  );

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto' }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>Settings</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 1.5 }}>
            <TabButton value="profile" label="Profile" icon={<PersonIcon />} />
            <TabButton value="security" label="API Keys" icon={<KeyIcon />} />
            <TabButton value="preferences" label="Preferences" icon={<ThemeIcon />} />
          </Paper>
        </Grid>

        <Grid item xs={12} md={9}>
          {tab === 'profile' && (
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', fontSize: 28 }}>
                  {(profile.full_name || profile.username || 'U')[0].toUpperCase()}
                </Avatar>
                <Box>
                  <Typography variant="h6">{profile.full_name || profile.username || 'User'}</Typography>
                  <Typography variant="body2" color="text.secondary">{profile.email || 'No email'}</Typography>
                </Box>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12}><TextField fullWidth label="Username" value={profile.username} onChange={e => setProfile({ ...profile, username: e.target.value })} /></Grid>
                <Grid item xs={12} sm={6}><TextField fullWidth label="Full Name" value={profile.full_name} onChange={e => setProfile({ ...profile, full_name: e.target.value })} /></Grid>
                <Grid item xs={12} sm={6}><TextField fullWidth label="Email" type="email" value={profile.email} onChange={e => setProfile({ ...profile, email: e.target.value })} /></Grid>
                <Grid item xs={12}>
                  <Button variant="contained" onClick={handleSaveProfile} disabled={saving}>
                    {saving ? <CircularProgress size={20} /> : 'Save Changes'}
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          )}

          {tab === 'security' && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <KeyIcon /> API Keys
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                API keys allow programmatic access to your Paper Agent library. Keep them secure.
              </Typography>

              <Stack spacing={1.5} sx={{ mb: 3 }}>
                {apiKeys.length === 0 && <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>No API keys yet.</Typography>}
                {apiKeys.map((key) => (
                  <Card key={key.id} variant="outlined">
                    <CardContent sx={{ py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>{key.name || 'API Key'}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {showKey[key.id] ? key.full_key || key.key : (key.key_prefix || `${key.key?.slice(0, 12)}...`)}
                        </Typography>
                      </Box>
                      <Box>
                        <IconButton size="small" onClick={() => setShowKey({ ...showKey, [key.id]: !showKey[key.id] })}>
                          {showKey[key.id] ? <HideIcon /> : <ViewIcon />}
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDeleteApiKey(key.id)}><DeleteIcon /></IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Stack>

              <Button variant="outlined" startIcon={<AddIcon />} onClick={() => setKeyDialog(true)}>Create API Key</Button>

              <Dialog open={keyDialog} onClose={() => setKeyDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Create API Key</DialogTitle>
                <DialogContent>
                  {newKeyResult ? (
                    <Box>
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        Copy this key now. You won't be able to see it again!
                      </Alert>
                      <TextField fullWidth value={newKeyResult.full_key || newKeyResult.key} InputProps={{
                        readOnly: true,
                        endAdornment: <IconButton onClick={() => navigator.clipboard.writeText(newKeyResult.full_key || newKeyResult.key)}><CopyIcon /></IconButton>
                      }} />
                    </Box>
                  ) : (
                    <TextField autoFocus fullWidth margin="dense" label="Key Name"
                      value={newKeyName} onChange={e => setNewKeyName(e.target.value)}
                      placeholder="e.g. Development, CI/CD" />
                  )}
                </DialogContent>
                <DialogActions>
                  <Button onClick={() => { setKeyDialog(false); setNewKeyResult(null); }}>Close</Button>
                  {!newKeyResult && <Button variant="contained" onClick={handleCreateApiKey}>Create</Button>}
                </DialogActions>
              </Dialog>
            </Paper>
          )}

          {tab === 'preferences' && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>Preferences</Typography>
              <Stack spacing={3}>
                <Box>
                  <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><LangIcon /> Language</Typography>
                  <FormControl size="small">
                    <Select value={i18n.language || 'en'} onChange={e => handleLanguageChange(e.target.value)}>
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="zh">中文 (Chinese)</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                <Divider />
                <Box>
                  <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><SecurityIcon /> Default Privacy</Typography>
                  <FormControlLabel control={<Switch defaultChecked />} label="Show document titles in search results" />
                </Box>
                <Divider />
                <Box>
                  <Button variant="outlined" color="error" onClick={logout}>Logout</Button>
                </Box>
              </Stack>
            </Paper>
          )}
        </Grid>
      </Grid>

      <Snackbar open={notify.open} autoHideDuration={4000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
