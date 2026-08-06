from abc import ABC, abstractmethod
import pandas as pd

class BaseDataProvider(ABC):
    @abstractmethod
    def run_query(self, query: str) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def get_schema(self) -> str:
        pass