"""
PowerBuilder Parser
Extracts SQL queries, table relationships, and business logic from PowerBuilder source files
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PowerBuilderParser:
    """Parser for PowerBuilder .srw, .srd, .pbl files"""

    def __init__(self):
        """Initialize PowerBuilder parser"""
        # SQL patterns (case-insensitive)
        self.sql_patterns = [
            # SELECT statements
            re.compile(r'SELECT\s+.+?FROM\s+.+?(?:WHERE|GROUP BY|ORDER BY|;|\n\n)', re.IGNORECASE | re.DOTALL),
            # INSERT statements
            re.compile(r'INSERT\s+INTO\s+.+?VALUES\s+.+?(?:;|\n)', re.IGNORECASE | re.DOTALL),
            # UPDATE statements
            re.compile(r'UPDATE\s+.+?SET\s+.+?(?:WHERE|;|\n)', re.IGNORECASE | re.DOTALL),
            # DELETE statements
            re.compile(r'DELETE\s+FROM\s+.+?(?:WHERE|;|\n)', re.IGNORECASE | re.DOTALL),
        ]

        # Table name patterns
        self.table_pattern = re.compile(
            r'(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([A-Z_][A-Z0-9_]*)',
            re.IGNORECASE
        )

        # Comment patterns (PowerBuilder uses // and /* */)
        self.comment_patterns = [
            re.compile(r'//.*?$', re.MULTILINE),
            re.compile(r'/\*.*?\*/', re.DOTALL)
        ]

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a PowerBuilder source file

        Args:
            file_path: Path to .srw, .srd, or .pbl file

        Returns:
            Dict with extracted information
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            logger.error(f"File not found: {file_path}")
            return self._empty_result()

        try:
            # Try multiple encodings (PowerBuilder files can use various encodings)
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'utf-16']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.debug(f"Successfully read file with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                logger.error(f"Could not read file with any encoding: {file_path}")
                return self._empty_result()

            # Parse content
            result = {
                "file_name": file_path_obj.name,
                "file_path": str(file_path_obj.absolute()),
                "file_type": file_path_obj.suffix.lower(),
                "sql_queries": self.extract_sql_queries(content),
                "tables_referenced": self.extract_table_references(content),
                "business_rules": self.extract_business_rules(content),
                "comments": self.extract_comments(content),
                "success": True
            }

            logger.info(
                f"Parsed {file_path_obj.name}: "
                f"{len(result['sql_queries'])} SQL queries, "
                f"{len(result['tables_referenced'])} tables"
            )

            return result

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return self._empty_result()

    def extract_sql_queries(self, content: str) -> List[Dict[str, str]]:
        """
        Extract SQL queries from PowerBuilder source

        Args:
            content: File content

        Returns:
            List of SQL queries with metadata
        """
        queries = []

        for pattern in self.sql_patterns:
            matches = pattern.findall(content)
            for match in matches:
                # Clean up the SQL
                sql = match.strip()
                sql = re.sub(r'\s+', ' ', sql)  # Normalize whitespace

                # Determine query type
                query_type = self._determine_query_type(sql)

                queries.append({
                    "sql": sql,
                    "type": query_type,
                    "tables": self._extract_tables_from_sql(sql)
                })

        # Remove duplicates
        unique_queries = []
        seen_sqls = set()

        for query in queries:
            sql_normalized = query["sql"].lower()
            if sql_normalized not in seen_sqls:
                seen_sqls.add(sql_normalized)
                unique_queries.append(query)

        return unique_queries

    def extract_table_references(self, content: str) -> List[str]:
        """
        Extract all table references from content

        Args:
            content: File content

        Returns:
            List of unique table names
        """
        tables = set()

        # Find all table names
        matches = self.table_pattern.findall(content)
        for match in matches:
            # Filter out SQL keywords
            if match.upper() not in ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'GROUP']:
                tables.add(match.upper())

        return sorted(list(tables))

    def extract_business_rules(self, content: str) -> List[Dict[str, str]]:
        """
        Extract business rules from comments and code patterns

        Args:
            content: File content

        Returns:
            List of business rules
        """
        rules = []

        # Extract meaningful comments (longer than 20 chars)
        comments = self.extract_comments(content)

        for comment in comments:
            comment_text = comment["text"].strip()

            # Look for business rule indicators
            indicators = ['rule:', 'business:', 'logic:', 'validation:', 'must', 'should', 'if']

            if len(comment_text) > 20 and any(ind in comment_text.lower() for ind in indicators):
                rules.append({
                    "type": "comment",
                    "text": comment_text,
                    "context": comment.get("context", "")
                })

        # Look for IF-THEN patterns (common in business logic)
        if_then_pattern = re.compile(
            r'IF\s+(.+?)\s+THEN\s+(.+?)(?:ELSE|END IF)',
            re.IGNORECASE | re.DOTALL
        )

        if_then_matches = if_then_pattern.findall(content)
        for condition, action in if_then_matches:
            rules.append({
                "type": "if_then_logic",
                "condition": condition.strip()[:200],  # Limit length
                "action": action.strip()[:200]
            })

        return rules

    def extract_comments(self, content: str) -> List[Dict[str, str]]:
        """
        Extract comments from PowerBuilder source

        Args:
            content: File content

        Returns:
            List of comments
        """
        comments = []

        # Single-line comments //
        single_line_comments = re.findall(r'//(.*)$', content, re.MULTILINE)
        for comment in single_line_comments:
            text = comment.strip()
            if text:  # Ignore empty comments
                comments.append({
                    "type": "single_line",
                    "text": text
                })

        # Multi-line comments /* */
        multi_line_comments = re.findall(r'/\*(.*?)\*/', content, re.DOTALL)
        for comment in multi_line_comments:
            text = comment.strip()
            if text:
                comments.append({
                    "type": "multi_line",
                    "text": text
                })

        return comments

    def parse_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Parse multiple PowerBuilder files

        Args:
            file_paths: List of file paths

        Returns:
            Aggregated results
        """
        all_results = []
        all_tables = set()
        all_sql_queries = []
        all_business_rules = []

        for file_path in file_paths:
            result = self.parse_file(file_path)

            if result["success"]:
                all_results.append(result)
                all_tables.update(result["tables_referenced"])
                all_sql_queries.extend(result["sql_queries"])
                all_business_rules.extend(result["business_rules"])

        return {
            "files_parsed": len(all_results),
            "total_tables": len(all_tables),
            "tables": sorted(list(all_tables)),
            "total_sql_queries": len(all_sql_queries),
            "sql_queries": all_sql_queries,
            "total_business_rules": len(all_business_rules),
            "business_rules": all_business_rules,
            "file_results": all_results
        }

    def generate_knowledge_base(
        self,
        parsed_results: Dict[str, Any],
        database_sid: str,
        schema_name: str
    ) -> List[Dict[str, Any]]:
        """
        Convert parsed results into knowledge base entries for Vector DB

        Args:
            parsed_results: Results from parse_multiple_files
            database_sid: Database SID
            schema_name: Schema name

        Returns:
            List of knowledge entries ready for embedding
        """
        knowledge_entries = []

        # Entry 1: SQL queries
        for i, query in enumerate(parsed_results.get("sql_queries", [])):
            knowledge_entries.append({
                "id": f"{database_sid}_{schema_name}_sql_{i}",
                "type": "sql_query",
                "content": query["sql"],
                "metadata": {
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "query_type": query["type"],
                    "tables": query.get("tables", []),
                    "source": "powerbuilder"
                }
            })

        # Entry 2: Business rules
        for i, rule in enumerate(parsed_results.get("business_rules", [])):
            content = rule.get("text", "")
            if rule.get("condition"):
                content = f"Condition: {rule['condition']}\nAction: {rule.get('action', '')}"

            knowledge_entries.append({
                "id": f"{database_sid}_{schema_name}_rule_{i}",
                "type": "business_rule",
                "content": content,
                "metadata": {
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "rule_type": rule.get("type", "unknown"),
                    "source": "powerbuilder"
                }
            })

        # Entry 3: Table relationships (from SQL analysis)
        table_relationships = self._analyze_table_relationships(
            parsed_results.get("sql_queries", [])
        )

        for i, relationship in enumerate(table_relationships):
            knowledge_entries.append({
                "id": f"{database_sid}_{schema_name}_rel_{i}",
                "type": "table_relationship",
                "content": f"Tables {relationship['table1']} and {relationship['table2']} are related through {relationship['relationship_type']}",
                "metadata": {
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "table1": relationship["table1"],
                    "table2": relationship["table2"],
                    "relationship_type": relationship["relationship_type"],
                    "source": "powerbuilder"
                }
            })

        return knowledge_entries

    def _determine_query_type(self, sql: str) -> str:
        """Determine the type of SQL query"""
        sql_upper = sql.upper()

        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        else:
            return "UNKNOWN"

    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from a SQL query"""
        tables = []
        matches = self.table_pattern.findall(sql)

        for match in matches:
            if match.upper() not in ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'GROUP']:
                tables.append(match.upper())

        return list(set(tables))

    def _analyze_table_relationships(self, sql_queries: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Analyze table relationships from SQL JOINs"""
        relationships = []

        for query in sql_queries:
            sql = query.get("sql", "")

            # Look for JOIN patterns
            join_pattern = re.compile(
                r'FROM\s+([A-Z_][A-Z0-9_]*)\s+.*?JOIN\s+([A-Z_][A-Z0-9_]*)',
                re.IGNORECASE
            )

            matches = join_pattern.findall(sql)
            for table1, table2 in matches:
                relationships.append({
                    "table1": table1.upper(),
                    "table2": table2.upper(),
                    "relationship_type": "JOIN"
                })

        # Remove duplicates
        unique_relationships = []
        seen = set()

        for rel in relationships:
            key = f"{rel['table1']}_{rel['table2']}"
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

        return unique_relationships

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "file_name": "",
            "file_path": "",
            "file_type": "",
            "sql_queries": [],
            "tables_referenced": [],
            "business_rules": [],
            "comments": [],
            "success": False
        }
