import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Button, Paper, TextField, Alert, 
  List, ListItem, ListItemText, ListItemIcon, Divider,
  CircularProgress, IconButton, Chip
} from '@mui/material';
import { 
  Link as LinkIcon, 
  Refresh as RefreshIcon,
  CloudDownload as DownloadIcon,
  Folder as FolderIcon,
  Article as ArticleIcon
} from '@mui/icons-material';
import api from '../services/api';

const Zotero = () => {
  const [connected, setConnected] = useState(false);
  const [creds, setCreds] = useState({ zotero_user_id: '', api_key: '' });
  const [collections, setCollections] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const response = await api.get('/zotero/collections');
      setCollections(response.data);
      setConnected(true);
    } catch (err) {
      setConnected(false);
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    try {
      await api.post('/zotero/connect', creds);
      setStatus({ type: 'success', message: 'Zotero connected!' });
      setConnected(true);
      checkConnection();
    } catch (err) {
      setStatus({ type: 'error', message: 'Connection failed. Check your ID and API Key.' });
    } finally {
      setLoading(false);
    }
  };

  const importItem = async (itemKey) => {
    try {
      setStatus({ type: 'info', message: 'Importing paper...' });
      await api.post(`/zotero/import/${itemKey}`);
      setStatus({ type: 'success', message: 'Paper imported successfully!' });
    } catch (err) {
      setStatus({ type: 'error', message: 'Import failed.' });
    }
  };

  if (!connected) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', mt: 10 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold">Connect to Zotero</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Sync your Zotero library to analyze your existing papers with AI.
          </Typography>
          <TextField
            fullWidth
            label="Zotero User ID"
            margin="normal"
            value={creds.zotero_user_id}
            onChange={(e) => setCreds({ ...creds, zotero_user_id: e.target.value })}
            helperText="Found in Zotero settings -> Feeds/API"
          />
          <TextField
            fullWidth
            label="API Key"
            type="password"
            margin="normal"
            value={creds.api_key}
            onChange={(e) => setCreds({ ...creds, api_key: e.target.value })}
          />
          <Button 
            variant="contained" 
            fullWidth 
            sx={{ mt: 3 }} 
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Connect Library'}
          </Button>
          {status && <Alert severity={status.type} sx={{ mt: 2 }}>{status.message}</Alert>}
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">Zotero Integration</Typography>
      
      {status && <Alert severity={status.type} sx={{ mb: 2 }} onClose={() => setStatus(null)}>{status.message}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Collections</Typography>
            <List>
              {collections.map((col) => (
                <ListItem button key={col.key}>
                  <ListItemIcon><FolderIcon color="primary" /></ListItemIcon>
                  <ListItemText primary={col.data.name} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Papers in Library</Typography>
              <Button startIcon={<RefreshIcon />} size="small">Sync All</Button>
            </Box>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Only items with valid metadata and PDF attachments will be processed.
            </Alert>
            {/* Real items would be fetched here based on collection click */}
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 5 }}>
              Select a collection to view papers and import them into Paper Agent.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Zotero;
