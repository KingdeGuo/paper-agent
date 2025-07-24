import React, { useState, useEffect } from 'react';
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
  const [thinkingProcess, setThinkingProcess] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isAnswering, setIsAnswering] = useState(false);

  const handleGenerateThinkingSummary = async () => {
    if (!documentId) return;
    
    setIsThinking(true);
    setThinkingProcess('');
    
    try {
      for await (const chunk of summaryAPI.generateStreaming(documentId, 500, 'detailed')) {
        setThinkingProcess(prev => prev + chunk);
      }
    } catch (error) {
      console.error('Error generating thinking summary:', error);
      setThinkingProcess('Error generating thinking summary: ' + error.message);
    } finally {
      setIsThinking(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!documentId || !question.trim()) return;
    
    setIsAnswering(true);
    setAnswer('');
    
    try {
      for await (const chunk of summaryAPI.answerQuestionStreaming(documentId, question)) {
        setAnswer(prev => prev + chunk);
      }
    } catch (error) {
      console.error('Error answering question:', error);
      setAnswer('Error answering question: ' + error.message);
    } finally {
      setIsAnswering(false);
    }
  };

  return (
    <Box>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">思考模式</Typography>
            <Chip label="Beta" color="secondary" size="small" />
          </Box>
          
          <Typography variant="body2" sx={{ mb: 2 }}>
            启用思考模式可以查看AI模型的推理过程和分析思路，帮助您更好地理解模型是如何处理和分析文档内容的。
          </Typography>
          
          <Button
            variant="contained"
            onClick={handleGenerateThinkingSummary}
            disabled={isThinking || !documentId}
            sx={{ mb: 2 }}
          >
            {isThinking ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                思考中...
              </>
            ) : (
              '生成思考过程摘要'
            )}
          </Button>
          
          {isThinking && (
            <ThinkingProgress thinkingText={thinkingProcess} />
          )}
          
          {thinkingProcess && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                思考过程:
              </Typography>
              <Card variant="outlined">
                <CardContent>
                  <pre style={{ 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word',
                    fontSize: '0.875rem',
                    lineHeight: 1.6
                  }}>
                    {thinkingProcess}
                  </pre>
                </CardContent>
              </Card>
            </Box>
          )}
        </CardContent>
      </Card>
      
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            交互式问答
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="向AI提问关于文档内容的问题..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <Button
            variant="contained"
            onClick={handleAskQuestion}
            disabled={isAnswering || !question.trim() || !documentId}
          >
            {isAnswering ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                思考中...
              </>
            ) : (
              '提问'
            )}
          </Button>
          
          {isAnswering && (
            <ThinkingProgress thinkingText={answer} />
          )}
          
          {answer && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                AI 回答:
              </Typography>
              <Card variant="outlined">
                <CardContent>
                  <pre style={{ 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word',
                    fontSize: '0.875rem',
                    lineHeight: 1.6
                  }}>
                    {answer}
                  </pre>
                </CardContent>
              </Card>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ThinkingMode;