import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import DescriptionIcon from '@mui/icons-material/Description';
import SearchIcon from '@mui/icons-material/Search';
import DashboardIcon from '@mui/icons-material/Dashboard';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [selectedModel, setSelectedModel] = useState('openai');
  
  const getModelDisplayName = (model) => {
    const modelNames = {
      'openai': 'OpenAI',
      'qwen': 'Qwen (通义千问)',
      'deepseek': 'DeepSeek',
      'ollama': 'Ollama',
      'anthropic': 'Anthropic',
      'huggingface': 'HuggingFace'
    };
    return modelNames[model] || model;
  };
  
  const handleModelChange = (e) => {
    const model = e.target.value;
    setSelectedModel(model);
    // 在实际应用中，这里会调用API来更新默认模型
    localStorage.setItem('selectedModel', model);
  };
  
  const modelOptions = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'qwen', label: 'Qwen (通义千问)' },
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'ollama', label: 'Ollama' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'huggingface', label: 'HuggingFace' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          智能文献管理系统
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            color="inherit"
            startIcon={<DashboardIcon />}
            onClick={() => navigate('/')}
            variant={isActive('/') ? 'outlined' : 'text'}
          >
            仪表板
          </Button>
          <Button
            color="inherit"
            startIcon={<DescriptionIcon />}
            onClick={() => navigate('/documents')}
            variant={isActive('/documents') ? 'outlined' : 'text'}
          >
            文献管理
          </Button>
          <Button
            color="inherit"
            startIcon={<SearchIcon />}
            onClick={() => navigate('/search')}
            variant={isActive('/search') ? 'outlined' : 'text'}
          >
            智能搜索
          </Button>
          
          {/* 模型选择器 */}
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
            <Typography variant="body2" sx={{ mr: 1, color: 'text.secondary' }}>
              模型:
            </Typography>
            <select
              value={selectedModel}
              onChange={handleModelChange}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {modelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
