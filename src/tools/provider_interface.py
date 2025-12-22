from abc import ABC, abstractmethod
from typing import Optional
from src.data.models import (
    Price,
    FinancialMetrics,
    LineItem,
    InsiderTrade,
    CompanyNews,
    CompanyFactsResponse,
)

class DataProvider(ABC):
    @abstractmethod
    def get_prices(
        self, ticker: str, start_date: str, end_date: str, api_key: Optional[str] = None
    ) -> list[Price]:
        pass

    @abstractmethod
    def get_financial_metrics(
        self,
        ticker: str,
        end_date: str,
        period: str = "ttm",
        limit: int = 10,
        api_key: Optional[str] = None,
    ) -> list[FinancialMetrics]:
        pass

    @abstractmethod
    def search_line_items(
        self,
        ticker: str,
        line_items: list[str],
        end_date: str,
        period: str = "ttm",
        limit: int = 10,
        api_key: Optional[str] = None,
    ) -> list[LineItem]:
        pass

    @abstractmethod
    def get_insider_trades(
        self,
        ticker: str,
        end_date: str,
        start_date: Optional[str] = None,
        limit: int = 1000,
        api_key: Optional[str] = None,
    ) -> list[InsiderTrade]:
        pass

    @abstractmethod
    def get_company_news(
        self,
        ticker: str,
        end_date: str,
        start_date: Optional[str] = None,
        limit: int = 1000,
        api_key: Optional[str] = None,
    ) -> list[CompanyNews]:
        pass

    @abstractmethod
    def get_market_cap(
        self,
        ticker: str,
        end_date: str,
        api_key: Optional[str] = None,
    ) -> Optional[float]:
        pass

    @abstractmethod
    def get_company_facts(
        self,
        ticker: str,
        api_key: Optional[str] = None,
    ) -> Optional[CompanyFactsResponse]:
        pass
