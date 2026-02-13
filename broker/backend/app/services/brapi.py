import httpx
from datetime import datetime, timedelta
from ..config import settings


class BrapiService:
    """Service to fetch data from brapi.dev API"""

    def __init__(self):
        self.base_url = settings.brapi_base_url

    async def get_quote(self, symbol: str) -> dict:
        """Get current quote for a symbol"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/quote/{symbol}",
                params={"token": "demo"}
            )
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                return data["results"][0]
            return {}

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Get quotes for multiple symbols"""
        symbols_str = ",".join(symbols)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/quote/{symbols_str}",
                params={"token": "demo"}
            )
            data = response.json()
            return data.get("results", [])

    async def get_historical_data(self, symbol: str, range_days: int = 365) -> list[dict]:
        """Get historical price data for a symbol"""
        # Calculate date range (last N days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=range_days)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/quote/{symbol}",
                params={
                    "range": "1y",
                    "interval": "1d",
                    "token": "demo"
                }
            )
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                historical = result.get("historicalDataPrice", [])
                return historical

            return []


brapi_service = BrapiService()
