import os
import pandas as pd
from functools import lru_cache

from src.data.models import (
    CompanyNews,
    FinancialMetrics,
    Price,
    LineItem,
    InsiderTrade,
    CompanyFactsResponse,
)
from src.tools.provider_interface import DataProvider
from src.tools.financial_datasets import FinancialDatasetsProvider
from src.tools.yfinance_provider import YFinanceProvider

@lru_cache()
def get_provider() -> DataProvider:
    provider_name = os.environ.get("DATA_PROVIDER", "financialdatasets")
    print(f"Using data provider: {provider_name}")
    if provider_name.lower() == "yfinance":
        return YFinanceProvider()
    return FinancialDatasetsProvider()

def get_prices(ticker: str, start_date: str, end_date: str, api_key: str = None) -> list[Price]:
    return get_provider().get_prices(ticker, start_date, end_date, api_key=api_key)

def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str = None,
) -> list[FinancialMetrics]:
    return get_provider().get_financial_metrics(ticker, end_date, period, limit, api_key)

def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str = None,
) -> list[LineItem]:
    return get_provider().search_line_items(ticker, line_items, end_date, period, limit, api_key)

def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str = None,
) -> list[InsiderTrade]:
    return get_provider().get_insider_trades(ticker, end_date, start_date, limit, api_key)

def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str = None,
) -> list[CompanyNews]:
    return get_provider().get_company_news(ticker, end_date, start_date, limit, api_key)

def get_market_cap(
    ticker: str,
    end_date: str,
    api_key: str = None,
) -> float | None:
    return get_provider().get_market_cap(ticker, end_date, api_key)

def get_company_facts(
    ticker: str,
    api_key: str = None,
) -> CompanyFactsResponse | None:
    return get_provider().get_company_facts(ticker, api_key)

def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df

def get_price_data(ticker: str, start_date: str, end_date: str, api_key: str = None) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date, api_key=api_key)
    return prices_to_df(prices)
