import { useEffect, useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import { checkHealth, getPatternStats, getMetadataStats } from '../services/api';

interface HealthStatus {
  api: string;
  vector_db: string;
  embedding_service: string;
}

interface PatternStats {
  total_patterns: number;
  avg_success_rate: number;
  total_reuses: number;
  estimated_llm_calls_saved: number;
}

interface MetadataStats {
  metadata_count: number;
  patterns_count: number;
  business_rules_count: number;
  total_entries: number;
}

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [patternStats, setPatternStats] = useState<PatternStats | null>(null);
  const [metadataStats, setMetadataStats] = useState<MetadataStats | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [healthRes, patternRes, metadataRes] = await Promise.all([
          checkHealth(),
          getPatternStats(),
          getMetadataStats(),
        ]);

        setHealth(healthRes.data);
        setPatternStats(patternRes.data);
        setMetadataStats(metadataRes.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Health
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography>
                API: {health?.api === 'healthy' ? '✅' : '❌'} {health?.api}
              </Typography>
              <Typography>
                Vector DB: {health?.vector_db === 'healthy' ? '✅' : '❌'} {health?.vector_db}
              </Typography>
              <Typography>
                Embeddings: {health?.embedding_service === 'healthy' ? '✅' : '❌'}{' '}
                {health?.embedding_service}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Learning Statistics */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Learning Engine
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography>Patterns: {patternStats?.total_patterns || 0}</Typography>
              <Typography>
                Success Rate: {((patternStats?.avg_success_rate || 0) * 100).toFixed(1)}%
              </Typography>
              <Typography>Reuses: {patternStats?.total_reuses || 0}</Typography>
              <Typography>
                LLM Calls Saved: {patternStats?.estimated_llm_calls_saved || 0}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Vector DB Statistics */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Vector Database
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography>Tables: {metadataStats?.metadata_count || 0}</Typography>
              <Typography>Patterns: {metadataStats?.patterns_count || 0}</Typography>
              <Typography>Business Rules: {metadataStats?.business_rules_count || 0}</Typography>
              <Typography>Total Entries: {metadataStats?.total_entries || 0}</Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Start
            </Typography>
            <Typography variant="body2" sx={{ mt: 2 }}>
              1. Upload PowerBuilder files to extract SQL patterns automatically
            </Typography>
            <Typography variant="body2">
              2. View and manage learned SQL patterns
            </Typography>
            <Typography variant="body2">
              3. Connect databases and migrate metadata to Vector DB
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
