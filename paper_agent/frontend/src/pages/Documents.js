import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CompareArrows as CompareIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import { documentsAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { Checkbox } from '@mui/material';

const Documents = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);

  const handleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleCompare = () => {
    if (selectedIds.length < 2) return;
    navigate('/comparison', { state: { selectedIds } });
  };
  
  const handleDistill = () => {
    if (selectedIds.length < 2) return;
    navigate('/discovery', { state: { selectedIds } });
  };

  const [uploadDialog, setUploadDialog] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [metadata, setMetadata] = useState({
    title: '',
    authors: '',
    year: '',
    keywords: '',
  });

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await documentsAPI.getAll();
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    try {
      const metadataObj = {
        title: metadata.title || undefined,
        authors: metadata.authors ? metadata.authors.split(',').map(a => a.trim()) : undefined,
        year: metadata.year ? parseInt(metadata.year) : undefined,
        keywords: metadata.keywords ? metadata.keywords.split(',').map(k => k.trim()) : undefined,
      };

      await documentsAPI.upload(uploadFile, metadataObj);
      setUploadDialog(false);
      setUploadFile(null);
      setMetadata({ title: '', authors: '', year: '', keywords: '' });
      fetchDocuments();
    } catch (error) {
      console.error('Error uploading document:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm(t('documents.confirmDelete'))) {
      try {
        await documentsAPI.delete(id);
        fetchDocuments();
      } catch (error) {
        console.error('Error deleting document:', error);
      }
    }
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 0:
        return <Chip label={t('documents.processingStatus.pending')} color="default" size="small" />;
      case 1:
        return <Chip label={t('documents.processingStatus.processing')} color="warning" size="small" />;
      case 2:
        return <Chip label={t('documents.processingStatus.completed')} color="success" size="small" />;
      case 3:
        return <Chip label={t('documents.processingStatus.failed')} color="error" size="small" />;
      default:
        return <Chip label={t('documents.processingStatus.unknown')} size="small" />;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          {t('documents.title')}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {selectedIds.length >= 2 && (
            <>
              <Button
                variant="contained"
                color="secondary"
                startIcon={<CompareIcon />}
                onClick={handleCompare}
                sx={{ fontWeight: 'bold' }}
              >
                Compare ({selectedIds.length})
              </Button>
              <Button
                variant="contained"
                color="info"
                startIcon={<ScienceIcon />}
                onClick={handleDistill}
                sx={{ fontWeight: 'bold' }}
              >
                Distill
              </Button>
            </>
          )}
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialog(true)}
            sx={{ fontWeight: 'bold', ml: 1 }}
          >
            {t('documents.upload')}
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 3 }}>
        <Table>
          <TableHead sx={{ bgcolor: 'grey.50' }}>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedIds.length > 0 && selectedIds.length < documents.length}
                  checked={documents.length > 0 && selectedIds.length === documents.length}
                  onChange={() => {
                    if (selectedIds.length === documents.length) setSelectedIds([]);
                    else setSelectedIds(documents.map(d => d.id));
                  }}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>{t('documents.filename')}</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>{t('documents.titleField')}</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>{t('documents.authors')}</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>{t('documents.year')}</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>{t('documents.status')}</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>{t('documents.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.map((doc) => (
              <TableRow 
                key={doc.id} 
                hover 
                selected={selectedIds.includes(doc.id)}
                onClick={() => handleSelect(doc.id)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell padding="checkbox">
                  <Checkbox checked={selectedIds.includes(doc.id)} />
                </TableCell>
                <TableCell>{doc.filename}</TableCell>
                <TableCell sx={{ fontWeight: 'medium' }}>{doc.title || t('documents.noName')}</TableCell>
                <TableCell>{doc.authors?.slice(0, 2).join(', ')}{doc.authors?.length > 2 ? '...' : ''}</TableCell>
                <TableCell>{doc.year || '-'}</TableCell>
                <TableCell>{getStatusChip(doc.processed)}</TableCell>
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={() => navigate(`/documents/${doc.id}`)}
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = `/api/documents/${doc.id}/download`;
                      link.download = doc.filename;
                      link.click();
                    }}
                  >
                    <DownloadIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(doc.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('documents.uploadTitle')}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setUploadFile(e.target.files[0])}
              style={{ marginBottom: '20px' }}
            />
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('documents.titleField')}
                  value={metadata.title}
                  onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('documents.authors')}
                  helperText={t('documents.authorsSeparator')}
                  value={metadata.authors}
                  onChange={(e) => setMetadata({ ...metadata, authors: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('documents.year')}
                  type="number"
                  value={metadata.year}
                  onChange={(e) => setMetadata({ ...metadata, year: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('documents.keywords')}
                  helperText={t('documents.keywordsSeparator')}
                  value={metadata.keywords}
                  onChange={(e) => setMetadata({ ...metadata, keywords: e.target.value })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>{t('documents.cancel')}</Button>
          <Button onClick={handleUpload} variant="contained" disabled={!uploadFile}>
            {t('documents.upload')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Documents;
