import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Toolbar,
  IconButton,
  Typography,
  Slider,
  FormControlLabel,
  Switch,
  Paper,
  CircularProgress,
  Alert,
  Tooltip,
  Stack,
  Chip,
} from '@mui/material';
import {
  NavigateBefore,
  NavigateNext,
  ZoomIn,
  ZoomOut,
  Fullscreen,
  FullscreenExit,
  Highlight,
  NoteAdd,
  BookmarkAdd,
  BookmarkAdded,
} from '@mui/icons-material';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const PDFViewer = ({ documentId, fileUrl, onHighlight, onNote }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [highlights, setHighlights] = useState([]);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    if (documentId) {
      loadHighlights();
    }
  }, [documentId]);

  const loadHighlights = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/annotations/${documentId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setHighlights(data.highlights || []);
      }
    } catch (err) {
      console.error('Failed to load highlights:', err);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (error) => {
    console.error('PDF load error:', error);
    setError('Failed to load PDF. Please try again.');
    setLoading(false);
  };

  const changePage = (offset) => {
    setPageNumber((prevPageNumber) => {
      const newPage = prevPageNumber + offset;
      return Math.max(1, Math.min(newPage, numPages || 1));
    });
  };

  const changeScale = (event, newValue) => {
    setScale(newValue / 100);
  };

  const toggleFullscreen = () => {
    if (!fullscreen && containerRef.current) {
      containerRef.current.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setFullscreen(!fullscreen);
  };

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const range = selection.getRangeAt(0);
    const text = selection.toString().trim();
    
    if (text.length > 0 && onHighlight) {
      const rect = range.getBoundingClientRect();
      onHighlight({
        text,
        page: pageNumber,
        position: {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
        },
      });
    }
  }, [pageNumber, onHighlight]);

  useEffect(() => {
    document.addEventListener('mouseup', handleTextSelection);
    return () => document.removeEventListener('mouseup', handleTextSelection);
  }, [handleTextSelection]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="600px">
        <CircularProgress />
        <Typography ml={2}>Loading PDF...</Typography>
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      {/* Toolbar */}
      <Toolbar variant="dense" sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Stack direction="row" spacing={1} alignItems="center" width="100%">
          <IconButton
            onClick={() => changePage(-1)}
            disabled={pageNumber <= 1}
            size="small"
          >
            <NavigateBefore />
          </IconButton>
          
          <Typography variant="body2">
            Page {pageNumber} of {numPages}
          </Typography>
          
          <IconButton
            onClick={() => changePage(1)}
            disabled={pageNumber >= (numPages || 1)}
            size="small"
          >
            <NavigateNext />
          </IconButton>

          <Box flex={1} />

          <ZoomOut fontSize="small" />
          <Slider
            value={scale * 100}
            onChange={changeScale}
            min={50}
            max={200}
            step={10}
            sx={{ width: 100, mx: 1 }}
          />
          <ZoomIn fontSize="small" />

          <Tooltip title="Toggle Annotations">
            <IconButton
              onClick={() => setShowAnnotations(!showAnnotations)}
              color={showAnnotations ? 'primary' : 'default'}
              size="small"
            >
              <Highlight fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Add Note">
            <IconButton
              onClick={() => onNote && onNote({ page: pageNumber })}
              size="small"
            >
              <NoteAdd fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title={fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
            <IconButton onClick={toggleFullscreen} size="small">
              {fullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Tooltip>
        </Stack>
      </Toolbar>

      {/* Highlights indicator */}
      {highlights.length > 0 && (
        <Box mb={2}>
          <Chip
            icon={<BookmarkAdded />}
            label={`${highlights.length} highlights`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>
      )}

      {/* PDF Document */}
      <Box
        ref={containerRef}
        sx={{
          overflow: 'auto',
          maxHeight: fullscreen ? '100vh' : '800px',
          display: 'flex',
          justifyContent: 'center',
          bgcolor: '#f5f5f5',
          p: 2,
        }}
      >
        <Document
          file={fileUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading={
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          }
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            renderTextLayer={true}
            renderAnnotationLayer={showAnnotations}
          />
        </Document>
      </Box>

      {/* Page Navigation */}
      {numPages > 1 && (
        <Box display="flex" justifyContent="center" mt={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            <IconButton
              onClick={() => setPageNumber(1)}
              disabled={pageNumber <= 1}
              size="small"
            >
              First
            </IconButton>
            <IconButton
              onClick={() => changePage(-10)}
              disabled={pageNumber <= 10}
              size="small"
            >
              -10
            </IconButton>
            <IconButton
              onClick={() => changePage(-1)}
              disabled={pageNumber <= 1}
              size="small"
            >
              ‹
            </IconButton>
            
            <Typography variant="body2" mx={2}>
              {pageNumber} / {numPages}
            </Typography>
            
            <IconButton
              onClick={() => changePage(1)}
              disabled={pageNumber >= (numPages || 1)}
              size="small"
            >
              ›
            </IconButton>
            <IconButton
              onClick={() => changePage(10)}
              disabled={pageNumber > (numPages || 1) - 10}
              size="small"
            >
              +10
            </IconButton>
            <IconButton
              onClick={() => setPageNumber(numPages)}
              disabled={pageNumber >= (numPages || 1)}
              size="small"
            >
              Last
            </IconButton>
          </Stack>
        </Box>
      )}
    </Paper>
  );
};

export default PDFViewer;
