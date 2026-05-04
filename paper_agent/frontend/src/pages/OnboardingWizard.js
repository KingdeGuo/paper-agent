import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Button, Stepper, Step, StepLabel, Card, CardContent, CircularProgress, LinearProgress, Chip, Stack, Grid, Alert } from '@mui/material';
import { AutoAwesome as AIIcon, Upload as UploadIcon, Folder as FolderIcon, TrackChanges as GoalIcon, Link as LinkIcon, Explore as ExploreIcon, CheckCircle as DoneIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const STEPS = [
  { label: 'Welcome', icon: <AIIcon />, color: '#2563eb' },
  { label: 'Your First Paper', icon: <UploadIcon />, color: '#16a34a' },
  { label: 'AI Setup', icon: <AIIcon />, color: '#7c3aed' },
  { label: 'Organize', icon: <FolderIcon />, color: '#ea580c' },
  { label: 'Reading Goals', icon: <GoalIcon />, color: '#0891b2' },
  { label: 'Connect Zotero', icon: <LinkIcon />, color: '#d946ef' },
  { label: 'Explore', icon: <ExploreIcon />, color: '#f59e0b' },
];

const OnboardingWizard = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [onboarding, setOnboarding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => { fetchStatus(); }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try { const res = await api.get('/onboarding/status'); setOnboarding(res.data);
      const firstIncomplete = (res.data?.steps || []).findIndex(s => !s.completed);
      if (firstIncomplete >= 0) setActiveStep(firstIncomplete);
    } catch (e) { }
    finally { setLoading(false); }
  };

  const handleLoadDemo = async () => {
    setDemoLoading(true);
    try {
      await api.get('/onboarding/demo-data');
      await api.post('/onboarding/complete/upload_first_paper');
      fetchStatus();
    } catch (e) { }
    finally { setDemoLoading(false); }
  };

  const handleSkip = async (stepId) => {
    try { await api.post(`/onboarding/complete/${stepId}`); fetchStatus(); } catch (e) { }
  };

  const handleGo = (path) => {
    navigate(path);
  };

  const renderStepContent = (step) => {
    const stepData = STEPS[step];
    const id = onboarding?.steps?.[step]?.id;

    switch (step) {
      case 0:
        return (
          <Box textAlign="center" py={4}>
            <AIIcon sx={{ fontSize: 80, mb: 2, color: 'primary.main' }} />
            <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>Welcome to Paper Agent!</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
              Your AI Research Companion. Manage papers, generate insights, collaborate with your team, and accelerate your research.
            </Typography>
            <Button variant="contained" size="large" onClick={() => handleSkip(id)}>Get Started →</Button>
          </Box>
        );

      case 1:
        return (
          <Box textAlign="center" py={4}>
            <UploadIcon sx={{ fontSize: 60, mb: 2, color: 'success.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>Add Your First Paper</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Upload a PDF, search arXiv, paste a DOI, or load demo papers to explore.
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button variant="contained" onClick={() => handleGo('/documents')}>Upload PDF</Button>
              <Button variant="outlined" onClick={() => handleGo('/search')}>Search arXiv</Button>
              <Button variant="text" onClick={handleLoadDemo} disabled={demoLoading}>
                {demoLoading ? <CircularProgress size={20} /> : 'Load Demo Papers'}
              </Button>
            </Stack>
          </Box>
        );

      case 2:
        return (
          <Box textAlign="center" py={4}>
            <AIIcon sx={{ fontSize: 60, mb: 2, color: 'secondary.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>Configure AI</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Set up an AI provider for summaries, analysis, and chat. 
              The header dropdown already has OpenAI, DeepSeek, Qwen, and Ollama options.
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button variant="contained" onClick={() => handleGo('/settings')}>Configure Now</Button>
              <Button variant="text" onClick={() => handleSkip(id)}>Skip</Button>
            </Stack>
          </Box>
        );

      case 3:
        return (
          <Box textAlign="center" py={4}>
            <FolderIcon sx={{ fontSize: 60, mb: 2, color: 'warning.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>Organize Your Library</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Create folders to organize papers by topic, methodology, or research area. The AI can suggest a taxonomy.
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button variant="contained" onClick={() => handleGo('/literature-tree')}>Create Folders</Button>
              <Button variant="text" onClick={() => handleSkip(id)}>Skip</Button>
            </Stack>
          </Box>
        );

      case 4:
        return (
          <Box textAlign="center" py={4}>
            <GoalIcon sx={{ fontSize: 60, mb: 2, color: 'info.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>Set Reading Goals</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Set weekly reading targets to stay on track with your research.
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button variant="contained" onClick={() => handleGo('/reading')}>Set Goals</Button>
              <Button variant="text" onClick={() => handleSkip(id)}>Skip</Button>
            </Stack>
          </Box>
        );

      case 5:
        return (
          <Box textAlign="center" py={4}>
            <LinkIcon sx={{ fontSize: 60, mb: 2, color: 'secondary.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>Connect Zotero</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Import your existing Zotero library with one click.
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button variant="contained" onClick={() => handleGo('/zotero')}>Connect Zotero</Button>
              <Button variant="text" onClick={() => handleSkip(id)}>Skip</Button>
            </Stack>
          </Box>
        );

      case 6:
        return (
          <Box textAlign="center" py={4}>
            <ExploreIcon sx={{ fontSize: 60, mb: 2, color: 'warning.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>Explore Features</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              You're all set! Here are some features to explore:
            </Typography>
            <Grid container spacing={1.5} justifyContent="center" sx={{ maxWidth: 500, mx: 'auto' }}>
              {[
                { label: 'Ask AI', path: '/ask', icon: '🤖' },
                { label: 'Knowledge Graph', path: '/knowledge', icon: '🕸️' },
                { label: 'Literature Tree', path: '/literature-tree', icon: '🌳' },
                { label: 'Research Chat', path: '/research-chat', icon: '💬' },
                { label: 'Flashcards', path: '/flashcards', icon: '🧠' },
                { label: 'Conference Tracker', path: '/conferences', icon: '🎯' },
              ].map((f, i) => (
                <Grid item key={i}>
                  <Button variant="outlined" onClick={() => handleGo(f.path)}>{f.icon} {f.label}</Button>
                </Grid>
              ))}
            </Grid>
            <Button variant="contained" sx={{ mt: 3 }} onClick={() => navigate('/')}>Go to Dashboard</Button>
          </Box>
        );

      default:
        return null;
    }
  };

  if (loading) return <Box textAlign="center" py={10}><CircularProgress /></Box>;
  if (onboarding && !onboarding.in_progress) return null; // Already completed

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
          {STEPS.map((s, i) => (
            <Step key={i} completed={onboarding?.steps?.[i]?.completed}>
              <StepLabel StepIconComponent={() => (
                <Box sx={{
                  width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', bgcolor: onboarding?.steps?.[i]?.completed ? 'success.main' : s.color,
                  color: 'white', fontSize: 18, mb: 1,
                }}>{onboarding?.steps?.[i]?.completed ? <DoneIcon fontSize="small" /> : s.icon}</Box>
              )}>{s.label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <LinearProgress variant="determinate" value={onboarding?.progress || 0}
          sx={{ height: 6, borderRadius: 3, mb: 3 }} />

        {renderStepContent(activeStep)}
      </Paper>
    </Box>
  );
};

export default OnboardingWizard;
