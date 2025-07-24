import React, { useState, useEffect } from 'react';
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
  Alert
} from '@mui/material';
import { useParams } from 'react-router-dom';
import { documentsAPI, summaryAPI } from '../services/api';
import ThinkingMode from '../components/ThinkingMode';

const DocumentDetail = () => {
  const { id } = useParams();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryStyle, setSummaryStyle] = useState('academic');
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    fetchDocument();
  }, [id]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      const doc = await documentsAPI.getById(id);
      setDocument(doc);
    } catch (err) {
      setError('获取文档详情失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!id) return;
    
    try {
      setSummaryLoading(true);
      const result = await summaryAPI.generate(id, 500, summaryStyle);
      setSummary(result.summary);
    } catch (err) {
      setError('生成摘要失败: ' + err.message);
    } finally {
      setSummaryLoading(false);
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
        <Typography>未找到文档</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {document.title || '文献详情'}
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
            {document.description || '暂无描述'}
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button
              variant="contained"
              onClick={handleGenerateSummary}
              disabled={summaryLoading}
            >
              {summaryLoading ? <CircularProgress size={24} /> : '生成摘要'}
            </Button>
            
            <Box>
              <Button
                variant={summaryStyle === 'academic' ? 'contained' : 'outlined'}
                onClick={() => setSummaryStyle('academic')}
                size="small"
                sx={{ mr: 1 }}
              >
                学术版
              </Button>
              <Button
                variant={summaryStyle === 'simple' ? 'contained' : 'outlined'}
                onClick={() => setSummaryStyle('simple')}
                size="small"
                sx={{ mr: 1 }}
              >
                简洁版
              </Button>
              <Button
                variant={summaryStyle === 'detailed' ? 'contained' : 'outlined'}
                onClick={() => setSummaryStyle('detailed')}
                size="small"
              >
                详细版
              </Button>
            </Box>
          </Box>
          
          {summary && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                文档摘要
              </Typography>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2">{summary}</Typography>
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
        <Tab label="文档内容" />
        <Tab label="思考模式" />
      </Tabs>
      
      {activeTab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              文档内容
            </Typography>
            <Typography variant="body2">
              文档内容显示功能正在开发中...
            </Typography>
          </CardContent>
        </Card>
      )}
      
      {activeTab === 1 && (
        <ThinkingMode documentId={id} documentTitle={document.title} />
      )}
    </Box>
  );
};

export default DocumentDetail;