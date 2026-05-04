import React from 'react';
import { useTranslation } from 'react-i18next';
import { Box, Typography, Container } from '@mui/material';
import KnowledgeGraph from '../components/KnowledgeGraph';

const Knowledge = () => {
  const { t } = useTranslation();

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', mb: 4 }}>
          {t('nav.knowledge') || 'Semantic Knowledge Network'}
        </Typography>
        
        <KnowledgeGraph viewMode="global" />
      </Box>
    </Container>
  );
};

export default Knowledge;
