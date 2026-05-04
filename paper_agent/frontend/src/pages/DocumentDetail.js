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
} from '@mui/material';
import { useParams } from 'react-router-dom';
import { documentsAPI, summaryAPI, knowledgeAPI } from '../services/api';
import ThinkingMode from '../components/ThinkingMode';
import PDFViewer from '../components/PDFViewer';

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
      setError(`Review failed: ${err.message}`);
    } finally {
      setReviewLoading(false);
    }
  };

  const handleHighlight = (data) => {
    console.log('Highlight created:', data);
    // TODO: Save highlight via API
  };

  const handleNote = (data) => {
    console.log('Note created:', data);
    // TODO: Save note via API
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
              <Card variant="outlined">
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
        <Tab label="PDF Viewer" />
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
    </Box>
  );
};

export default DocumentDetail;
