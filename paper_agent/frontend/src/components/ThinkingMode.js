import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Chip,
  Divider,
  Button,
  TextField
} from '@mui/material';
import { summaryAPI } from '../services/api';
import ThinkingProgress from './ThinkingProgress';

const ThinkingMode = ({ documentId, documentTitle }) => {
  const { t } = useTranslation();
  const [rawText, setRawText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [question, setQuestion] = useState('');
  const [isAnswering, setIsAnswering] = useState(false);

  const parseReasoning = (text) => {
    const thoughtMatch = text.match(/<thought>([\s\S]*?)<\/thought>/);
    let thought = '';
    let answer = text;

    if (thoughtMatch) {
      thought = thoughtMatch[1];
      answer = text.replace(/<thought>[\s\S]*?<\/thought>/, '').trim();
    } else if (text.includes('<thought>')) {
      const parts = text.split('<thought>');
      thought = parts[1];
      answer = parts[0];
    }

    return { thought, answer };
  };

  const handleGenerateThinkingSummary = async () => {
    if (!documentId) return;
    
    setIsThinking(true);
    setRawText('');
    
    try {
      for await (const chunk of summaryAPI.generateStreaming(documentId, 1000, 'detailed')) {
        setRawText(prev => prev + chunk);
      }
    } catch (error) {
      console.error('Error generating thinking summary:', error);
      setRawText('Error: ' + error.message);
    } finally {
      setIsThinking(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!documentId || !question.trim()) return;
    
    setIsAnswering(true);
    setRawText('');
    
    try {
      for await (const chunk of summaryAPI.answerQuestionStreaming(documentId, question)) {
        setRawText(prev => prev + chunk);
      }
    } catch (error) {
      console.error('Error answering question:', error);
      setRawText('Error: ' + error.message);
    } finally {
      setIsAnswering(false);
    }
  };

  const { thought, answer } = parseReasoning(rawText);

  return (
    <Box>
      <Card sx={{ mb: 2, borderRadius: 2, boxShadow: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                {t('documentDetail.thinkingMode')}
              </Typography>
              <Chip label="PRO" color="primary" size="small" sx={{ ml: 1, height: 20, fontSize: '0.65rem' }} />
            </Box>
            <Button
              variant="outlined"
              size="small"
              onClick={handleGenerateThinkingSummary}
              disabled={isThinking || isAnswering || !documentId}
            >
              {isThinking ? <CircularProgress size={16} sx={{ mr: 1 }} /> : null}
              {t('documentDetail.regenerateSummary')}
            </Button>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('documentDetail.thinkingModeDescription')}
          </Typography>
          
          {(isThinking || thought) && (
            <Box sx={{ mb: 3 }}>
              <ThinkingProgress thinkingText={thought} />
            </Box>
          )}
          
          {answer && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'medium', display: 'flex', alignItems: 'center' }}>
                <Divider sx={{ flexGrow: 1, mr: 2 }} />
                {t('documentDetail.analysisResult')}
                <Divider sx={{ flexGrow: 1, ml: 2 }} />
              </Typography>
              <Paper variant="outlined" sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 2 }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                  {answer}
                </Typography>
              </Paper>
            </Box>
          )}
        </CardContent>
      </Card>
      
      <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'medium' }}>
            {t('documentDetail.interactiveQA')}
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder={t('documentDetail.askQuestion')}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isThinking || isAnswering}
            sx={{ mb: 2 }}
          />
          
          <Button
            variant="contained"
            fullWidth
            onClick={handleAskQuestion}
            disabled={isThinking || isAnswering || !question.trim() || !documentId}
            sx={{ py: 1.5, fontWeight: 'bold' }}
          >
            {isAnswering ? (
              <>
                <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
                {t('documentDetail.thinking')}
              </>
            ) : (
              t('documentDetail.submitQuestion')
            )}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ThinkingMode;