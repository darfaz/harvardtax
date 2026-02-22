from datetime import datetime
import httpx
from app.config import settings

QBO_BASE_URL = {
    "sandbox": "https://sandbox-quickbooks.api.intuit.com",
    "production": "https://quickbooks.api.intuit.com",
}


class QBOClient:
    def __init__(self, access_token: str, realm_id: str):
        self.access_token = access_token
        self.realm_id = realm_id
        self.base_url = f"{QBO_BASE_URL[settings.qbo_environment]}/v3/company/{realm_id}"

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_company_info(self) -> dict:
        data = await self._get(f"companyinfo/{self.realm_id}")
        return data["CompanyInfo"]

    async def get_chart_of_accounts(self) -> list[dict]:
        data = await self._get("query", params={
            "query": "SELECT * FROM Account WHERE Active = true MAXRESULTS 1000"
        })
        return data.get("QueryResponse", {}).get("Account", [])

    async def get_profit_and_loss(self, start_date: str, end_date: str) -> dict:
        data = await self._get("reports/ProfitAndLoss", params={
            "start_date": start_date,
            "end_date": end_date,
            "accounting_method": "Accrual",
        })
        return data

    async def get_balance_sheet(self, as_of_date: str) -> dict:
        data = await self._get("reports/BalanceSheet", params={
            "date_macro": "",
            "as_of_date": as_of_date,
        })
        return data

    async def get_trial_balance(self, start_date: str, end_date: str) -> dict:
        data = await self._get("reports/TrialBalance", params={
            "start_date": start_date,
            "end_date": end_date,
        })
        return data
