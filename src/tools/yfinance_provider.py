import yfinance as yf # type: ignore
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

from src.data.models import (
    Price,
    FinancialMetrics,
    LineItem,
    InsiderTrade,
    CompanyNews,
    CompanyFacts,
    CompanyFactsResponse,
)
from src.tools.provider_interface import DataProvider

class YFinanceProvider(DataProvider):
    def get_prices(
        self, ticker: str, start_date: str, end_date: str, api_key: Optional[str] = None
    ) -> list[Price]:
        # yfinance download
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df.empty:
                return []
            
            prices = []
            for index, row in df.iterrows():
                # Handle multi-index columns if present (common in recent yfinance versions)
                # Usually it's just 'Open', 'High', etc.
                # If ticker is a list it returns MultiIndex, but here it's single.
                # But sometimes it returns (Price, Ticker) column index.
                
                # Check if we need to flatten
                try:
                    open_price = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
                    close_price = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])
                    high_price = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
                    low_price = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
                    volume = int(row['Volume'].iloc[0]) if isinstance(row['Volume'], pd.Series) else int(row['Volume'])
                except (AttributeError, KeyError, ValueError):
                    # Fallback for simple structure
                    open_price = float(row['Open'])
                    close_price = float(row['Close'])
                    high_price = float(row['High'])
                    low_price = float(row['Low'])
                    volume = int(row['Volume'])

                prices.append(
                    Price(
                        open=open_price,
                        close=close_price,
                        high=high_price,
                        low=low_price,
                        volume=volume,
                        time=index.strftime('%Y-%m-%d'),
                    )
                )
            return prices
        except Exception as e:
            print(f"Error fetching prices from yfinance for {ticker}: {e}")
            return []

    def get_financial_metrics(
        self,
        ticker: str,
        end_date: str,
        period: str = "ttm",
        limit: int = 10,
        api_key: Optional[str] = None,
    ) -> list[FinancialMetrics]:
        try:
            stock = yf.Ticker(ticker)
            try:
                info = stock.info
            except Exception:
                # Capture yfinance internal errors (401, etc.)
                return []
            
            if info is None or not isinstance(info, dict):
                return []

            # Determine currency first to ensure dict access is safe
            currency = info.get('currency', 'USD')
            
            # Helper to safely get float/int values
            def safe_get(key):
                val = info.get(key)
                return val if val is not None else None

            metric = FinancialMetrics(
                ticker=ticker,
                report_period=end_date, 
                period=period,
                currency=currency,
                market_cap=safe_get('marketCap'),
                enterprise_value=safe_get('enterpriseValue'),
                price_to_earnings_ratio=safe_get('trailingPE'),
                price_to_book_ratio=safe_get('priceToBook'),
                price_to_sales_ratio=safe_get('priceToSalesTrailing12Months'),
                enterprise_value_to_ebitda_ratio=safe_get('enterpriseToEbitda'),
                enterprise_value_to_revenue_ratio=safe_get('enterpriseToRevenue'),
                free_cash_flow_yield=(safe_get('freeCashflow') / safe_get('marketCap')) if safe_get('freeCashflow') and safe_get('marketCap') else None,
                peg_ratio=safe_get('pegRatio'),
                gross_margin=safe_get('grossMargins'),
                operating_margin=safe_get('operatingMargins'),
                net_margin=safe_get('profitMargins'),
                return_on_equity=safe_get('returnOnEquity'),
                return_on_assets=safe_get('returnOnAssets'),
                return_on_invested_capital=None,
                asset_turnover=None,
                inventory_turnover=None,
                receivables_turnover=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                current_ratio=safe_get('currentRatio'),
                quick_ratio=safe_get('quickRatio'),
                cash_ratio=None,
                operating_cash_flow_ratio=None,
                debt_to_equity=safe_get('debtToEquity'),
                debt_to_assets=None,
                interest_coverage=None,
                revenue_growth=safe_get('revenueGrowth'),
                earnings_growth=safe_get('earningsGrowth'),
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=safe_get('payoutRatio'),
                earnings_per_share=safe_get('trailingEps'),
                book_value_per_share=safe_get('bookValue'),
                free_cash_flow_per_share=None,
            )
            return [metric]
        except Exception:
            # Silence errors for cleaner output when yfinance fails
            return []

    def search_line_items(
        self,
        ticker: str,
        line_items: list[str],
        end_date: str,
        period: str = "ttm",
        limit: int = 10,
        api_key: Optional[str] = None,
    ) -> list[LineItem]:
        # yfinance doesn't define a search API for line items.
        # We can implement a limited version by looking at financials/balance_sheet
        return []

    def get_insider_trades(
        self,
        ticker: str,
        end_date: str,
        start_date: Optional[str] = None,
        limit: int = 1000,
        api_key: Optional[str] = None,
    ) -> list[InsiderTrade]:
        try:
            stock = yf.Ticker(ticker)
            # insider_transactions returns a DataFrame
            # Columns: Shares, Value, Text, Start Date, Ownership, Period, Transaction
            # Note: yfinance insider data structure might vary.
            trades_df = stock.insider_transactions
            
            if trades_df is None or trades_df.empty:
                return []
                
            trades = []
            for index, row in trades_df.iterrows():
                # We need to filter by date if possible.
                # yfinance index is usually the Date or there is a 'Start Date' column?
                # Actually, recently it might be index as number 0,1,2... and 'Start Date' col.
                
                # Check structure
                trade_date_str = None
                if 'Start Date' in row:
                    trade_date = row['Start Date']
                    if isinstance(trade_date, pd.Timestamp):
                        trade_date_str = trade_date.strftime('%Y-%m-%d')
                    else:
                        trade_date_str = str(trade_date)
                
                # Filter by date if simple comparison possible
                if start_date and trade_date_str and trade_date_str < start_date:
                    continue
                if end_date and trade_date_str and trade_date_str > end_date:
                    continue

                trades.append(
                    InsiderTrade(
                        ticker=ticker,
                        issuer=None,
                        name=str(row.get('Insider', 'Unknown')),
                        title=str(row.get('Position', 'Unknown')),
                        is_board_director=None,
                        transaction_date=trade_date_str,
                        transaction_shares=float(row.get('Shares', 0)),
                        transaction_price_per_share=None, # Often not explicitly separate in simple view
                        transaction_value=float(row.get('Value', 0)),
                        shares_owned_before_transaction=None,
                        shares_owned_after_transaction=float(row.get('Shares Owned', 0)) if 'Shares Owned' in row else None,
                        security_title=None,
                        filing_date=trade_date_str or "", # Fallback
                    )
                )
            
            # Sort by date
            trades.sort(key=lambda x: x.transaction_date or "", reverse=True)
            return trades[:limit]

        except Exception as e:
            print(f"Error fetching insider trades from yfinance for {ticker}: {e}")
            return []

    def get_company_news(
        self,
        ticker: str,
        end_date: str,
        start_date: Optional[str] = None,
        limit: int = 1000,
        api_key: Optional[str] = None,
    ) -> list[CompanyNews]:
        try:
            stock = yf.Ticker(ticker)
            news_items = stock.news
            
            if not news_items:
                return []
                
            news_list = []
            for item in news_items:
                # Structure might be nested in 'content' or flat
                content = item.get('content', item)
                
                title = content.get('title', '')
                pub_date = content.get('pubDate', content.get('providerPublishTime', ''))
                
                # Handle date formatting
                date_str = ""
                if isinstance(pub_date, (int, float)):
                    date_str = datetime.fromtimestamp(pub_date).strftime('%Y-%m-%d')
                elif isinstance(pub_date, str):
                    # Try parsing ISO format
                    try:
                        date_str = pub_date.split('T')[0]
                    except:
                        date_str = pub_date
                        
                # Filter dates
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
                
                # Helper for provider
                provider = content.get('provider', {})
                author = provider.get('displayName', 'Unknown') if isinstance(provider, dict) else 'Unknown'
                
                # Helper for URL
                click_through = content.get('clickThroughUrl', {})
                url = click_through.get('url', '') if isinstance(click_through, dict) else content.get('link', '')

                news_list.append(
                    CompanyNews(
                        ticker=ticker,
                        title=title,
                        author=author,
                        source=author,
                        date=date_str,
                        url=url,
                        sentiment=None,
                    )
                )
            
            return news_list[:limit]

        except Exception as e:
            print(f"Error fetching news from yfinance for {ticker}: {e}")
            return []

    def get_market_cap(
        self,
        ticker: str,
        end_date: str,
        api_key: Optional[str] = None,
    ) -> Optional[float]:
        try:
            stock = yf.Ticker(ticker)
            return stock.info.get('marketCap')
        except Exception:
            return None

    def get_company_facts(
        self,
        ticker: str,
        api_key: Optional[str] = None,
    ) -> Optional[CompanyFactsResponse]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Helper to safe get
            def safe_get(key):
                return info.get(key)
                
            return CompanyFactsResponse(
                company_facts=CompanyFacts(
                    ticker=ticker,
                    name=safe_get('longName') or safe_get('shortName') or ticker,
                    market_cap=safe_get('marketCap'),
                    industry=safe_get('industry'),
                    sector=safe_get('sector'),
                    website_url=safe_get('website'),
                    description=safe_get('longBusinessSummary') or safe_get('shortBusinessSummary'),
                )
            )
        except Exception:
            return None
