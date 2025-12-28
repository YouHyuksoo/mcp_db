/**
 * Type definitions for Oracle NL-SQL Management Backend API
 */

// Health check types
export interface HealthStatus {
  api: string;
  vector_db: string;
  embedding_service: string;
}

// Vector DB statistics
export interface VectorDBStats {
  metadata_count: number;
  patterns_count: number;
  business_rules_count: number;
}

// Database information
export interface DatabaseInfo {
  database_sid: string;
  schema_name: string;
  table_count: number;
  last_updated: string | null;
  connection_status: string;
}

// Uploaded file information
export interface UploadedFile {
  file_name: string;
  file_type: string;
  upload_time: string;
  file_size: number;
  processing_status: string;
  rules_extracted: number | null;
}

// Pattern summary
export interface PatternSummary {
  pattern_id: string;
  question: string;
  database_sid: string;
  schema_name: string;
  use_count: number;
  success_rate: number;
  learned_at: string;
}

// Complete dashboard summary
export interface DashboardSummary {
  vector_db_stats: VectorDBStats;
  registered_databases: DatabaseInfo[];
  recent_patterns: PatternSummary[];
  upload_history: UploadedFile[];
  total_databases: number;
  total_patterns: number;
  total_uploads: number;
}

// Database list response
export interface DatabaseListResponse {
  databases: DatabaseInfo[];
  total_count: number;
}

// TNSNames types
export interface DatabaseConnection {
  sid: string;
  host: string;
  port: number;
  service_name: string;
  connection_type: string;
  description?: string;
}

export interface TNSNamesParseResponse {
  success: boolean;
  total_databases: number;
  databases: DatabaseConnection[];
  file_path: string;
  error?: string;
}

// Registered Database types
export interface RegisteredDatabase {
  database_sid: string;
  schema_name: string;
  host: string;
  port: number;
  service_name: string;
  user: string;
  is_connected: boolean;
  table_count: number;
  last_updated?: string | null;
}

export interface RegisteredDatabaseListResponse {
  databases: RegisteredDatabase[];
  total_count: number;
}

export interface DatabaseCredentials {
  database_sid: string;
  schema_name: string;
  host: string;
  port: number;
  service_name: string;
  user: string;
  password: string;
}

// Pattern types (matching backend models)
export interface PatternInfo {
  pattern_id: string;
  question: string;
  sql_query: string;
  database_sid: string;
  schema_name: string;
  use_count: number;
  success_rate: number;
  avg_execution_time_ms: number | null;
  avg_user_rating: number | null;
  learned_at: string;
  last_used_at: string | null;
}

export interface ListPatternsResponse {
  patterns: PatternInfo[];
  total_count: number;
}

export interface PatternStatsResponse {
  total_patterns: number;
  avg_success_rate: number;
  total_reuses: number;
  estimated_llm_calls_saved: number;
}
