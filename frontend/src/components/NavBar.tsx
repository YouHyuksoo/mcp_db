import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import StorageIcon from '@mui/icons-material/Storage';
import DashboardIcon from '@mui/icons-material/Dashboard';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PatternIcon from '@mui/icons-material/Pattern';

const NavBar = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <StorageIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Oracle NL-SQL Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            startIcon={<DashboardIcon />}
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/upload"
            startIcon={<UploadFileIcon />}
          >
            Upload
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/patterns"
            startIcon={<PatternIcon />}
          >
            Patterns
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/databases"
            startIcon={<StorageIcon />}
          >
            Databases
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;
