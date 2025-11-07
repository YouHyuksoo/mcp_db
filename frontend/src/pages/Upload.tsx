import { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  Alert,
  LinearProgress,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { uploadPowerBuilderFiles } from '../services/api';

const Upload = () => {
  const [databaseSid, setDatabaseSid] = useState('');
  const [schemaName, setSchemaName] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/octet-stream': ['.srw', '.srd', '.pbl', '.sra'],
    },
    onDrop: (acceptedFiles) => {
      setFiles(acceptedFiles);
      setMessage(null);
    },
  });

  const handleUpload = async () => {
    if (!databaseSid || !schemaName) {
      setMessage({ type: 'error', text: 'Please enter Database SID and Schema Name' });
      return;
    }

    if (files.length === 0) {
      setMessage({ type: 'error', text: 'Please select files to upload' });
      return;
    }

    try {
      setUploading(true);
      setMessage(null);

      const response = await uploadPowerBuilderFiles(files, databaseSid, schemaName);

      setMessage({
        type: 'success',
        text: `Upload successful! Job ID: ${response.data.job_id}. Processing in background...`,
      });
      setFiles([]);
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Upload failed',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Upload PowerBuilder Files
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Database SID"
            value={databaseSid}
            onChange={(e) => setDatabaseSid(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Schema Name"
            value={schemaName}
            onChange={(e) => setSchemaName(e.target.value)}
          />
        </Box>

        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.400',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'background.paper',
            '&:hover': {
              bgcolor: 'action.hover',
            },
          }}
        >
          <input {...getInputProps()} />
          <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6">
            {isDragActive ? 'Drop files here' : 'Drag & drop PowerBuilder files'}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            or click to browse (.srw, .srd, .pbl, .sra files)
          </Typography>
        </Box>

        {files.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Selected Files ({files.length}):
            </Typography>
            {files.map((file, index) => (
              <Typography key={index} variant="body2">
                - {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </Typography>
            ))}
          </Box>
        )}

        {message && (
          <Alert severity={message.type} sx={{ mt: 2 }}>
            {message.text}
          </Alert>
        )}

        {uploading && <LinearProgress sx={{ mt: 2 }} />}

        <Button
          variant="contained"
          fullWidth
          onClick={handleUpload}
          disabled={uploading}
          sx={{ mt: 3 }}
        >
          {uploading ? 'Uploading...' : 'Upload Files'}
        </Button>
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          About PowerBuilder Parsing
        </Typography>
        <Typography variant="body2" paragraph>
          Upload PowerBuilder source files (.srw, .srd, .pbl) to automatically extract:
        </Typography>
        <ul>
          <li>
            <Typography variant="body2">SQL queries (SELECT, INSERT, UPDATE, DELETE)</Typography>
          </li>
          <li>
            <Typography variant="body2">Table relationships and JOINs</Typography>
          </li>
          <li>
            <Typography variant="body2">Business rules from comments</Typography>
          </li>
          <li>
            <Typography variant="body2">Data flow and logic patterns</Typography>
          </li>
        </ul>
        <Typography variant="body2" color="textSecondary">
          Processing happens in the background. Check job status after upload.
        </Typography>
      </Paper>
    </Container>
  );
};

export default Upload;
