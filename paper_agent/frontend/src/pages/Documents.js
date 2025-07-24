import React, { useState, useEffect } from 'react';
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
} from '@mui/icons-material';
import { documentsAPI } from '../services/api';

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
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
    if (window.confirm('确定要删除这个文献吗？')) {
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
        return <Chip label="待处理" color="default" size="small" />;
      case 1:
        return <Chip label="处理中" color="warning" size="small" />;
      case 2:
        return <Chip label="已完成" color="success" size="small" />;
      case 3:
        return <Chip label="失败" color="error" size="small" />;
      default:
        return <Chip label="未知" size="small" />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        文献管理
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialog(true)}
        >
          上传文献
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>文件名</TableCell>
              <TableCell>标题</TableCell>
              <TableCell>作者</TableCell>
              <TableCell>年份</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>上传时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell>{doc.filename}</TableCell>
                <TableCell>{doc.title || '未命名'}</TableCell>
                <TableCell>{doc.authors?.join(', ') || '未知'}</TableCell>
                <TableCell>{doc.year || '未知'}</TableCell>
                <TableCell>{getStatusChip(doc.processed)}</TableCell>
                <TableCell>
                  {new Date(doc.upload_date).toLocaleString('zh-CN')}
                </TableCell>
                <TableCell>
                  <IconButton
                    color="primary"
                    onClick={() => window.open(`/documents/${doc.id}`, '_blank')}
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
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
        <DialogTitle>上传文献</DialogTitle>
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
                  label="标题"
                  value={metadata.title}
                  onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="作者（用逗号分隔）"
                  value={metadata.authors}
                  onChange={(e) => setMetadata({ ...metadata, authors: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="年份"
                  type="number"
                  value={metadata.year}
                  onChange={(e) => setMetadata({ ...metadata, year: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="关键词（用逗号分隔）"
                  value={metadata.keywords}
                  onChange={(e) => setMetadata({ ...metadata, keywords: e.target.value })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>取消</Button>
          <Button onClick={handleUpload} variant="contained" disabled={!uploadFile}>
            上传
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Documents;
