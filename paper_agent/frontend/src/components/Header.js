import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useThemeMode } from '../contexts/ThemeContext';
import {
  AppBar, Toolbar, Typography, Box, Select, MenuItem, FormControl,
  IconButton, Menu, ListItemText, ListItemIcon, Button, Divider,
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import SecurityIcon from '@mui/icons-material/Security';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DescriptionIcon from '@mui/icons-material/Description';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SearchIcon from '@mui/icons-material/Search';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import FolderSpecialIcon from '@mui/icons-material/FolderSpecial';
import ScienceIcon from '@mui/icons-material/Science';
import BookIcon from '@mui/icons-material/Book';
import HistoryEduIcon from '@mui/icons-material/HistoryEdu';
import FormatQuoteIcon from '@mui/icons-material/FormatQuote';
import LinkIcon from '@mui/icons-material/Link';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import EventIcon from '@mui/icons-material/Event';
import EditNoteIcon from '@mui/icons-material/EditNote';
import ChatIcon from '@mui/icons-material/Chat';
import HubIcon from '@mui/icons-material/Hub';
import ForumIcon from '@mui/icons-material/Forum';
import SettingsIcon from '@mui/icons-material/Settings';

const Header = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const [selectedModel, setSelectedModel] = useState(localStorage.getItem('selectedModel') || 'openai');
  const [moreMenu, setMoreMenu] = useState(null);
  const { mode, toggleTheme } = useThemeMode();

  const handleModelChange = (e) => {
    const model = e.target.value;
    setSelectedModel(model);
    localStorage.setItem('selectedModel', model);
  };

  const isActive = (path) => location.pathname === path;

  const NavButton = ({ path, icon, label }) => (
    <Button
      color="inherit"
      size="small"
      startIcon={icon}
      onClick={() => navigate(path)}
      sx={{
        mx: 0.5,
        textTransform: 'none',
        borderRadius: 2,
        bgcolor: isActive(path) ? 'rgba(255,255,255,0.15)' : 'transparent',
        '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' },
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
          sx={{ flexGrow: 0, mr: 4, fontWeight: 'bold', cursor: 'pointer', whiteSpace: 'nowrap' }}
          onClick={() => navigate('/')}
        >
          📚 Paper Agent
        </Typography>

        <Box sx={{ display: 'flex', flexGrow: 1, overflowX: 'auto', py: 0.5, gap: 0.5 }}>
          <NavButton path="/" icon={<DashboardIcon />} label={t('nav.dashboard') || 'Home'} />
          <NavButton path="/documents" icon={<DescriptionIcon />} label={t('nav.documents') || 'Docs'} />
          <NavButton path="/reading" icon={<MenuBookIcon />} label="Reading" />
          <NavButton path="/flashcards" icon={<MenuBookIcon />} label="Review" />
          <NavButton path="/ask" icon={<SmartToyIcon />} label="Ask AI" />
          <NavButton path="/search" icon={<SearchIcon />} label={t('nav.search') || 'Search'} />
          <NavButton path="/knowledge" icon={<AccountTreeIcon />} label="KG" />
          <NavButton path="/literature-tree" icon={<FolderSpecialIcon />} label="Tree" />
          <NavButton path="/discovery" icon={<ScienceIcon />} label="Discovery" />
          <NavButton path="/notebooks" icon={<BookIcon />} label="Notebook" />
          <NavButton path="/drafting" icon={<HistoryEduIcon />} label="Drafting" />
          <NavButton path="/citations" icon={<FormatQuoteIcon />} label="Citations" />
          <NavButton path="/zotero" icon={<LinkIcon />} label="Zotero" />

          <IconButton color="inherit" size="small" onClick={(e) => setMoreMenu(e.currentTarget)} sx={{ ml: 0.5 }}>
            <MoreVertIcon />
          </IconButton>
          <Menu anchorEl={moreMenu} open={Boolean(moreMenu)} onClose={() => setMoreMenu(null)}>
            <MenuItem onClick={() => { navigate('/conferences'); setMoreMenu(null); }}>
              <ListItemIcon><EventIcon fontSize="small" /></ListItemIcon><ListItemText>Conferences</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { navigate('/journal'); setMoreMenu(null); }}>
              <ListItemIcon><EditNoteIcon fontSize="small" /></ListItemIcon><ListItemText>Journal</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { navigate('/research-chat'); setMoreMenu(null); }}>
              <ListItemIcon><ChatIcon fontSize="small" /></ListItemIcon><ListItemText>Research Chat</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { navigate('/graphrag'); setMoreMenu(null); }}>
              <ListItemIcon><HubIcon fontSize="small" /></ListItemIcon><ListItemText>GraphRAG</ListItemText>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { navigate('/insights'); setMoreMenu(null); }}>
              <ListItemIcon><ForumIcon fontSize="small" /></ListItemIcon><ListItemText>Scholar Insights</ListItemText>
            </MenuItem>
          </Menu>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 100 }}>
            <Select
              value={selectedModel}
              onChange={handleModelChange}
              sx={{
                color: 'inherit', fontSize: '0.75rem',
                '.MuiOutlinedInput-notchedOutline': { border: 'none' },
                bgcolor: 'rgba(255,255,255,0.1)', height: 32,
              }}
            >
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="qwen">Qwen</MenuItem>
              <MenuItem value="deepseek">DeepSeek</MenuItem>
              <MenuItem value="ollama">Ollama</MenuItem>
            </Select>
          </FormControl>
          <IconButton color="inherit" onClick={toggleTheme} size="small" title={mode === 'dark' ? 'Light mode' : 'Dark mode'}>
            {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
          <IconButton color="inherit" onClick={() => navigate('/settings')} size="small">
            <SettingsIcon />
          </IconButton>
          <IconButton color="inherit" onClick={() => navigate('/admin')} size="small">
            <SecurityIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
