import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useThemeMode } from '../contexts/ThemeContext';
import { AppBar, Toolbar, Typography, Box, Select, MenuItem, FormControl, IconButton, Menu, ListItemText, Button } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import SecurityIcon from '@mui/icons-material/Security';

const Header = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [selectedModel, setSelectedModel] = useState(localStorage.getItem('selectedModel') || 'openai');
  const [moreMenu, setMoreMenu] = useState(null);
  const [menuAnchor, setMenuAnchor] = useState({});
  const { mode, toggleTheme } = useThemeMode();

  const handleModelChange = (e) => {
    const model = e.target.value;
    setSelectedModel(model);
    localStorage.setItem('selectedModel', model);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <AppBar position="static" elevation={0} sx={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
      <Toolbar variant="dense">
        <Typography variant="h6" sx={{ flexGrow: 0, mr: 3, fontWeight: 'bold', cursor: 'pointer', whiteSpace: 'nowrap' }}
          onClick={() => navigate('/')}>
          📚 Paper Agent
        </Typography>

        <Box sx={{ display: 'flex', flexGrow: 1, gap: 0.5, overflow: 'hidden' }}>
          <Button color="inherit" size="small" onClick={() => navigate('/')}
            sx={{ textTransform: 'none', borderRadius: 2, fontWeight: isActive('/') ? 'bold' : 'normal', bgcolor: isActive('/') ? 'rgba(255,255,255,0.15)' : 'transparent' }}>
            🏠 Home
          </Button>
          <Button color="inherit" size="small" onClick={() => navigate('/overview')}
            sx={{ textTransform: 'none', borderRadius: 2, fontWeight: isActive('/overview') ? 'bold' : 'normal', bgcolor: isActive('/overview') ? 'rgba(255,255,255,0.15)' : 'transparent' }}>
            📊 Overview
          </Button>
          {MENUS.map((menu, mi) => (
            <Box key={mi}>
              <Button color="inherit" size="small"
                onClick={(e) => setMenuAnchor({ ...menuAnchor, [mi]: e.currentTarget })}
                sx={{ textTransform: 'none', borderRadius: 2, fontSize: '0.8rem' }}>
                {menu.label} ▾
              </Button>
              <Menu anchorEl={menuAnchor[mi]} open={Boolean(menuAnchor[mi])} onClose={() => setMenuAnchor({ ...menuAnchor, [mi]: null })}
                PaperProps={{ sx: { mt: 0.5 } }}>
                {menu.items.map((item, ii) => (
                  <MenuItem key={ii} onClick={() => { navigate(item.path); setMenuAnchor({}); }}
                    selected={isActive(item.path)} dense>
                    <ListItemText primaryTypographyProps={{ variant: 'body2' }}>
                      {item.icon} {item.label}
                    </ListItemText>
                  </MenuItem>
                ))}
              </Menu>
            </Box>
          ))}
          <Button color="inherit" size="small" onClick={() => navigate('/settings')}
            sx={{ textTransform: 'none', borderRadius: 2, ml: 'auto' }}>
            ⚙️
          </Button>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
          <FormControl size="small" sx={{ minWidth: 90 }}>
            <Select value={selectedModel} onChange={handleModelChange}
              sx={{ color: 'inherit', fontSize: '0.75rem', '.MuiOutlinedInput-notchedOutline': { border: 'none' }, bgcolor: 'rgba(255,255,255,0.1)', height: 28 }}>
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="qwen">Qwen</MenuItem>
              <MenuItem value="deepseek">DeepSeek</MenuItem>
              <MenuItem value="ollama">Ollama</MenuItem>
            </Select>
          </FormControl>
          <IconButton color="inherit" onClick={toggleTheme} size="small">
            {mode === 'dark' ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}
          </IconButton>
          <IconButton color="inherit" onClick={() => navigate('/admin')} size="small">
            <SecurityIcon fontSize="small" />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;

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
          <NavButton path="/reading" icon={<MenuBookIcon />} label="Reading" />
          <NavButton path="/analytics" icon={<SummaryIcon />} label="Analytics" />
          <NavButton path="/digest" icon={<SummaryIcon />} label="Digest" />
          <NavButton path="/flashcards" icon={<MenuBookIcon />} label="Review" />
          <NavButton path="/ask" icon={<SmartToyIcon />} label="Ask AI" />
          <NavButton path="/search" icon={<SearchIcon />} label={t('nav.search') || 'Search'} />
          <NavButton path="/knowledge" icon={<AccountTreeIcon />} label="KG" />
          <NavButton path="/literature-tree" icon={<FolderSpecialIcon />} label="Tree" />
          <NavButton path="/discovery" icon={<ScienceIcon />} label="Discovery" />
          <NavButton path="/notebooks" icon={<BookIcon />} label="Notebook" />
          <NavButton path="/drafting" icon={<HistoryEduIcon />} label="Drafting" />
          <NavButton path="/writing" icon={<IntegrationIcon />} label="Writing" />
          <NavButton path="/citations" icon={<FormatQuoteIcon />} label="Citations" />
          <NavButton path="/zotero" icon={<LinkIcon />} label="Zotero" />
          <IconButton color="inherit" size="small" onClick={(e) => setMoreMenu(e.currentTarget)} sx={{ ml: 0.5 }}>
            <MoreVertIcon />
          </IconButton>
          <Menu anchorEl={moreMenu} open={Boolean(moreMenu)} onClose={() => setMoreMenu(null)}>
            <MenuItem onClick={() => { navigate('/conferences'); setMoreMenu(null); }}><ListItemIcon><EventIcon fontSize="small" /></ListItemIcon><ListItemText>Conferences</ListItemText></MenuItem>
            <MenuItem onClick={() => { navigate('/journal'); setMoreMenu(null); }}><ListItemIcon><EditNoteIcon fontSize="small" /></ListItemIcon><ListItemText>Journal</ListItemText></MenuItem>
            <MenuItem onClick={() => { navigate('/research-chat'); setMoreMenu(null); }}><ListItemIcon><ChatIcon fontSize="small" /></ListItemIcon><ListItemText>Research Chat</ListItemText></MenuItem>
            <MenuItem onClick={() => { navigate('/graphrag'); setMoreMenu(null); }}><ListItemIcon><HubIcon fontSize="small" /></ListItemIcon><ListItemText>GraphRAG</ListItemText></MenuItem>
            <MenuItem onClick={() => { navigate('/agents'); setMoreMenu(null); }}><ListItemIcon><PsychologyAltIcon fontSize="small" /></ListItemIcon><ListItemText>AI Agents</ListItemText></MenuItem>
            <Divider />
            <MenuItem onClick={() => { navigate('/insights'); setMoreMenu(null); }}><ListItemIcon><ForumIcon fontSize="small" /></ListItemIcon><ListItemText>Scholar Insights</ListItemText></MenuItem>
          </Menu>
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
