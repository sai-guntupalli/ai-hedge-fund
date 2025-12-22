import duckdb
import json
from datetime import datetime
from typing import Any

from src.data.models import FinancialMetrics, Price

class HedgeFundDB:
    def __init__(self, db_path: str = "data/hedge_fund.db"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self.initialize_schema()

    def initialize_schema(self):
        """Create tables if they don't exist."""
        # Analysis Runs
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_run_id START 1;
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_run_id'),
                timestamp TIMESTAMP,
                start_date DATE,
                end_date DATE,
                model_name VARCHAR,
                model_provider VARCHAR,
                tickers VARCHAR[]
            );
        """)

        # Portfolio Decisions
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_decisions (
                run_id INTEGER,
                ticker VARCHAR,
                action VARCHAR,
                quantity DOUBLE,
                confidence DOUBLE,
                reasoning VARCHAR,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            );
        """)

        # Agent Signals
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_signals (
                run_id INTEGER,
                ticker VARCHAR,
                agent_name VARCHAR,
                signal VARCHAR,
                confidence DOUBLE,
                reasoning VARCHAR,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            );
        """)

        # Financial Metrics
        # Storing key columns + full JSON for flexibility
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS financial_metrics (
                run_id INTEGER,
                ticker VARCHAR,
                market_cap DOUBLE,
                pe_ratio DOUBLE,
                pb_ratio DOUBLE,
                ps_ratio DOUBLE,
                revenue_growth DOUBLE,
                earnings_growth DOUBLE,
                roe DOUBLE,
                debt_to_equity DOUBLE,
                current_ratio DOUBLE,
                full_data JSON,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            );
        """)
        
        # Prices (Summary or Raw?)
        # Let's store raw price history used for the run to enable replay/charts
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                run_id INTEGER,
                ticker VARCHAR,
                date DATE,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume BIGINT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
            );
        """)

    def save_analysis_run(self, tickers: list[str], start_date: str, end_date: str, model_name: str, model_provider: str) -> int:
        """Create a new run record and return the ID."""
        timestamp = datetime.now()
        # Insert and get returned id. DuckDB supports RETURNING id
        result = self.conn.execute("""
            INSERT INTO analysis_runs (timestamp, start_date, end_date, model_name, model_provider, tickers)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING id
        """, (timestamp, start_date, end_date, model_name, model_provider, tickers)).fetchone()
        return result[0]

    def save_portfolio_decisions(self, run_id: int, decisions: dict):
        """Save portfolio decisions."""
        for ticker, decision in decisions.items():
            action = decision.get("action", "HOLD")
            quantity = decision.get("quantity", 0)
            confidence = decision.get("confidence", 0)
            reasoning = str(decision.get("reasoning", ""))
            
            self.conn.execute("""
                INSERT INTO portfolio_decisions (run_id, ticker, action, quantity, confidence, reasoning)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (run_id, ticker, action, quantity, confidence, reasoning))

    def save_agent_signals(self, run_id: int, user_signals: dict):
        """Save agent signals."""
        for agent_name, ticker_signals in user_signals.items():
            for ticker, signal_data in ticker_signals.items():
                signal = signal_data.get("signal", "NEUTRAL")
                confidence = signal_data.get("confidence", 0)
                reasoning = str(signal_data.get("reasoning", ""))
                
                self.conn.execute("""
                    INSERT INTO agent_signals (run_id, ticker, agent_name, signal, confidence, reasoning)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (run_id, ticker, agent_name, signal, confidence, reasoning))

    def save_financial_metrics(self, run_id: int, ticker: str, metrics: list[FinancialMetrics]):
        """Save financial metrics."""
        if not metrics:
            return
            
        m = metrics[0] # Current/latest
        
        # safely get attributes
        full_json = m.model_dump_json()
        
        self.conn.execute("""
            INSERT INTO financial_metrics (
                run_id, ticker, market_cap, pe_ratio, pb_ratio, ps_ratio, 
                revenue_growth, earnings_growth, roe, debt_to_equity, current_ratio, full_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, ticker, 
            m.market_cap, m.price_to_earnings_ratio, m.price_to_book_ratio, m.price_to_sales_ratio,
            m.revenue_growth, m.earnings_growth, m.return_on_equity, m.debt_to_equity, m.current_ratio,
            full_json
        ))

    def save_prices(self, run_id: int, ticker: str, prices: list[Price]):
        """Save price history."""
        # This could be large, so we might want to batch insert.
        # Construct list of tuples
        data = []
        for p in prices:
            data.append((run_id, ticker, p.time, p.open, p.high, p.low, p.close, p.volume))
            
        if data:
            self.conn.executemany("""
                INSERT INTO prices (run_id, ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

    def close(self):
        self.conn.close()
