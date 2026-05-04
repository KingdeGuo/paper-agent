import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Paper,
  Chip,
  Stack,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
} from '@mui/material';
import { summaryAPI } from '../services/api';
import api from '../services/api';

/**
 * Knowledge Graph Visualization Component
 * Uses D3.js for rendering the graph
 */
const KnowledgeGraph = ({ documentId, onNodeClick }) => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [depth, setDepth] = useState(1);
  const [viewMode, setViewMode] = useState('document'); // 'document' or 'global'
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const svgRef = useRef(null);

  useEffect(() => {
    loadGraphData();
  }, [documentId, depth, viewMode]);

  useEffect(() => {
    if (graphData && svgRef.current) {
      renderGraph();
    }
  }, [graphData]);

  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = '/knowledge/graph/visualization';
      if (viewMode === 'document' && documentId) {
        url = `/knowledge/graph/${documentId}?depth=${depth}`;
      }
      
      const response = await api.get(url);
      setGraphData(response.data);
    } catch (err) {
      setError(err.message || 'Failed to load graph data');
    } finally {
      setLoading(false);
    }
  };

  const renderGraph = () => {
    import('d3').then((d3) => {
      const svg = d3.select(svgRef.current);
      svg.selectAll('*').remove();

      const width = svgRef.current.clientWidth;
      const height = 600;

      svg.attr('viewBox', [0, 0, width, height]);

      const simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.edges).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(60));

      const g = svg.append('g');

      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => g.attr('transform', event.transform));

      svg.call(zoom);

      // Arrow markers for directed edges
      svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('xoverflow', 'visible')
        .append('svg:path')
        .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
        .attr('fill', '#999')
        .style('stroke', 'none');

      const links = g.append('g')
        .selectAll('line')
        .data(graphData.edges)
        .enter()
        .append('line')
        .attr('stroke', d => {
          if (d.type === 'improves_upon') return '#FF6B6B';
          if (d.type === 'contradicts') return '#FFA500';
          return '#999';
        })
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => d.type === 'cites' ? 1 : 2.5)
        .attr('marker-end', 'url(#arrowhead)')
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
          setSelectedEdge(d);
          setSelectedNode(null);
          event.stopPropagation();
        });

      const nodes = g.append('g')
        .selectAll('circle')
        .data(graphData.nodes)
        .enter()
        .append('circle')
        .attr('r', d => (d.center ? 14 : 10))
        .attr('fill', d => {
          if (d.center) return '#FF6B6B';
          if (d.type === 'reference') return '#A8E6CF';
          if (d.type === 'paper') return '#3498DB';
          return '#95A5A6';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .style('filter', 'drop-shadow(0px 2px 2px rgba(0,0,0,0.1))')
        .call(drag(simulation, d3))
        .on('click', (event, d) => {
          setSelectedNode(d);
          setSelectedEdge(null);
          if (onNodeClick) onNodeClick(d.id);
          event.stopPropagation();
        });

      const labels = g.append('g')
        .selectAll('text')
        .data(graphData.nodes)
        .enter()
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', -20)
        .attr('font-size', '10px')
        .attr('font-family', 'Inter, sans-serif')
        .attr('fill', '#2C3E50')
        .style('pointer-events', 'none')
        .text(d => (d.label || d.id).substring(0, 25) + (d.label?.length > 25 ? '...' : ''));

      simulation.on('tick', () => {
        links
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);

        labels
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      });

      svg.on('click', () => {
        setSelectedNode(null);
        setSelectedEdge(null);
      });
    });
  };

  const drag = (simulation, d3) => {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x; d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      });
  };

  if (loading) return <Box display="flex" justifyContent="center" py={10}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={selectedNode || selectedEdge ? 8 : 12}>
        <Paper elevation={3} sx={{ p: 2, borderRadius: 2, position: 'relative' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Knowledge Network</Typography>
              <Chip label={viewMode === 'document' ? 'Local' : 'Global'} size="small" color="primary" variant="outlined" />
            </Stack>
            
            <Stack direction="row" spacing={1}>
              <FormControl size="small">
                <Select value={viewMode} onChange={(e) => setViewMode(e.target.value)}>
                  <MenuItem value="document">Current Paper</MenuItem>
                  <MenuItem value="global">Entire Library</MenuItem>
                </Select>
              </FormControl>
              {viewMode === 'document' && (
                <FormControl size="small">
                  <Select value={depth} onChange={(e) => setDepth(e.target.value)}>
                    <MenuItem value={1}>Depth 1</MenuItem>
                    <MenuItem value={2}>Depth 2</MenuItem>
                  </Select>
                </FormControl>
              )}
            </Stack>
          </Box>

          <Box ref={svgRef} sx={{ width: '100%', height: 600, bgcolor: '#fdfdfd', borderRadius: 1 }} />
          
          <Box sx={{ position: 'absolute', bottom: 20, left: 20, bgcolor: 'rgba(255,255,255,0.8)', p: 1, borderRadius: 1, border: '1px solid #eee' }}>
            <Typography variant="caption" display="block">Legend:</Typography>
            <Stack direction="row" spacing={1} mt={0.5}>
              <Box sx={{ width: 12, height: 12, bgcolor: '#FF6B6B', borderRadius: '50%' }} /> <Typography variant="caption">Active</Typography>
              <Box sx={{ width: 12, height: 12, bgcolor: '#3498DB', borderRadius: '50%' }} /> <Typography variant="caption">Paper</Typography>
              <Box sx={{ width: 12, height: 12, bgcolor: '#A8E6CF', borderRadius: '50%' }} /> <Typography variant="caption">Reference</Typography>
            </Stack>
          </Box>
        </Paper>
      </Grid>

      {(selectedNode || selectedEdge) && (
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', borderRadius: 2, boxShadow: 3 }}>
            <CardContent>
              {selectedNode ? (
                <>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ fontWeight: 'bold' }}>
                    Node Details
                  </Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    {selectedNode.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Type: <Chip label={selectedNode.type} size="small" sx={{ ml: 1 }} />
                  </Typography>
                  {selectedNode.authors?.length > 0 && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      <strong>Authors:</strong> {selectedNode.authors.join(', ')}
                    </Typography>
                  )}
                  {selectedNode.year && (
                    <Typography variant="body2">
                      <strong>Year:</strong> {selectedNode.year}
                    </Typography>
                  )}
                  <Button variant="contained" fullWidth sx={{ mt: 3 }} size="small" onClick={() => window.open(`/documents/${selectedNode.id}`, '_blank')}>
                    View Full Details
                  </Button>
                </>
              ) : (
                <>
                  <Typography variant="h6" gutterBottom color="secondary" sx={{ fontWeight: 'bold' }}>
                    Link Discovery
                  </Typography>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                    Relationship: {selectedEdge.label}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary', lineHeight: 1.6 }}>
                    {selectedEdge.explanation || "System identified a connection based on shared content and citation patterns."}
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );
};

export default KnowledgeGraph;
