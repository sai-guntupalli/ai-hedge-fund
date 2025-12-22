from datetime import datetime
import json
from typing import Any

from src.tools.api import (
    get_financial_metrics,
    get_company_news,
    get_insider_trades,
    get_prices,
    get_market_cap,
    get_company_facts,
)
from src.data.models import FinancialMetrics, CompanyNews, InsiderTrade, Price

def _format_financial_metrics(metrics: list[FinancialMetrics]) -> str:
    if not metrics:
        return "No financial metrics available."
    
    # Use the first metric object for current data
    m = metrics[0]
    
    md = "### Financial Metrics\n\n"
    md += "| Metric | Value |\n"
    md += "| :--- | :--- |\n"
    md += f"| Market Cap | ${m.market_cap:,.2f} |\n" if m.market_cap else "| Market Cap | N/A |\n"
    md += f"| P/E Ratio | {m.price_to_earnings_ratio:.2f} |\n" if m.price_to_earnings_ratio else "| P/E Ratio | N/A |\n"
    md += f"| P/B Ratio | {m.price_to_book_ratio:.2f} |\n" if m.price_to_book_ratio else "| P/B Ratio | N/A |\n"
    md += f"| P/S Ratio | {m.price_to_sales_ratio:.2f} |\n" if m.price_to_sales_ratio else "| P/S Ratio | N/A |\n"
    md += f"| Revenue Growth | {m.revenue_growth:.2%} |\n" if m.revenue_growth else "| Revenue Growth | N/A |\n"
    md += f"| Earnings Growth | {m.earnings_growth:.2%} |\n" if m.earnings_growth else "| Earnings Growth | N/A |\n"
    md += f"| ROE | {m.return_on_equity:.2%} |\n" if m.return_on_equity else "| ROE | N/A |\n"
    md += f"| Profit Margin | {m.net_margin:.2%} |\n" if m.net_margin else "| Profit Margin | N/A |\n"
    md += f"| Debt/Equity | {m.debt_to_equity:.2f} |\n" if m.debt_to_equity else "| Debt/Equity | N/A |\n"
    md += f"| Current Ratio | {m.current_ratio:.2f} |\n" if m.current_ratio else "| Current Ratio | N/A |\n"
    
    return md

def _format_news(news: list[CompanyNews]) -> str:
    if not news:
        return "No recent company news."
    
    md = "### Recent News\n\n"
    for item in news[:5]:  # Top 5 news
        md += f"**{item.date}** - [{item.title}]({item.url}) ({item.source})\n\n"
        if item.sentiment:
            md += f"*Sentiment: {item.sentiment}*\n\n"
    
    return md

def _format_insider_trades(trades: list[InsiderTrade]) -> str:
    if not trades:
        return "No recent insider trades."

    md = "### Insider Trades\n\n"
    md += "| Date | Name | Title | Transaction | Shares | Value |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for t in trades[:10]: # Top 10 trades
        trans_type = "Buy" if (t.transaction_shares or 0) > 0 else "Sell" # Simplified assumption if not explicit
        # Better: infer from shares diff or explicit type if available in model (current model implies structure)
        # Assuming transaction_shares is signed or we just list it.
        # Let's just list the signed shares if possible or strict logic
        shares = t.transaction_shares
        val = t.transaction_value
        
        md += f"| {t.transaction_date} | {t.name} | {t.title} | {trans_type} | {shares:,.0f} | ${val:,.0f} |\n"
    
    return md

def _format_prices(prices: list[Price]) -> str:
    if not prices:
        return "No price data available."
        
    md = "### Price History (Recent)\n\n"
    md += "| Date | Open | High | Low | Close | Volume |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    # Show last 10 days
    recent_prices = sorted(prices, key=lambda x: x.time, reverse=True)[:10]
    
    for p in recent_prices:
        md += f"| {p.time} | {p.open:.2f} | {p.high:.2f} | {p.low:.2f} | {p.close:.2f} | {p.volume:,} |\n"
        
    return md

def generate_markdown_report(
    result: dict,
    tickers: list[str],
    start_date: str,
    end_date: str,
    output_file: str
) -> None:
    """
    Generates a Markdown report with analysis results and detailed metrics.
    """
    decisions = result.get("decisions", {})
    analyst_signals = result.get("analyst_signals", {})
    
    md = f"# Hedge Fund Analysis Report\n\n"
    md += f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += f"**Analysis Period:** {start_date} to {end_date}\n\n"
    
    md += "## Portfolio Summary\n\n"
    md += "| Ticker | Action | Quantity | Confidence |\n"
    md += "| :--- | :--- | :--- | :--- |\n"
    
    for ticker, decision in decisions.items():
        action = decision.get("action", "HOLD").upper()
        qty = decision.get("quantity", 0)
        conf = decision.get("confidence", 0)
        md += f"| {ticker} | {action} | {qty} | {conf:.1f}% |\n"
        
    md += "\n---\n"
    
    for ticker in tickers:
        md += f"\n## Analysis for {ticker}\n\n"
        
        # Trading Decision
        decision = decisions.get(ticker, {})
        md += "### Trading Decision\n\n"
        md += f"- **Action:** {decision.get('action', 'N/A').upper()}\n"
        md += f"- **Quantity:** {decision.get('quantity', 0)}\n"
        md += f"- **Confidence:** {decision.get('confidence', 0):.1f}%\n"
        md += f"- **Reasoning:** {decision.get('reasoning', 'N/A')}\n\n"
        
        # Agent Signals
        md += "### Agent Signals\n\n"
        # Structure is analyst_signals[agent_name][ticker]
        for agent, signals in analyst_signals.items():
            if ticker not in signals:
                continue
            
            if agent == "risk_management_agent":
                continue
            
            signal_data = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            sig_type = signal_data.get("signal", "N/A").upper()
            conf = signal_data.get("confidence", 0)
            reason = signal_data.get("reasoning", "")
            
            md += f"#### {agent_name}\n"
            md += f"- **Signal:** {sig_type}\n"
            md += f"- **Confidence:** {conf}%\n"
            md += f"- **Reasoning:** {reason}\n\n"
        
        # Fetch detailed metrics
        # Note: We fetch live/fresh data here to ensure specific details are present
        # even if agents used cached or summarized versions.
        print(f"Fetching detailed metrics for {ticker} report...")
        
        try:
            company_facts = get_company_facts(ticker)
            if company_facts and company_facts.company_facts.description:
                md += "### Company Description\n\n"
                md += f"{company_facts.company_facts.description}\n\n"
        except Exception as e:
            md += f"Error fetching company description: {e}\n\n"

        try:
            metrics = get_financial_metrics(ticker, end_date)
            md += _format_financial_metrics(metrics) + "\n"
        except Exception as e:
            md += f"Error fetching financial metrics: {e}\n"

        try:
            news = get_company_news(ticker, end_date, limit=5)
            md += _format_news(news) + "\n"
        except Exception as e:
            md += f"Error fetching news: {e}\n"
            
        try:
            trades = get_insider_trades(ticker, end_date, limit=10)
            md += _format_insider_trades(trades) + "\n"
        except Exception as e:
            md += f"Error fetching insider trades: {e}\n"

        try:
            prices = get_prices(ticker, start_date, end_date)
            md += _format_prices(prices) + "\n"
        except Exception as e:
            md += f"Error fetching prices: {e}\n"
            
        md += "\n---\n"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\nReport successfully saved to: {output_file}")
    except Exception as e:
        print(f"Error saving report to {output_file}: {e}")
