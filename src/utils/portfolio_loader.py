import pandas as pd
import logging

def load_holdings(file_path: str) -> dict:
    """
    Parses a CSV file containing portfolio holdings and returns a dictionary compatible with the AgentState portfolio.

    Expected CSV columns (approximate):
    Symbol, Name, Quantity, Avg. Price, ...

    Returns:
        dict: A dictionary with 'positions' and valid 'tickers' list.
    """
    try:
        # Load CSV
        df = pd.read_csv(file_path)
        
        # Clean column names
        df.columns = [c.strip() for c in df.columns]
        
        required_cols = ['Symbol', 'Quantity', 'Avg. Price']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        positions = {}
        tickers = []

        for _, row in df.iterrows():
            ticker = str(row['Symbol']).strip().upper()
            if not ticker or ticker == 'NAN':
                continue
            
            # Helper to clean numeric strings (remove commas, $, etc)
            def clean_num(val):
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    return float(val.replace(',', '').replace('$', '').replace('%', '').strip())
                return 0.0

            try:
                quantity = clean_num(row['Quantity'])
                avg_price = clean_num(row['Avg. Price'])
            except ValueError:
                logging.warning(f"Skipping invalid data for {ticker}")
                continue

            if quantity > 0:
                positions[ticker] = {
                    "long": quantity,
                    "long_cost_basis": avg_price,
                    "short": 0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0 # Default
                }
                tickers.append(ticker)
            
            # If negative quantity logic is needed later, add here.

        return {
            "positions": positions,
            "tickers": tickers
        }

    except Exception as e:
        raise ValueError(f"Error reading holdings file: {e}")
