import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Divider,
  Paper,
  Stack,
  Alert,
} from '@mui/material';
import { 
  CompareArrows as CompareIcon,
  AutoAwesome as AIIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import ThinkingProgress from '../components/ThinkingProgress';

const Comparison = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const selectedIds = location.state?.selectedIds || [];

  useEffect(() => {
    if (selectedIds.length >= 2) {
      handleCompare();
    } else {
      setError("Please select at least 2 papers from the Documents page to compare.");
    }
  }, [selectedIds]);

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/review/compare', {
        document_ids: selectedIds
      });
      setResult(response.data);
    } catch (err) {
      setError("Failed to generate comparative analysis. " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate(-1)} sx={{ mr: 2 }}>
          {t('common.back')}
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          {t('nav.comparison') || 'Comparative Analysis'}
        </Typography>
      </Box>

      {error && <Alert severity="warning" sx={{ mb: 3 }}>{error}</Alert>}

      {loading && (
        <Box sx={{ textAlign: 'center', py: 10 }}>
          <CircularProgress size={60} thickness={2} sx={{ mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            AI is synthesizing research papers...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This may take 30-60 seconds for deep analysis.
          </Typography>
        </Box>
      )}

      {result && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card sx={{ borderRadius: 2, boxShadow: 3, mb: 3, bgcolor: 'primary.dark', color: 'white' }}>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <CompareIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                      Multivariate Research Synthesis
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Comparing: {result.titles?.join(' vs ')}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {result.thought && (
            <Grid item xs={12}>
              <ThinkingProgress thinkingText={result.thought} />
            </Grid>
          )}

          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 4, borderRadius: 2, minHeight: 500 }}>
              <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
                <AIIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Synthesis Report</Typography>
              </Box>
              <Divider sx={{ mb: 3 }} />
              <Box className="markdown-body">
                <ReactMarkdown>{result.comparison}</ReactMarkdown>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Comparison;
