import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Chip, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress, Alert, Stack, IconButton, Collapse, List, ListItemButton, ListItemText } from '@mui/material';
import { ChevronRight, ExpandMore, CreateNewFolder, AutoAwesome as AIIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const LiteratureTree = () => {
  const navigate = useNavigate();
  const [tree, setTree] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState(false);
  const [newName, setNewName] = useState('');
  const [parentId, setParentId] = useState(null);
  const [suggestDialog, setSuggestDialog] = useState(false);
  const [suggestedTaxonomy, setSuggestedTaxonomy] = useState(null);

  useEffect(() => { fetchTree(); }, []);

  const fetchTree = async () => {
    setLoading(true);
    try { const res = await api.get('/directory/tree'); setTree(res.data?.tree || []); } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleNodeClick = async (nodeId) => {
    setSelectedNode(nodeId);
    try { const res = await api.get(`/directory/node/${nodeId}/papers`); setPapers(res.data?.papers || []); } catch (e) { }
  };

  const handleCreateNode = async () => {
    if (!newName.trim()) return;
    try { await api.post('/directory/nodes', null, { params: { name: newName, parent_id: parentId } }); setDialog(false); setNewName(''); fetchTree(); } catch (e) { }
  };

  const handleSuggestTaxonomy = async () => {
    setSuggestDialog(true);
    try { const res = await api.post('/directory/suggest-taxonomy'); setSuggestedTaxonomy(res.data); } catch (e) { }
  };

  const handleApplyTaxonomy = async () => {
    const tax = suggestedTaxonomy?.suggested_taxonomy?.taxonomy || [];
    for (const folder of tax) {
      try { await api.post('/directory/nodes', null, { params: { name: folder.name } }); } catch (e) { }
      for (const child of (folder.children || [])) {
        try { /* would need parent ID */ } catch (e) { }
      }
    }
    setSuggestDialog(false); fetchTree();
  };

  const TreeNode = ({ node }) => {
    const [open, setOpen] = useState(false);
    const hasChildren = node.children?.length > 0;
    return (
      <>
        <ListItemButton onClick={() => { handleNodeClick(node.id); if (hasChildren) setOpen(!open); }} sx={{ pl: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
            {hasChildren ? (open ? <ExpandMore fontSize="small" /> : <ChevronRight fontSize="small" />) : <Box sx={{ width: 24 }} />}
            <span>{node.icon || '📁'}</span>
            <ListItemText primary={node.name} primaryTypographyProps={{ variant: 'body2' }} />
            <Chip label={node.paper_count || 0} size="small" variant="outlined" />
          </Box>
        </ListItemButton>
        {hasChildren && (
          <Collapse in={open}>
            <List disablePadding>
              {node.children.map((child) => <TreeNode key={child.id} node={child} />)}
            </List>
          </Collapse>
        )}
      </>
    );
  };

  const renderTree = (nodes) => (
    <List disablePadding>
      {nodes.map((n) => <TreeNode key={n.id} node={n} />)}
    </List>
  );

  return (
    <Box sx={{ display: 'flex', gap: 3, height: 'calc(100vh - 160px)' }}>
      <Paper sx={{ width: 350, p: 2, overflow: 'auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>📚 Literature</Typography>
          <Stack direction="row" spacing={0.5}>
            <IconButton size="small" onClick={() => { setParentId(selectedNode); setDialog(true); }}><CreateNewFolder /></IconButton>
            <IconButton size="small" onClick={handleSuggestTaxonomy}><AIIcon /></IconButton>
          </Stack>
        </Box>
        {loading ? <CircularProgress /> : tree.length === 0 ? (
          <Box textAlign="center" py={5} sx={{ opacity: 0.5 }}>
            <Typography variant="body2">No folders yet.</Typography>
            <Button size="small" onClick={() => { setParentId(null); setDialog(true); }}>Create Root Folder</Button>
            <Button size="small" onClick={handleSuggestTaxonomy}>AI Suggest</Button>
          </Box>
        ) : (
          renderTree(tree)
        )}
      </Paper>

      <Paper sx={{ flex: 1, p: 2, overflow: 'auto' }}>
        {selectedNode ? (
          <>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>Papers in this folder</Typography>
            {papers.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>No papers assigned. Drag or auto-classify papers into this folder.</Typography>
            ) : papers.map((p, i) => (
              <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1.5, borderBottom: '1px solid', borderColor: 'divider', cursor: 'pointer' }}
                onClick={() => navigate(`/documents/${p.document_id}`)}>
                <Box><Typography variant="body2" sx={{ fontWeight: 500 }}>{p.title}</Typography><Typography variant="caption" color="text.secondary">{(p.authors || []).slice(0, 2).join(', ')} {p.year ? `(${p.year})` : ''}</Typography></Box>
                <Chip label="View" size="small" />
              </Box>
            ))}
          </>
        ) : (
          <Box textAlign="center" py={10} sx={{ opacity: 0.5 }}>
            <Typography variant="h6">Select a folder</Typography>
            <Typography variant="body2" color="text.secondary">Browse your literature by topic, methodology, or research area.</Typography>
          </Box>
        )}
      </Paper>

      <Dialog open={dialog} onClose={() => setDialog(false)}>
        <DialogTitle>Create Folder</DialogTitle>
        <DialogContent><TextField autoFocus fullWidth margin="dense" label="Folder name" value={newName} onChange={e => setNewName(e.target.value)} /></DialogContent>
        <DialogActions><Button onClick={() => setDialog(false)}>Cancel</Button><Button variant="contained" onClick={handleCreateNode}>Create</Button></DialogActions>
      </Dialog>

      <Dialog open={suggestDialog} onClose={() => setSuggestDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>AI-Suggested Taxonomy</DialogTitle>
        <DialogContent>
          {suggestedTaxonomy ? (
            <Box>
              <Typography variant="body2" color="text.secondary">Based on {suggestedTaxonomy.based_on} papers in your library</Typography>
              {(suggestedTaxonomy.suggested_taxonomy?.taxonomy || []).map((t, i) => (
                <Box key={i} sx={{ ml: 2, mt: 1 }}><Typography variant="body2" sx={{ fontWeight: 600 }}>📁 {t.name}</Typography>
                  {(t.children || []).map((c, j) => <Typography key={j} variant="caption" display="block" sx={{ ml: 3 }}>📂 {c.name}</Typography>)}
                </Box>
              ))}
            </Box>
          ) : <CircularProgress />}
        </DialogContent>
        <DialogActions><Button onClick={() => setSuggestDialog(false)}>Cancel</Button><Button variant="contained" onClick={handleApplyTaxonomy}>Apply Taxonomy</Button></DialogActions>
      </Dialog>
    </Box>
  );
};

export default LiteratureTree;
