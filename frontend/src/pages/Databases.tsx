import { Container, Typography, Paper, Box, Alert } from '@mui/material';

const Databases = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Database Management
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Alert severity="info">
          This page is under development. Future features:
        </Alert>
        <Box sx={{ mt: 2 }}>
          <ul>
            <li>
              <Typography variant="body2">View connected databases</Typography>
            </li>
            <li>
              <Typography variant="body2">Add new database connections</Typography>
            </li>
            <li>
              <Typography variant="body2">Explore schemas and tables</Typography>
            </li>
            <li>
              <Typography variant="body2">Migrate metadata to Vector DB</Typography>
            </li>
            <li>
              <Typography variant="body2">View database statistics</Typography>
            </li>
          </ul>
        </Box>
      </Paper>
    </Container>
  );
};

export default Databases;
