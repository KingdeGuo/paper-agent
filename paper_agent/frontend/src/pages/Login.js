import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  Link,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { login, register } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login: setAuth } = useAuth();
  
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (mode === 'register' && formData.password !== formData.confirmPassword) {
      setError(t('auth.passwordMismatch'));
      setLoading(false);
      return;
    }

    try {
      let response;
      
      if (mode === 'login') {
        response = await login({
          username: formData.username,
          password: formData.password,
        });
      } else {
        response = await register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.fullName,
        });
      }

      // Save token and user info
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user || { username: formData.username }));
      
      setAuth(response.user || { username: formData.username });
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" align="center" gutterBottom>
          {t('app.shortTitle')}
        </Typography>
        
        <Tabs
          value={mode}
          onChange={(e, newValue) => setMode(newValue)}
          centered
          sx={{ mb: 3 }}
        >
          <Tab label={t('auth.login')} value="login" />
          <Tab label={t('auth.register')} value="register" />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            margin="normal"
            label={t('auth.username')}
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />

          {mode === 'register' && (
            <>
              <TextField
                fullWidth
                margin="normal"
                label={t('auth.email')}
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
              <TextField
                fullWidth
                margin="normal"
                label={t('auth.fullName')}
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
              />
            </>
          )}

          <TextField
            fullWidth
            margin="normal"
            label={t('auth.password')}
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            required
            helperText={mode === 'register' ? t('auth.passwordHint') : ''}
          />

          {mode === 'register' && (
            <TextField
              fullWidth
              margin="normal"
              label={t('auth.confirmPassword')}
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              error={formData.confirmPassword && formData.password !== formData.confirmPassword}
              helperText={formData.confirmPassword && formData.password !== formData.confirmPassword ? t('auth.passwordMismatch') : ''}
            />
          )}

          <Button
            fullWidth
            type="submit"
            variant="contained"
            size="large"
            sx={{ mt: 3 }}
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} />
            ) : mode === 'login' ? (
              t('auth.login')
            ) : (
              t('auth.register')
            )}
          </Button>
        </Box>

        <Box mt={2} textAlign="center">
          <Typography variant="body2" color="textSecondary">
            {mode === 'login' ? (
              <>
                {t('auth.noAccount')}{' '}
                <Link
                  component="button"
                  onClick={() => setMode('register')}
                >
                  {t('auth.register')}
                </Link>
              </>
            ) : (
              <>
                {t('auth.hasAccount')}{' '}
                <Link
                  component="button"
                  onClick={() => setMode('login')}
                >
                  {t('auth.login')}
                </Link>
              </>
            )}
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login;
