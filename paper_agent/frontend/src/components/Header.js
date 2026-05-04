import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AppBar, Toolbar, Typography, Button, Box, Select, MenuItem, FormControl, IconButton, Tooltip } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import DescriptionIcon from '@mui/icons-material/Description';
import SearchIcon from '@mui/icons-material/Search';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import BookIcon from '@mui/icons-material/Book';
import ScienceIcon from '@mui/icons-material/Science';
import LinkIcon from '@mui/icons-material/Link';
import HistoryEduIcon from '@mui/icons-material/HistoryEdu';
import TranslateIcon from '@mui/icons-material/Translate';

const Header = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [selectedModel, setSelectedModel] = useState(localStorage.getItem('selectedModel') || 'openai');

  const handleModelChange = (e) => {
    const model = e.target.value;
    setSelectedModel(model);
    localStorage.setItem('selectedModel', model);
  };

  const isActive = (path) => location.pathname === path;

  const NavButton = ({ path, icon, label }) => (
    <Button
      color="inherit"
      startIcon={icon}
      onClick={() => navigate(path)}
      sx={{ 
        mx: 0.5,
        textTransform: 'none',
        borderRadius: 2,
        bgcolor: isActive(path) ? 'rgba(255,255,255,0.15)' : 'transparent',
        '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' }
      }}
    >
      {label}
    </Button>
  );

  return (
    <AppBar position="static" elevation={0} sx={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
      <Toolbar variant="dense">
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ flexGrow: 0, mr: 4, fontWeight: 'bold', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          Paper Agent
        </Typography>
        
        <Box sx={{ display: 'flex', flexGrow: 1, overflowX: 'auto', py: 0.5 }}>
          <NavButton path="/" icon={<DashboardIcon />} label={t('nav.dashboard') || 'Home'} />
          <NavButton path="/documents" icon={<DescriptionIcon />} label={t('nav.documents') || 'Docs'} />
          <NavButton path="/search" icon={<SearchIcon />} label={t('nav.search') || 'Search'} />
          <NavButton path="/knowledge" icon={<AccountTreeIcon />} label="KG" />
          <NavButton path="/discovery" icon={<ScienceIcon />} label="Discovery" />
          <NavButton path="/notebooks" icon={<BookIcon />} label="Notebook" />
          <NavButton path="/drafting" icon={<HistoryEduIcon />} label="Drafting" />
          <NavButton path="/zotero" icon={<LinkIcon />} label="Zotero" />
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 100 }}>
            <Select
              value={selectedModel}
              onChange={handleModelChange}
              sx={{ 
                color: 'inherit',
                fontSize: '0.75rem',
                '.MuiOutlinedInput-notchedOutline': { border: 'none' },
                bgcolor: 'rgba(255,255,255,0.1)',
                height: 32,
              }}
            >
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="qwen">Qwen</MenuItem>
              <MenuItem value="deepseek">DeepSeek</MenuItem>
              <MenuItem value="ollama">Ollama</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
