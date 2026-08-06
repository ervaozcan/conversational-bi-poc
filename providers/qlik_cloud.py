from providers.base import BaseDataProvider
import pandas as pd

class QlikCloudProvider(BaseDataProvider):
    def __init__(self, api_key: str, tenant_url: str, appId: str):
        self.api_key = api_key
        self.tenant_url = tenant_url
        self.appId = appId

    def run_query(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("Qlik API key tanımlandığında aktifleşecek.")

    def get_schema(self) -> str:
        pass