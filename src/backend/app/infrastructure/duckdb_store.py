"""DuckDB integration — fast analytics on local files and in-memory data.

DuckDB excels at:
- Analytical queries over CSV/Parquet/JSON files directly (no import needed)
- In-memory OLAP on ingested data
- Fast aggregations, joins, window functions
- Exporting query results to Parquet/CSV

Usage:
    store = DuckDBStore()
    results = store.query("SELECT * FROM read_csv('resources/data/sales.csv') LIMIT 10")
    store.query("CREATE TABLE insights AS SELECT ... FROM read_parquet('data/*.parquet')")
    store.close()
"""

import duckdb

from app.config import settings


class DuckDBStore:
    """Lightweight analytics store backed by DuckDB."""

    def __init__(self, path: str | None = None):
        self.path = path or settings.duckdb_path
        self.conn = duckdb.connect(self.path)

    def query(self, sql: str, params: list | None = None) -> list[dict]:
        """Execute a SQL query and return results as dicts."""
        result = self.conn.execute(sql, params or [])
        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def query_df(self, sql: str, params: list | None = None):
        """Execute a SQL query and return a Polars/Pandas DataFrame."""
        return self.conn.execute(sql, params or []).fetchdf()

    def ingest_csv(self, table_name: str, file_path: str) -> int:
        """Ingest a CSV file into a DuckDB table."""
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv('{file_path}')")
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0

    def ingest_json(self, table_name: str, file_path: str) -> int:
        """Ingest a JSON file into a DuckDB table."""
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json('{file_path}')")
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0

    def ingest_parquet(self, table_name: str, file_path: str) -> int:
        """Ingest Parquet file(s) into a DuckDB table. Supports globs."""
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')")
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0

    def export_parquet(self, table_or_query: str, output_path: str) -> None:
        """Export table or query results to Parquet."""
        if table_or_query.strip().upper().startswith("SELECT"):
            self.conn.execute(f"COPY ({table_or_query}) TO '{output_path}' (FORMAT PARQUET)")
        else:
            self.conn.execute(f"COPY {table_or_query} TO '{output_path}' (FORMAT PARQUET)")

    def close(self):
        self.conn.close()
