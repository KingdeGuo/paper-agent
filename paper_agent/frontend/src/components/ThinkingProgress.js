import React, { useState, useEffect } from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Card,
  CardContent,
  Chip
} from '@mui/material';

const ThinkingProgress = ({ thinkingText }) => {
  const [progress, setProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('初始化');
  const [details, setDetails] = useState('');

  // 定义思考阶段
  const thinkingPhases = [
    '初始化',
    '问题分析',
    '信息检索',
    '内容理解',
    '答案构建',
    '完成'
  ];

  useEffect(() => {
    if (!thinkingText) {
      setProgress(0);
      setCurrentPhase('初始化');
      setDetails('');
      return;
    }

    // 模拟进度更新
    const updateProgress = () => {
      setProgress(prev => {
        const newProgress = Math.min(prev + 1, 100);
        
        // 根据进度更新阶段
        const phaseIndex = Math.floor((newProgress / 100) * (thinkingPhases.length - 1));
        setCurrentPhase(thinkingPhases[phaseIndex]);
        
        return newProgress;
      });
    };

    const interval = setInterval(updateProgress, 100);
    return () => clearInterval(interval);
  }, [thinkingText]);

  useEffect(() => {
    if (!thinkingText) return;
    
    // 提取思考过程中的关键信息
    const lines = thinkingText.split('\n');
    if (lines.length > 0) {
      const lastLine = lines[lines.length - 1];
      if (lastLine.trim()) {
        setDetails(lastLine.trim());
      }
    }
  }, [thinkingText]);

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1">
            AI 思考过程
          </Typography>
          <Chip 
            label={currentPhase} 
            color={currentPhase === '完成' ? 'success' : 'primary'} 
            size="small" 
          />
        </Box>
        
        <Box sx={{ mb: 1 }}>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ 
              height: 10, 
              borderRadius: 5,
              backgroundColor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                backgroundColor: currentPhase === '完成' ? 'success.main' : 'primary.main'
              }
            }} 
          />
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            进度: {progress}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {details && `最新: ${details.substring(0, 30)}${details.length > 30 ? '...' : ''}`}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ThinkingProgress;