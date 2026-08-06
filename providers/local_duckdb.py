import duckdb
import pandas as pd
from providers.base import BaseDataProvider

class LocalDuckDBProvider(BaseDataProvider):
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.conn = duckdb.connect(database=':memory:')
        self.conn.execute(f"CREATE TABLE sales AS SELECT * FROM read_csv_auto('{csv_path}')")

    def run_query(self, sql_query: str) -> pd.DataFrame:
        return self.conn.execute(sql_query).df()

    def get_schema(self) -> str:
        schema_info = self.conn.execute("DESCRIBE sales").fetchall()
        schema_str = "Tablo Adı: sales\nSütunlar:\n"
        for col in schema_info:
            schema_str += f"- {col[0]} ({col[1]})\n"
        return schema_str
