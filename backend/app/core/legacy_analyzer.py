"""
Legacy Analyzer
Analyzes and stores knowledge extracted from legacy systems (PowerBuilder, etc.)
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class LegacyAnalyzer:
    """Analyzer for legacy system knowledge"""

    def __init__(self, vector_store, embedding_service, powerbuilder_parser):
        """
        Initialize legacy analyzer

        Args:
            vector_store: VectorStore instance
            embedding_service: EmbeddingService instance
            powerbuilder_parser: PowerBuilderParser instance
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.powerbuilder_parser = powerbuilder_parser

    async def process_powerbuilder_files(
        self,
        file_paths: List[str],
        database_sid: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """
        Process PowerBuilder files and store knowledge in Vector DB

        Args:
            file_paths: List of PowerBuilder file paths
            database_sid: Database SID
            schema_name: Schema name

        Returns:
            Processing summary
        """
        logger.info(f"Processing {len(file_paths)} PowerBuilder files...")

        # Parse all files
        parsed_results = self.powerbuilder_parser.parse_multiple_files(file_paths)

        # Generate knowledge base entries
        knowledge_entries = self.powerbuilder_parser.generate_knowledge_base(
            parsed_results,
            database_sid,
            schema_name
        )

        # Store in Vector DB
        stored_count = 0
        sql_query_count = 0
        business_rule_count = 0
        relationship_count = 0

        for entry in knowledge_entries:
            try:
                # Create embedding
                embedding = self.embedding_service.embed_text(entry["content"])

                # Store based on type
                entry_type = entry["type"]

                if entry_type == "sql_query":
                    # Store as business rule (SQL examples)
                    self.vector_store.add_business_rule(
                        rule_id=entry["id"],
                        rule_text=entry["content"],
                        embedding=embedding,
                        metadata=entry["metadata"]
                    )
                    sql_query_count += 1

                elif entry_type == "business_rule":
                    self.vector_store.add_business_rule(
                        rule_id=entry["id"],
                        rule_text=entry["content"],
                        embedding=embedding,
                        metadata=entry["metadata"]
                    )
                    business_rule_count += 1

                elif entry_type == "table_relationship":
                    self.vector_store.add_business_rule(
                        rule_id=entry["id"],
                        rule_text=entry["content"],
                        embedding=embedding,
                        metadata=entry["metadata"]
                    )
                    relationship_count += 1

                stored_count += 1

            except Exception as e:
                logger.error(f"Error storing entry {entry['id']}: {e}")

        summary = {
            "files_processed": parsed_results["files_parsed"],
            "tables_discovered": parsed_results["total_tables"],
            "table_list": parsed_results["tables"],
            "sql_queries_extracted": sql_query_count,
            "business_rules_extracted": business_rule_count,
            "relationships_discovered": relationship_count,
            "total_knowledge_entries": stored_count,
            "success": True
        }

        logger.info(
            f"PowerBuilder processing complete: "
            f"{stored_count} knowledge entries stored "
            f"({sql_query_count} SQL, {business_rule_count} rules, {relationship_count} relationships)"
        )

        return summary

    async def export_knowledge_summary(
        self,
        database_sid: str,
        schema_name: str,
        output_path: str
    ) -> str:
        """
        Export a human-readable summary of extracted knowledge

        Args:
            database_sid: Database SID
            schema_name: Schema name
            output_path: Path to save the summary

        Returns:
            Path to the saved summary file
        """
        # Get all business rules for this database/schema
        # (This requires querying Vector DB, which we'll simulate)

        summary_content = f"""
# PowerBuilder Knowledge Extraction Summary

**Database**: {database_sid}
**Schema**: {schema_name}
**Extracted**: [Timestamp]

## Tables Discovered

[List of tables from parsing]

## SQL Query Patterns

[Common SQL patterns found in PowerBuilder source]

## Business Rules

[Extracted business rules from comments and logic]

## Table Relationships

[JOIN relationships discovered from SQL analysis]

---

This knowledge has been embedded into the Vector DB and will be used to:
1. Improve SQL generation accuracy
2. Understand business logic
3. Recommend related tables
"""

        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)

        logger.info(f"Knowledge summary exported to: {output_file}")
        return str(output_file)

    def analyze_legacy_complexity(
        self,
        parsed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the complexity of the legacy codebase

        Args:
            parsed_results: Results from PowerBuilder parser

        Returns:
            Complexity metrics
        """
        sql_queries = parsed_results.get("sql_queries", [])
        tables = parsed_results.get("tables", [])
        business_rules = parsed_results.get("business_rules", [])

        # Count query types
        query_types = {}
        for query in sql_queries:
            qtype = query.get("type", "UNKNOWN")
            query_types[qtype] = query_types.get(qtype, 0) + 1

        # Calculate average query complexity (number of tables per query)
        query_complexities = []
        for query in sql_queries:
            query_complexities.append(len(query.get("tables", [])))

        avg_complexity = (
            sum(query_complexities) / len(query_complexities)
            if query_complexities else 0
        )

        return {
            "total_files": parsed_results.get("files_parsed", 0),
            "total_tables": len(tables),
            "total_sql_queries": len(sql_queries),
            "query_types": query_types,
            "avg_tables_per_query": round(avg_complexity, 2),
            "total_business_rules": len(business_rules),
            "complexity_score": self._calculate_complexity_score(
                len(tables),
                len(sql_queries),
                avg_complexity
            )
        }

    def _calculate_complexity_score(
        self,
        table_count: int,
        query_count: int,
        avg_tables_per_query: float
    ) -> str:
        """
        Calculate overall complexity score

        Returns:
            "low", "medium", "high", or "very_high"
        """
        score = 0

        # Factor 1: Number of tables
        if table_count > 100:
            score += 3
        elif table_count > 50:
            score += 2
        elif table_count > 20:
            score += 1

        # Factor 2: Number of queries
        if query_count > 500:
            score += 3
        elif query_count > 100:
            score += 2
        elif query_count > 50:
            score += 1

        # Factor 3: Query complexity
        if avg_tables_per_query > 5:
            score += 3
        elif avg_tables_per_query > 3:
            score += 2
        elif avg_tables_per_query > 2:
            score += 1

        if score >= 7:
            return "very_high"
        elif score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"
