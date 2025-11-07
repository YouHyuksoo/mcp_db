import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// Health check
export const checkHealth = () => {
  return api.get('/../../api/health');
};

// Metadata APIs
export const searchMetadata = (question: string, limit: number = 5) => {
  return api.post('/metadata/search', { question, limit });
};

export const migrateMetadata = (database_sid: string, schema_name: string, metadata_dir: string) => {
  return api.post('/metadata/migrate', { database_sid, schema_name, metadata_dir });
};

export const getMetadataStats = () => {
  return api.get('/metadata/stats');
};

// Pattern APIs
export const learnPattern = (data: {
  question: string;
  sql_query: string;
  database_sid: string;
  schema_name: string;
  tables_used: string[];
  execution_success: boolean;
  execution_time_ms?: number;
  row_count?: number;
}) => {
  return api.post('/patterns/learn', data);
};

export const findSimilarPattern = (question: string, database_sid: string, schema_name: string) => {
  return api.post('/patterns/find-similar', { question, database_sid, schema_name });
};

export const listPatterns = (database_sid?: string, schema_name?: string, limit: number = 100) => {
  return api.get('/patterns/list', { params: { database_sid, schema_name, limit } });
};

export const deletePattern = (pattern_id: string) => {
  return api.delete(`/patterns/${pattern_id}`);
};

export const getPatternStats = () => {
  return api.get('/patterns/stats');
};

// PowerBuilder APIs
export const uploadPowerBuilderFiles = (files: File[], database_sid: string, schema_name: string) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('database_sid', database_sid);
  formData.append('schema_name', schema_name);

  return api.post('/powerbuilder/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getJobStatus = (job_id: string) => {
  return api.get(`/powerbuilder/jobs/${job_id}`);
};

export const listJobs = () => {
  return api.get('/powerbuilder/jobs');
};

export const deleteJob = (job_id: string) => {
  return api.delete(`/powerbuilder/jobs/${job_id}`);
};

export default api;
