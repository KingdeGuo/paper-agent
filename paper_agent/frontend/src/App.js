import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import { I18nextProvider } from 'react-i18next';
import i18n from './i18n/i18n';

import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Search from './pages/Search';
import DocumentDetail from './pages/DocumentDetail';
import Knowledge from './pages/Knowledge';
import Comparison from './pages/Comparison';
import Notebooks from './pages/Notebooks';
import Discovery from './pages/Discovery';
import Zotero from './pages/Zotero';
import Drafting from './pages/Drafting';
import Citations from './pages/Citations';
import ReadingList from './pages/ReadingList';
import AskLibrary from './pages/AskLibrary';
import ResearchDigest from './pages/ResearchDigest';
import WritingIntegration from './pages/WritingIntegration';
import Settings from './pages/Settings';
import Admin from './pages/Admin';
import Login from './pages/Login';
import { AuthProvider } from './contexts/AuthContext';
import { SnackbarProvider } from './contexts/SnackbarContext';
import ProtectedRoute from './components/ProtectedRoute';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb', // More modern blue
    },
    secondary: {
      main: '#7c3aed', // Purple for AI features
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <I18nextProvider i18n={i18n}>
      <AuthProvider>
        <SnackbarProvider>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <Header />
              <Box sx={{ p: 3, flexGrow: 1 }}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                  <Route path="/documents" element={<ProtectedRoute><Documents /></ProtectedRoute>} />
                  <Route path="/documents/:id" element={<ProtectedRoute><DocumentDetail /></ProtectedRoute>} />
                  <Route path="/search" element={<ProtectedRoute><Search /></ProtectedRoute>} />
                  <Route path="/knowledge" element={<ProtectedRoute><Knowledge /></ProtectedRoute>} />
                  <Route path="/comparison" element={<ProtectedRoute><Comparison /></ProtectedRoute>} />
                  <Route path="/notebooks" element={<ProtectedRoute><Notebooks /></ProtectedRoute>} />
                  <Route path="/discovery" element={<ProtectedRoute><Discovery /></ProtectedRoute>} />
                  <Route path="/zotero" element={<ProtectedRoute><Zotero /></ProtectedRoute>} />
                  <Route path="/drafting" element={<ProtectedRoute><Drafting /></ProtectedRoute>} />
                  <Route path="/citations" element={<ProtectedRoute><Citations /></ProtectedRoute>} />
                  <Route path="/reading" element={<ProtectedRoute><ReadingList /></ProtectedRoute>} />
                  <Route path="/ask" element={<ProtectedRoute><AskLibrary /></ProtectedRoute>} />
                  <Route path="/digest" element={<ProtectedRoute><ResearchDigest /></ProtectedRoute>} />
                  <Route path="/writing" element={<ProtectedRoute><WritingIntegration /></ProtectedRoute>} />
                  <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
                  <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />
                </Routes>
              </Box>
            </Box>
          </Router>
        </ThemeProvider>
        </SnackbarProvider>
      </AuthProvider>
    </I18nextProvider>
  );
}

export default App;
