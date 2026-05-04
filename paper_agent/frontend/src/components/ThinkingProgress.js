import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Typography,
  LinearProgress,
  Paper,
  Chip,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

const ThinkingProgress = ({ thinkingText = '' }) => {
  const { t } = useTranslation();

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <AutoAwesomeIcon sx={{ mr: 1, color: 'secondary.main' }} />
        <Typography variant="subtitle2" color="textSecondary">
          {t('documentDetail.thinkingProcess')}
        </Typography>
        <Chip
          label={t('documentDetail.inProgress')}
          size="small"
          color="warning"
          sx={{ ml: 1 }}
        />
      </Box>
      <LinearProgress sx={{ mb: 2 }} />
      {thinkingText && (
        <Typography
          variant="body2"
          color="textSecondary"
          sx={{
            fontStyle: 'italic',
            maxHeight: 100,
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {thinkingText}
        </Typography>
      )}
    </Paper>
  );
};

export default ThinkingProgress;