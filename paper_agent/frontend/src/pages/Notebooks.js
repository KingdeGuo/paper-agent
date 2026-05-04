import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Grid, Paper, Card, CardContent, 
  Button, IconButton, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, List, ListItem, ListItemText,
  Divider, Chip, Tab, Tabs
} from '@mui/material';
import { 
  Book as NotebookIcon, 
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ChevronRight as ChevronRightIcon,
  AutoAwesome as MagicIcon
} from '@mui/icons-material';
import api from '../services/api';

const Notebooks = () => {
  const [notebooks, setNotebooks] = useState([]);
  const [selectedNotebook, setSelectedNotebook] = useState(null);
  const [entries, setEntries] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newNotebook, setNewNotebook] = useState({ title: '', description: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchNotebooks();
  }, []);

  const fetchNotebooks = async () => {
    try {
      const response = await api.get('/notebooks');
      setNotebooks(response.data);
      if (response.data.length > 0 && !selectedNotebook) {
        handleSelectNotebook(response.data[0]);
      }
    } catch (err) {
      console.error("Failed to fetch notebooks", err);
    }
  };

  const handleSelectNotebook = async (notebook) => {
    setSelectedNotebook(notebook);
    setLoading(true);
    try {
      const response = await api.get(`/notebooks/${notebook.id}/entries`);
      setEntries(response.data);
    } catch (err) {
      console.error("Failed to fetch entries", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNotebook = async () => {
    try {
      await api.post('/notebooks', newNotebook);
      setOpenDialog(false);
      setNewNotebook({ title: '', description: '' });
      fetchNotebooks();
    } catch (err) {
      console.error("Failed to create notebook", err);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {/* Notebook Sidebar */}
        <Grid item xs={12} md={3}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h5" fontWeight="bold">My Notebooks</Typography>
            <IconButton color="primary" onClick={() => setOpenDialog(true)}>
              <AddIcon />
            </IconButton>
          </Box>
          <Paper sx={{ height: '75vh', overflow: 'auto' }}>
            <List>
              {notebooks.map((nb) => (
                <ListItem 
                  button 
                  key={nb.id} 
                  selected={selectedNotebook?.id === nb.id}
                  onClick={() => handleSelectNotebook(nb)}
                  sx={{ mb: 1 }}
                >
                  <ListItemIcon>
                    <NotebookIcon color={selectedNotebook?.id === nb.id ? 'primary' : 'inherit'} />
                  </ListItemIcon>
                  <ListItemText primary={nb.title} />
                  <ChevronRightIcon fontSize="small" />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Entry Workspace */}
        <Grid item xs={12} md={9}>
          {selectedNotebook ? (
            <Box>
              <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">{selectedNotebook.title}</Typography>
                  <Typography variant="body1" color="text.secondary">{selectedNotebook.description}</Typography>
                </Box>
                <Button variant="outlined" startIcon={<MagicIcon />}>AI Synthesis</Button>
              </Box>

              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={2}>
                {entries.length === 0 ? (
                  <Box sx={{ width: '100%', textAlign: 'center', py: 10, opacity: 0.5 }}>
                    <Typography>No entries yet. Start adding notes or AI insights!</Typography>
                  </Box>
                ) : (
                  entries.map((entry) => (
                    <Grid item xs={12} key={entry.id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Chip 
                              label={entry.type.toUpperCase()} 
                              size="small" 
                              color={entry.type === 'note' ? 'default' : 'secondary'} 
                            />
                            <Typography variant="caption" color="text.secondary">
                              {new Date(entry.created_at).toLocaleString()}
                            </Typography>
                          </Box>
                          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                            {entry.content}
                          </Typography>
                          {entry.document_id && (
                            <Box sx={{ mt: 2 }}>
                              <Chip label="Linked Paper" variant="outlined" size="small" />
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))
                )}
              </Grid>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 20, opacity: 0.5 }}>
              <NotebookIcon sx={{ fontSize: 100, mb: 2 }} />
              <Typography variant="h5">Select a notebook to begin</Typography>
            </Box>
          )}
        </Grid>
      </Grid>

      {/* Create Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Create New Notebook</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Title"
            fullWidth
            variant="outlined"
            value={newNotebook.title}
            onChange={(e) => setNewNotebook({ ...newNotebook, title: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newNotebook.description}
            onChange={(e) => setNewNotebook({ ...newNotebook, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateNotebook} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Notebooks;
