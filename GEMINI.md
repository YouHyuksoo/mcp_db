# Gemini Context: Oracle Database MCP Server

## Project Overview

This project is a Python-based **Model-Context-Protocol (MCP) Server** designed to facilitate natural language querying of Oracle databases. It runs locally and integrates directly with the Claude Desktop application, acting as a bridge between the AI assistant and one or more Oracle databases.

The server's primary role is to provide comprehensive, context-rich metadata to the Claude AI, which then uses that metadata to generate and execute Oracle SQL queries. It does **not** call any external LLM APIs itself; all AI reasoning is handled by the Claude Desktop client.

**Core Technologies:**
- **Language:** Python 3.9+
- **Database:** Oracle DB (via `oracledb` driver)
- **Key Libraries:** `mcp`, `pandas`, `cryptography`, `python-dotenv`
- **AI Integration:** Claude Desktop (via MCP)

## Key Workflows

### 1. Metadata Integration
The server builds a "unified metadata" store by combining:
1.  **Technical Schema:** Automatically extracted from the Oracle DB (tables, columns, PKs, FKs, indexes).
2.  **Business Context:** Provided by the user via structured CSV files (`common_columns_template.csv`, `code_definitions_template.csv`, `table_info_template.csv`) located in the `common_metadata` directory. This includes human-readable names, descriptions, and business rules.

The main tool for this is `extract_and_integrate_metadata`.

### 2. Natural Language to SQL (2-Stage Process)
This is the central feature, driven by the Claude Desktop app:
- **Stage 1:** Claude calls `get_table_summaries_for_query` to get a high-level summary of all tables. Based on this and the user's query, Claude selects the most relevant tables.
- **Stage 2:** Claude calls `get_detailed_metadata_for_sql` for the selected tables. The server provides the rich, unified metadata for only those tables.
- **SQL Generation:** Claude uses this detailed context to construct an accurate Oracle SQL query.
- **Execution:** Claude calls `execute_sql` to run the query via the server and return the results.

### 3. Database Exploration
The server provides a suite of tools for exploring the database schema, including:
- `show_databases`, `show_schemas`, `show_tables`
- `describe_table`
- `show_procedures`, `show_procedure_source`

## Building and Running

This project is designed to be run as a service invoked by the Claude Desktop application.

### 1. Installation
A Python virtual environment (`venv`) is already present. To ensure all dependencies are installed:
```bash
# Activate the virtual environment
.\venv\Scripts\activate

# Install/verify dependencies
pip install -r requirements.txt
```

### 2. Configuration
- **Encryption Key:** The application uses an encryption key to secure database credentials. This key must be set in a `.env` file.
  ```bash
  # Create the .env file from the example
  copy .env.example .env

  # Generate a new key and add it to the .env file
  # (Run this python command and paste the output into the .env file)
  python -c "from cryptography.fernet import Fernet; print(f'ENCRYPTION_KEY={Fernet.generate_key().decode()}')"
  ```
- **Claude Desktop:** The Claude Desktop application must be configured to connect to this MCP server. Edit the `claude_desktop_config.json` file (typically in `%APPDATA%\Claude\`) to include:
  ```json
  {
    "mcpServers": {
      "oracle-db": {
        "command": "D:\\Project\\mcp_db\\venv\\Scripts\\python.exe",
        "args": ["-m", "src.mcp_server"],
        "cwd": "D:\\Project\\mcp_db",
        "env": {
          "PYTHONPATH": "D:\\Project\\mcp_db"
        }
      }
    }
  }
  ```
  *(Note: The file paths should be absolute and match your system.)*

### 3. Running the Server
The server is started **automatically by the Claude Desktop application** when a tool from the `oracle-db` MCP server is invoked. There is no need to run `mcp_server.py` manually.

## Development Conventions

- **Main Entrypoint:** `src/mcp_server.py` defines all the tools and the main server loop.
- **Modularity:** Functionality is broken into separate modules within the `src/` directory (e.g., `oracle_connector.py`, `metadata_manager.py`, `credentials_manager.py`).
- **Metadata:** All metadata is stored in the `metadata/` and `common_metadata/` directories. The `credentials/` directory stores encrypted connection strings.
- **Dependencies:** Project dependencies are managed in `requirements.txt`.
- **SQL Rules:** The file `sql_rules.md` contains guidelines for the LLM on how to generate correct and optimal Oracle SQL. These rules can be viewed and updated via the `view_sql_rules` and `update_sql_rules` tools.
