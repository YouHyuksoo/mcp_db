"""
Metadata Migrator
Migrates existing JSON metadata files to ChromaDB Vector Store
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class MetadataMigrator:
    """Migrate JSON metadata to Vector DB"""

    def __init__(self, vector_store, embedding_service):
        """
        Initialize migrator

        Args:
            vector_store: VectorStore instance
            embedding_service: EmbeddingService instance
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    async def migrate_from_json(
        self,
        metadata_dir: str,
        database_sid: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """
        Migrate metadata from JSON files to Vector DB

        Args:
            metadata_dir: Directory containing JSON metadata files
            database_sid: Database SID
            schema_name: Schema name

        Returns:
            Migration summary
        """
        metadata_path = Path(metadata_dir) / database_sid / schema_name

        if not metadata_path.exists():
            logger.warning(f"Metadata path does not exist: {metadata_path}")
            return {
                "success": False,
                "error": "Metadata directory not found",
                "tables_migrated": 0
            }

        # Find all JSON files
        json_files = list(metadata_path.glob("*.json"))

        if not json_files:
            logger.warning(f"No JSON files found in: {metadata_path}")
            return {
                "success": False,
                "error": "No JSON metadata files found",
                "tables_migrated": 0
            }

        logger.info(f"Found {len(json_files)} JSON metadata files")

        # Prepare batch data
        table_ids = []
        summary_texts = []
        embeddings = []
        metadatas = []

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Create table ID
                table_name = metadata.get("table_name", json_file.stem)
                table_id = f"{database_sid}.{schema_name}.{table_name}"

                # Create summary text for embedding
                summary_text = self._create_table_summary(metadata)

                # Create embedding
                embedding = self.embedding_service.embed_text(summary_text)

                # Prepare metadata
                table_metadata = {
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "korean_name": metadata.get("korean_name", ""),
                    "description": metadata.get("description", ""),
                    "column_count": len(metadata.get("columns", [])),
                    "has_primary_key": bool(metadata.get("primary_key")),
                    "has_foreign_keys": bool(metadata.get("foreign_keys")),
                }

                table_ids.append(table_id)
                summary_texts.append(summary_text)
                embeddings.append(embedding)
                metadatas.append(table_metadata)

                logger.debug(f"Prepared: {table_id}")

            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")
                continue

        # Batch add to Vector DB
        if table_ids:
            try:
                self.vector_store.add_metadata_batch(
                    table_ids=table_ids,
                    summary_texts=summary_texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                logger.info(f"✓ Migrated {len(table_ids)} tables to Vector DB")

                return {
                    "success": True,
                    "tables_migrated": len(table_ids),
                    "database_sid": database_sid,
                    "schema_name": schema_name
                }

            except Exception as e:
                logger.error(f"Error during batch migration: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tables_migrated": 0
                }
        else:
            return {
                "success": False,
                "error": "No valid metadata to migrate",
                "tables_migrated": 0
            }

    def _create_table_summary(self, metadata: Dict[str, Any]) -> str:
        """
        Create a rich text summary for embedding

        Args:
            metadata: Table metadata dict

        Returns:
            Summary text
        """
        parts = []

        # Table name
        table_name = metadata.get("table_name", "")
        parts.append(f"Table: {table_name}")

        # Korean name
        korean_name = metadata.get("korean_name", "")
        if korean_name:
            parts.append(f"Korean Name: {korean_name}")

        # Description
        description = metadata.get("description", "")
        if description:
            parts.append(f"Description: {description}")

        # Column information
        columns = metadata.get("columns", [])
        if columns:
            # Create column summaries (limit to top 15 for embedding efficiency)
            column_summaries = []
            for col in columns[:15]:
                col_name = col.get("column_name", "")
                col_korean = col.get("korean_name", "")
                col_desc = col.get("description", "")

                if col_korean or col_desc:
                    col_text = f"{col_name}"
                    if col_korean:
                        col_text += f" ({col_korean})"
                    if col_desc:
                        col_text += f": {col_desc}"
                    column_summaries.append(col_text)
                else:
                    column_summaries.append(col_name)

            parts.append("Columns: " + ", ".join(column_summaries))

        # Primary key
        primary_key = metadata.get("primary_key", [])
        if primary_key:
            parts.append(f"Primary Key: {', '.join(primary_key)}")

        # Foreign keys
        foreign_keys = metadata.get("foreign_keys", [])
        if foreign_keys:
            fk_texts = []
            for fk in foreign_keys[:5]:  # Limit to 5 FKs
                ref_table = fk.get("referenced_table", "")
                fk_texts.append(f"References {ref_table}")
            parts.append("Foreign Keys: " + ", ".join(fk_texts))

        return "\n".join(parts)

    async def migrate_all_databases(
        self,
        metadata_root_dir: str
    ) -> Dict[str, Any]:
        """
        Migrate all databases and schemas from metadata directory

        Args:
            metadata_root_dir: Root metadata directory

        Returns:
            Overall migration summary
        """
        metadata_root = Path(metadata_root_dir)

        if not metadata_root.exists():
            logger.error(f"Metadata root directory does not exist: {metadata_root}")
            return {
                "success": False,
                "error": "Metadata root directory not found"
            }

        total_migrated = 0
        database_results = []

        # Find all database directories
        for db_dir in metadata_root.iterdir():
            if not db_dir.is_dir():
                continue

            database_sid = db_dir.name

            # Find all schema directories
            for schema_dir in db_dir.iterdir():
                if not schema_dir.is_dir():
                    continue

                schema_name = schema_dir.name

                logger.info(f"Migrating {database_sid}.{schema_name}...")

                result = await self.migrate_from_json(
                    metadata_root_dir,
                    database_sid,
                    schema_name
                )

                if result["success"]:
                    total_migrated += result["tables_migrated"]
                    database_results.append({
                        "database_sid": database_sid,
                        "schema_name": schema_name,
                        "tables_migrated": result["tables_migrated"]
                    })

        return {
            "success": True,
            "total_tables_migrated": total_migrated,
            "databases_processed": len(database_results),
            "details": database_results
        }
