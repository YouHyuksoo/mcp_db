"""
Enhanced Metadata Builder
Creates rich, structured metadata for Vector DB embedding
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedMetadataBuilder:
    """Build enhanced metadata structure for Vector DB"""

    @staticmethod
    def create_summary_text(
        database_sid: str,
        schema_name: str,
        table_name: str,
        korean_name: Optional[str] = None,
        description: Optional[str] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        business_rules: Optional[List[Dict[str, Any]]] = None,
        related_tables: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Create rich summary text for embedding

        ★ 핵심: database_sid와 schema_name을 텍스트에 포함하여
                 의미 검색에서도 DB/Schema 구분 가능

        Args:
            database_sid: Database SID (필수)
            schema_name: Schema name (필수)
            table_name: Table name
            korean_name: Korean table name
            description: Table description
            columns: Column information
            business_rules: Business rules
            related_tables: Related table information

        Returns:
            Rich summary text for embedding
        """
        parts = []

        # Header with DB and Schema (중요!)
        header = f"[{database_sid}.{schema_name}] {table_name}"
        if korean_name:
            header += f" ({korean_name})"
        parts.append(header)
        parts.append("")  # Empty line

        # Description
        if description:
            parts.append(f"설명: {description}")
            parts.append("")

        # Key columns (limit to 10 most important)
        if columns:
            parts.append("핵심 컬럼:")
            key_columns = [col for col in columns if col.get("is_key") or col.get("is_important")][:10]
            if not key_columns:
                key_columns = columns[:10]  # Take first 10 if no key columns marked

            for col in key_columns:
                col_name = col.get("name", col.get("column_name", ""))
                col_korean = col.get("korean_name", "")
                col_desc = col.get("description", "")
                col_type = col.get("data_type", "")

                col_text = f"- {col_name}"
                if col_korean:
                    col_text += f" ({col_korean})"
                if col_desc:
                    col_text += f": {col_desc}"
                elif col_type:
                    col_text += f" [{col_type}]"

                parts.append(col_text)
            parts.append("")

        # Business rules
        if business_rules:
            parts.append("비즈니스 로직:")
            for rule in business_rules[:5]:  # Limit to 5 rules
                rule_text = rule.get("description", rule.get("rule", ""))
                if rule_text:
                    parts.append(f"- {rule_text}")
            parts.append("")

        # Related tables
        if related_tables:
            parts.append("연관 테이블:")
            for rel in related_tables[:5]:  # Limit to 5 related tables
                rel_table = rel.get("table_name", "")
                rel_korean = rel.get("korean_name", "")
                rel_desc = rel.get("description", "")

                rel_text = f"- {rel_table}"
                if rel_korean:
                    rel_text += f" ({rel_korean})"
                if rel_desc:
                    rel_text += f": {rel_desc}"

                parts.append(rel_text)

        return "\n".join(parts)

    @staticmethod
    def create_metadata_dict(
        database_sid: str,
        schema_name: str,
        table_name: str,
        korean_name: Optional[str] = None,
        description: Optional[str] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        related_tables: Optional[List[Dict[str, Any]]] = None,
        business_rules: Optional[List[Dict[str, Any]]] = None,
        indexes: Optional[List[Dict[str, Any]]] = None,
        sample_values: Optional[Dict[str, List[str]]] = None,
        row_count: Optional[int] = None,
        **extra_fields
    ) -> Dict[str, Any]:
        """
        Create structured metadata dictionary

        ★ 핵심: database_sid와 schema_name은 필수 필드

        Args:
            database_sid: Database SID (필수)
            schema_name: Schema name (필수)
            table_name: Table name
            korean_name: Korean table name
            description: Table description
            columns: List of column dicts with enhanced info
            related_tables: Related table information
            business_rules: Business rules
            indexes: Index information
            sample_values: Sample data values
            row_count: Estimated row count
            **extra_fields: Additional custom fields

        Returns:
            Metadata dictionary for ChromaDB
        """
        metadata = {
            # ★ 필수 필터 조건
            "database_sid": database_sid,
            "schema_name": schema_name,
            "table_name": table_name,

            # 기본 정보
            "korean_name": korean_name or "",
            "description": description or "",
            "column_count": len(columns) if columns else 0,
        }

        # 핵심 컬럼 (JSON string으로 저장)
        if columns:
            import json
            # Store up to 10 key columns
            key_columns = []
            for col in columns[:10]:
                key_col = {
                    "name": col.get("name", col.get("column_name", "")),
                    "korean_name": col.get("korean_name", ""),
                    "data_type": col.get("data_type", ""),
                    "nullable": col.get("nullable", True),
                    "is_pk": col.get("is_pk", False),
                    "description": col.get("description", "")
                }

                # Add code values if present
                code_values = col.get("code_values", col.get("codes"))
                if code_values:
                    key_col["code_values"] = code_values

                key_columns.append(key_col)

            metadata["key_columns"] = json.dumps(key_columns, ensure_ascii=False)

        # 관계 정보
        if related_tables:
            import json
            rel_tables = []
            for rel in related_tables[:10]:
                rel_tables.append({
                    "table_name": rel.get("table_name", ""),
                    "korean_name": rel.get("korean_name", ""),
                    "relationship_type": rel.get("relationship_type", rel.get("type", "")),
                    "foreign_key": rel.get("foreign_key", ""),
                    "description": rel.get("description", "")
                })
            metadata["related_tables"] = json.dumps(rel_tables, ensure_ascii=False)

        # 비즈니스 규칙
        if business_rules:
            import json
            rules = []
            for rule in business_rules[:10]:
                if isinstance(rule, str):
                    rules.append({"rule": rule})
                elif isinstance(rule, dict):
                    rules.append({
                        "rule": rule.get("rule", ""),
                        "description": rule.get("description", "")
                    })
            metadata["business_rules"] = json.dumps(rules, ensure_ascii=False)

        # 인덱스 정보
        if indexes:
            import json
            idx_list = []
            for idx in indexes[:10]:
                idx_list.append({
                    "name": idx.get("name", ""),
                    "type": idx.get("type", ""),
                    "columns": idx.get("columns", [])
                })
            metadata["indexes"] = json.dumps(idx_list, ensure_ascii=False)

        # 샘플 값
        if sample_values:
            import json
            metadata["sample_values"] = json.dumps(sample_values, ensure_ascii=False)

        # 메타 정보
        if row_count is not None:
            metadata["row_count_estimate"] = row_count

        # PK/FK 존재 여부 (빠른 필터링용)
        if columns:
            metadata["has_primary_key"] = any(col.get("is_pk") for col in columns)
            metadata["has_foreign_keys"] = len(related_tables) > 0 if related_tables else False

        # 추가 필드
        metadata.update(extra_fields)

        # Timestamp
        from datetime import datetime
        metadata["updated_at"] = datetime.now().isoformat()

        return metadata

    @staticmethod
    def parse_csv_row(
        row: Dict[str, str],
        database_sid: str,
        schema_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse CSV row to enhanced metadata format

        Expected CSV columns:
        - table_name (required)
        - korean_name
        - description
        - column_name
        - column_korean_name
        - column_description
        - column_type
        - is_pk (Y/N)
        - code_values (comma-separated)
        - related_table
        - relationship_type
        - business_rule

        Args:
            row: CSV row dict
            database_sid: Database SID
            schema_name: Schema name

        Returns:
            Parsed metadata or None if invalid
        """
        table_name = row.get("table_name", "").strip()
        if not table_name:
            return None

        # Column info
        column_info = None
        if row.get("column_name"):
            column_info = {
                "name": row.get("column_name", "").strip(),
                "korean_name": row.get("column_korean_name", "").strip(),
                "description": row.get("column_description", "").strip(),
                "data_type": row.get("column_type", "").strip(),
                "is_pk": row.get("is_pk", "").upper() == "Y",
                "nullable": row.get("nullable", "Y").upper() == "Y"
            }

            # Parse code values
            code_values_str = row.get("code_values", "").strip()
            if code_values_str:
                column_info["code_values"] = [v.strip() for v in code_values_str.split(",")]

        # Related table info
        related_table = None
        if row.get("related_table"):
            related_table = {
                "table_name": row.get("related_table", "").strip(),
                "korean_name": row.get("related_table_korean", "").strip(),
                "relationship_type": row.get("relationship_type", "1:N").strip(),
                "foreign_key": row.get("foreign_key", "").strip(),
                "description": row.get("relationship_description", "").strip()
            }

        # Business rule
        business_rule = None
        if row.get("business_rule"):
            business_rule = {
                "rule": row.get("business_rule", "").strip(),
                "description": row.get("business_rule_description", "").strip()
            }

        return {
            "database_sid": database_sid,
            "schema_name": schema_name,
            "table_name": table_name,
            "korean_name": row.get("korean_name", "").strip(),
            "description": row.get("description", "").strip(),
            "column": column_info,
            "related_table": related_table,
            "business_rule": business_rule
        }

    @staticmethod
    def aggregate_table_data(parsed_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate multiple CSV rows per table

        Args:
            parsed_rows: List of parsed CSV rows

        Returns:
            Dict of {table_id: aggregated_data}
        """
        tables = {}

        for row in parsed_rows:
            database_sid = row["database_sid"]
            schema_name = row["schema_name"]
            table_name = row["table_name"]
            table_id = f"{database_sid}.{schema_name}.{table_name}"

            # Initialize table entry
            if table_id not in tables:
                tables[table_id] = {
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "korean_name": row.get("korean_name", ""),
                    "description": row.get("description", ""),
                    "columns": [],
                    "related_tables": [],
                    "business_rules": []
                }

            # Aggregate columns
            if row.get("column"):
                # Check if column already exists
                col_name = row["column"]["name"]
                if not any(c["name"] == col_name for c in tables[table_id]["columns"]):
                    tables[table_id]["columns"].append(row["column"])

            # Aggregate related tables
            if row.get("related_table"):
                rel_table = row["related_table"]["table_name"]
                if not any(r["table_name"] == rel_table for r in tables[table_id]["related_tables"]):
                    tables[table_id]["related_tables"].append(row["related_table"])

            # Aggregate business rules
            if row.get("business_rule"):
                rule = row["business_rule"]["rule"]
                if not any(r["rule"] == rule for r in tables[table_id]["business_rules"]):
                    tables[table_id]["business_rules"].append(row["business_rule"])

        return tables
