import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Button,
  Chip,
  Divider,
  Tabs,
  Tab,
  Alert,
  Paper,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { documentsAPI, summaryAPI, knowledgeAPI, annotationsAPI } from '../services/api';
import api from '../services/api';
import ThinkingMode from '../components/ThinkingMode';
import PDFViewer from '../components/PDFViewer';
import {
  MenuBook as ReadingIcon, CheckCircle as ReadIcon,
  Schedule as ToReadIcon, ContentCopy as CopyIcon,
  Download as DownloadIcon, Share as ShareIcon,
  BookmarkBorder as BookmarkIcon,
} from '@mui/icons-material';

const DocumentDetail = () => {
  const { t } = useTranslation();
  const { id } = useParams();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryStyle, setSummaryStyle] = useState('academic');
  const [activeTab, setActiveTab] = useState(0);
  const [textContent, setTextContent] = useState('');
  const [textLoading, setTextLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState(null);
  const [review, setReview] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [readingStatus, setReadingStatus] = useState(null);
  const [readingMenu, setReadingMenu] = useState(null);
  const [bibtex, setBibtex] = useState('');
  const [relatedPapers, setRelatedPapers] = useState([]);
  const [notify, setNotify] = useState({ open: false, msg: '', severity: 'success' });
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      fetchDocument();
      loadFileUrl();
    }
  }, [id]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      const doc = await documentsAPI.getById(id);
      setDocument(doc);
    } catch (err) {
      setError(t('errors.fetchFailed', { message: err.message }));
    } finally {
      setLoading(false);
    }
  };

  const loadFileUrl = () => {
    const token = localStorage.getItem('token');
    setFileUrl(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/documents/${id}/download?token=${token}`);
  };

  const fetchTextContent = useCallback(async () => {
    if (!id) return;
    try {
      setTextLoading(true);
      const data = await documentsAPI.getText(id);
      setTextContent(data.text || '');
    } catch (err) {
      setTextContent(t('errors.fetchFailed', { message: err.message }));
    } finally {
      setTextLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    if (activeTab === 2 && id && !textContent) {
      fetchTextContent();
    }
  }, [activeTab, id, textContent, fetchTextContent]);

  const handleGenerateSummary = async () => {
    if (!id) return;
    
    try {
      setSummaryLoading(true);
      const result = await summaryAPI.generate(id, 500, summaryStyle);
      setSummary(result.summary);
    } catch (err) {
      setError(t('errors.summaryFailed', { message: err.message }));
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleReview = async () => {
    try {
      setReviewLoading(true);
      const result = await knowledgeAPI.reviewDocument(id);
      setReview(result);
    } catch (err) {
      setError(t('errors.fetchFailed', { message: err.message }));
    } finally {
      setReviewLoading(false);
    }
  };

  const handleSetReadingStatus = async (status) => {
    try {
      await api.put(`/reading/${id}/status`, status, { headers: { 'Content-Type': 'text/plain' } });
      setReadingStatus(status);
      setReadingMenu(null);
      setNotify({ open: true, msg: `Marked as ${status}`, severity: 'success' });
    } catch (e) { console.error(e); }
  };

  const handleExportBibtex = async () => {
    try {
      const res = await api.get(`/citations/export/${id}`);
      setBibtex(res.data?.bibtex || '');
      navigator.clipboard.writeText(res.data?.bibtex || '');
      setNotify({ open: true, msg: 'BibTeX copied to clipboard', severity: 'success' });
    } catch (e) {
      setNotify({ open: true, msg: 'Failed to export', severity: 'error' });
    }
  };

  const handleLoadRelated = async () => {
    try {
      const res = await api.get(`/search/similar/${id}`, { params: { limit: 5 } });
      setRelatedPapers(res.data || []);
    } catch (e) { /* ignore */ }
  };

  const readingStatusChip = () => {
    const config = {
      to_read: { icon: <ToReadIcon />, label: 'To Read', color: 'warning' },
      reading: { icon: <ReadingIcon />, label: 'Reading', color: 'primary' },
      read: { icon: <ReadIcon />, label: 'Read', color: 'success' },
    };
    const c = config[readingStatus];
    return c ? <Chip icon={c.icon} label={c.label} color={c.color} size="small" variant="outlined" /> : null;
  };

  const handleHighlight = async (data) => {
    try {
      await annotationsAPI.createAnnotation(id, {
        page_number: data.page,
        text: data.text,
        position_x: data.position?.x,
        position_y: data.position?.y,
        width: data.position?.width,
        height: data.position?.height,
        highlight_color: '#FFEB3B',
      });
    } catch (err) {
      console.error('Failed to save highlight:', err);
    }
  };

  const handleNote = async (data) => {
    try {
      await annotationsAPI.createNote(id, {
        page_number: data.page,
        content: data.content || 'Untitled note',
        color: '#FFF9C4',
      });
    } catch (err) {
      console.error('Failed to save note:', err);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!document) {
    return (
      <Box>
        <Typography>{t('documentDetail.notFound')}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {document.title || t('documentDetail.title')}
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {document.authors && document.authors.map((author, index) => (
              <Chip key={index} label={author} size="small" />
            ))}
            {document.year && <Chip label={document.year} size="small" />}
            {document.keywords && document.keywords.map((keyword, index) => (
              <Chip key={index} label={keyword} size="small" color="primary" variant="outlined" />
            ))}
          </Box>

          <Box sx={{ display: 'flex', gap: 1, mb: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Button size="small" variant="outlined" startIcon={<ReadingIcon />}
              onClick={(e) => setReadingMenu(e.currentTarget)}>
              {readingStatus || 'Reading Status'}
            </Button>
            <Menu anchorEl={readingMenu} open={Boolean(readingMenu)} onClose={() => setReadingMenu(null)}>
              <MenuItem onClick={() => handleSetReadingStatus('to_read')}><ListItemIcon><ToReadIcon /></ListItemIcon><ListItemText>To Read</ListItemText></MenuItem>
              <MenuItem onClick={() => handleSetReadingStatus('reading')}><ListItemIcon><ReadingIcon /></ListItemIcon><ListItemText>Reading</ListItemText></MenuItem>
              <MenuItem onClick={() => handleSetReadingStatus('read')}><ListItemIcon><ReadIcon /></ListItemIcon><ListItemText>Read</ListItemText></MenuItem>
              <MenuItem onClick={() => handleSetReadingStatus('reference')}><ListItemIcon><BookmarkIcon /></ListItemIcon><ListItemText>Reference</ListItemText></MenuItem>
            </Menu>
            <Button size="small" variant="outlined" startIcon={<CopyIcon />} onClick={handleExportBibtex}>Copy BibTeX</Button>
            <Button size="small" variant="outlined" startIcon={<ShareIcon />} onClick={() => {
              navigator.clipboard.writeText(window.location.href);
              setNotify({ open: true, msg: 'Link copied', severity: 'success' });
            }}>Share Link</Button>
            <Box sx={{ flex: 1 }} />
            {readingStatusChip()}
          </Box>
          
          <Typography variant="body1" paragraph>
            {document.description || t('documentDetail.noDescription')}
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              onClick={handleGenerateSummary}
              disabled={summaryLoading}
            >
              {summaryLoading ? <CircularProgress size={24} /> : t('documentDetail.generateSummary')}
            </Button>
            
            <Button
              variant="outlined"
              onClick={handleReview}
              disabled={reviewLoading}
            >
              {reviewLoading ? <CircularProgress size={24} /> : t('documentDetail.reviewButton')}
            </Button>

            <Box>
              <Button
                variant={summaryStyle === 'academic' ? 'contained' : 'outlined'}
                onClick={() => setSummaryStyle('academic')}
                size="small"
                sx={{ mr: 1 }}
              >
                {t('documentDetail.summaryStyles.academic')}
              </Button>
              <Button
                variant={summaryStyle === 'simple' ? 'contained' : 'outlined'}
                onClick={() => setSummaryStyle('simple')}
                size="small"
                sx={{ mr: 1 }}
              >
                {t('documentDetail.summaryStyles.simple')}
              </Button>
              <Button
                variant={summaryStyle === 'detailed' ? 'contained' : 'outlined'}
                onClick={() => setSummaryStyle('detailed')}
                size="small"
              >
                {t('documentDetail.summaryStyles.detailed')}
              </Button>
            </Box>
          </Box>
          
          {summary && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                {t('documentDetail.summary')}
              </Typography>
              <Card variant="outlined" onMouseEnter={handleLoadRelated}>
                <CardContent>
                  <Typography variant="body2">{summary}</Typography>
                </CardContent>
              </Card>
            </Box>
          )}

          {review && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                {t('documentDetail.review')} - Score: {review.overall_score}/10
              </Typography>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2" paragraph>
                    <strong>Strengths:</strong> {review.strengths?.join('; ')}
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>Weaknesses:</strong> {review.weaknesses?.join('; ')}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Suggestions:</strong> {review.suggestions?.join('; ')}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          )}
        </CardContent>
      </Card>

      <Tabs 
        value={activeTab} 
        onChange={(e, newValue) => setActiveTab(newValue)}
        sx={{ mb: 2 }}
      >
        <Tab label={t('documentDetail.pdfViewer') || 'PDF Viewer'} />
        <Tab label={t('documentDetail.thinkingMode')} />
        <Tab label={t('documentDetail.content')} />
      </Tabs>

      {activeTab === 0 && fileUrl && (
        <PDFViewer
          documentId={id}
          fileUrl={fileUrl}
          onHighlight={handleHighlight}
          onNote={handleNote}
        />
      )}

      {activeTab === 1 && (
        <ThinkingMode documentId={id} documentTitle={document.title} />
      )}

      {activeTab === 2 && (
        <Paper>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('documentDetail.content')}
            </Typography>
            {textLoading ? (
              <Box display="flex" justifyContent="center" p={4}>
                <CircularProgress />
              </Box>
            ) : textContent ? (
              <Typography
                variant="body2"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  lineHeight: 1.8,
                  fontSize: '0.925rem',
                }}
              >
                {textContent}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                {t('common.noData')}
              </Typography>
            )}
          </CardContent>
        </Paper>
      )}

      {/* Related Papers */}
      {relatedPapers.length > 0 && (
        <Card variant="outlined" sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Related Papers</Typography>
            <Stack spacing={1}>
              {relatedPapers.map((r, i) => (
                <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                  onClick={() => navigate(`/documents/${r.document_id || r.id}`)}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{r.title || r.filename}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(r.authors || []).slice(0, 2).join(', ')} · Score: {((r.score || 0) * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Chip label="Similar" size="small" color="secondary" variant="outlined" />
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      <Snackbar open={notify.open} autoHideDuration={3000} onClose={() => setNotify({ ...notify, open: false })}>
        <Alert severity={notify.severity}>{notify.msg}</Alert>
      </Snackbar>
    </Box>
  );
};

export default DocumentDetail;
