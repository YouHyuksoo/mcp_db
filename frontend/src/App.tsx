import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Patterns from './pages/Patterns';
import Databases from './pages/Databases';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <NavBar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/patterns" element={<Patterns />} />
          <Route path="/databases" element={<Databases />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
