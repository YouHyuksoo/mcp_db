/**
 * API client for Oracle NL-SQL Management Backend
 */

import axios from "axios"
import type {
  HealthStatus,
  DashboardSummary,
  DatabaseListResponse,
  TNSNamesParseResponse,
  DatabaseConnection,
  RegisteredDatabaseListResponse,
  DatabaseCredentials,
  ListPatternsResponse,
  PatternStatsResponse
} from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
})

// API endpoints
export const api = {
  /**
   * Health check endpoint
   */
  health: {
    async check(): Promise<HealthStatus> {
      const response = await apiClient.get<HealthStatus>("/api/health")
      return response.data
    },
  },

  /**
   * Dashboard endpoints
   */
  dashboard: {
    /**
     * Get comprehensive dashboard summary
     */
    async getSummary(): Promise<DashboardSummary> {
      const response = await apiClient.get<DashboardSummary>("/api/v1/dashboard/summary")
      return response.data
    },

    /**
     * Get list of registered databases
     */
    async getDatabases(): Promise<DatabaseListResponse> {
      const response = await apiClient.get<DatabaseListResponse>("/api/v1/dashboard/databases")
      return response.data
    },
  },

  /**
   * Metadata endpoints
   */
  metadata: {
    /**
     * Upload and process CSV files to create metadata
     */
    async process(formData: FormData): Promise<{
      success: boolean
      tables_processed: number
      database_sid: string
      schema_name: string
      error?: string
    }> {
      const response = await axios.post(`${API_BASE_URL}/api/v1/metadata/process`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 60000, // 60 seconds for processing
      })
      return response.data
    },

    /**
     * Migrate/Re-process metadata from JSON files to Vector DB
     */
    async migrate(params: {
      metadata_dir: string
      database_sid: string
      schema_name: string
    }): Promise<{
      success: boolean
      tables_migrated: number
      database_sid: string
      schema_name: string
      error?: string
    }> {
      const response = await apiClient.post("/api/v1/metadata/migrate", params)
      return response.data
    },

    /**
     * Get list of metadata for a specific database
     */
    async list(params?: {
      database_sid?: string
      schema_name?: string
    }): Promise<{
      metadata: Array<{
        table_name: string
        table_comment: string
        column_count: number
        last_updated: string
      }>
      total_count: number
    }> {
      const queryParams = new URLSearchParams()
      if (params?.database_sid) queryParams.append("database_sid", params.database_sid)
      if (params?.schema_name) queryParams.append("schema_name", params.schema_name)

      const url = `/api/v1/metadata/list${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
      const response = await apiClient.get(url)
      return response.data
    },
  },

  /**
   * TNSNames endpoints
   */
  tnsnames: {
    /**
     * Parse tnsnames.ora file
     */
    async parse(filePath: string): Promise<TNSNamesParseResponse> {
      const response = await apiClient.post<TNSNamesParseResponse>("/api/v1/tnsnames/parse", {
        file_path: filePath,
      })
      return response.data
    },

    /**
     * Get list of parsed databases
     */
    async list(): Promise<{ databases: DatabaseConnection[]; total_count: number }> {
      const response = await apiClient.get("/api/v1/tnsnames/list")
      return response.data
    },

    /**
     * Search databases by keyword
     */
    async search(keyword: string): Promise<{ databases: DatabaseConnection[]; total_count: number }> {
      const response = await apiClient.get(`/api/v1/tnsnames/search/${keyword}`)
      return response.data
    },
  },

  /**
   * Database credentials management endpoints
   */
  databases: {
    /**
     * Get list of registered databases
     */
    async list(): Promise<RegisteredDatabaseListResponse> {
      const response = await apiClient.get<RegisteredDatabaseListResponse>("/api/v1/databases/list")
      return response.data
    },

    /**
     * Register new database
     */
    async register(credentials: DatabaseCredentials): Promise<{ success: boolean; message: string; database_sid: string }> {
      const response = await apiClient.post("/api/v1/databases/register", credentials)
      return response.data
    },

    /**
     * Delete registered database
     */
    async delete(databaseSid: string): Promise<{ success: boolean; message: string; database_sid: string }> {
      const response = await apiClient.delete(`/api/v1/databases/${databaseSid}`)
      return response.data
    },

    /**
     * Register database from tnsnames.ora
     */
    async registerFromTnsnames(sid: string, schemaName: string, user: string, password: string): Promise<{ success: boolean; message: string; database_sid: string }> {
      const response = await apiClient.post(`/api/v1/databases/register-from-tnsnames/${sid}`, {
        schema_name: schemaName,
        user,
        password
      })
      return response.data
    },

    /**
     * Get database info
     */
    async getInfo(databaseSid: string): Promise<any> {
      const response = await apiClient.get(`/api/v1/databases/${databaseSid}/info`)
      return response.data
    },
  },

  /**
   * SQL Pattern endpoints
   */
  patterns: {
    /**
     * List all learned patterns (with optional filtering)
     */
    async list(params?: {
      database_sid?: string
      schema_name?: string
      limit?: number
    }): Promise<ListPatternsResponse> {
      const queryParams = new URLSearchParams()
      if (params?.database_sid) queryParams.append("database_sid", params.database_sid)
      if (params?.schema_name) queryParams.append("schema_name", params.schema_name)
      if (params?.limit) queryParams.append("limit", params.limit.toString())

      const url = `/api/v1/patterns/list${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
      const response = await apiClient.get<ListPatternsResponse>(url)
      return response.data
    },

    /**
     * Get pattern statistics
     */
    async getStats(): Promise<PatternStatsResponse> {
      const response = await apiClient.get<PatternStatsResponse>("/api/v1/patterns/stats")
      return response.data
    },

    /**
     * Delete a pattern by ID
     */
    async delete(patternId: string): Promise<{ success: boolean; message: string }> {
      const response = await apiClient.delete(`/api/v1/patterns/${patternId}`)
      return response.data
    },
  },
}

export default api
