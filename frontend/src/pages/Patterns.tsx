import { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  CircularProgress,
  Box,
  Chip,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { listPatterns, deletePattern } from '../services/api';

interface Pattern {
  pattern_id: string;
  question: string;
  sql_query: string;
  database_sid: string;
  schema_name: string;
  use_count: number;
  success_rate: number;
  learned_at: string;
}

const Patterns = () => {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPatterns = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await listPatterns();
      setPatterns(response.data.patterns);
    } catch (err: any) {
      setError(err.message || 'Failed to load patterns');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns();
  }, []);

  const handleDelete = async (patternId: string) => {
    if (!confirm('Are you sure you want to delete this pattern?')) {
      return;
    }

    try {
      await deletePattern(patternId);
      await fetchPatterns();
    } catch (err: any) {
      setError(err.message || 'Failed to delete pattern');
    }
  };

  if (loading) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Learned SQL Patterns
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ mt: 3 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Question</TableCell>
                <TableCell>Database</TableCell>
                <TableCell>SQL Preview</TableCell>
                <TableCell align="right">Use Count</TableCell>
                <TableCell align="right">Success Rate</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {patterns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Box sx={{ py: 4 }}>
                      <Typography color="textSecondary">
                        No patterns learned yet. Start using the system to build up SQL patterns!
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                patterns.map((pattern) => (
                  <TableRow key={pattern.pattern_id}>
                    <TableCell sx={{ maxWidth: 300 }}>
                      <Typography variant="body2">{pattern.question}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={`${pattern.database_sid}.${pattern.schema_name}`}
                        size="small"
                      />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 400 }}>
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.85rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {pattern.sql_query.substring(0, 100)}...
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip label={pattern.use_count} size="small" color="primary" />
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${(pattern.success_rate * 100).toFixed(1)}%`}
                        size="small"
                        color={pattern.success_rate > 0.8 ? 'success' : 'warning'}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(pattern.pattern_id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};

export default Patterns;
