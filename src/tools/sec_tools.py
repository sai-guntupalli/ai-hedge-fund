import yfinance as yf
import re
import requests
from bs4 import BeautifulSoup
import os
from typing import Optional, Dict
from datetime import datetime
from typing import Optional, Dict
from datetime import datetime

def get_latest_10k_url(ticker_symbol: str) -> str | None:
    """
    Retrieves the URL of the latest 10-K filing for a given ticker using yfinance.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Access sec_filings
        # Note: yfinance structure for sec_filings can be a list of dicts
        # [{'date': ..., 'type': '10-K', 'edgarUrl': ..., 'exhibits': ...}, ...]
        if not hasattr(ticker, 'sec_filings'):
            print(f"No SEC filings found for {ticker_symbol} in yfinance.")
            return None
            
        filings = ticker.sec_filings
        if not filings:
            print(f"Empty SEC filings list for {ticker_symbol}.")
            return None
            
        # Filter for 10-K
        ten_ks = [f for f in filings if f.get('type') == '10-K']
        
        if not ten_ks:
            print(f"No 10-K filings found for {ticker_symbol}.")
            return None
            
        # Sort by date descending (though usually already sorted)
        # Dates are typically datetime.date objects or strings.
        # Let's assume they are comparable or sorted by yfinance.
        # Assuming list is sorted desc by default, take the first one.
        latest_10k = ten_ks[0]
        
        return latest_10k.get('edgarUrl')
        
    except Exception as e:
        print(f"Error fetching 10-K URL for {ticker_symbol}: {e}")
        return None


def get_latest_10k_text(ticker_symbol: str) -> str | None:
    """
    Combined function to get URL, download/load text, and save to disk.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        if not hasattr(ticker, 'sec_filings'):
            print(f"No SEC filings found for {ticker_symbol}")
            return None
        filings = ticker.sec_filings
        ten_ks = [f for f in filings if f.get('type') == '10-K']
        if not ten_ks:
            print(f"No 10-K found for {ticker_symbol}")
            return None
            
        latest = ten_ks[0]
        filing_date = latest.get('date')
        # Simple date string conversion is robust enough usually
        date_str = str(filing_date)
        
        # Try to get direct 10-K HTML link
        exhibits = latest.get('exhibits', {})
        url = exhibits.get('10-K') or exhibits.get('FORM 10-K') or latest.get('edgarUrl')
        
        if not url:
            return None
            
        # Define file path
        # Ensure directory exists
        data_dir = os.path.join(os.getcwd(), "data", "10k")
        os.makedirs(data_dir, exist_ok=True)
        
        filename = f"{ticker_symbol}_10k_{date_str}.html"
        file_path = os.path.join(data_dir, filename)
        
        html_content = ""
        
        if os.path.exists(file_path):
            print(f"Loading 10-K from local file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            print(f"Downloading 10-K from: {url}")
            html_content = download_10k_html(url)
            if html_content:
                print(f"Saving 10-K to {file_path}")
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                except Exception as e:
                    print(f"Error saving file: {e}")
        
        if not html_content:
            return None
            
        return clean_text(html_content)
        
    except Exception as e:
        print(f"Error fetching 10-K for {ticker_symbol}: {e}")
        return None

def download_10k_html(url: str) -> str | None:
    """Downloads the raw HTML content from the URL."""
    if not url:
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept-Encoding": "gzip, deflate",
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to download 10-K: Status {response.status_code}")
            return None
        return response.text
    except Exception as e:
        print(f"Error downloading 10-K html: {e}")
        return None

def clean_text(html_content: str) -> str:
    """
    Parses HTML and returns clean text.
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
    except:
        soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
        
    text = soup.get_text(separator='\n', strip=True)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_sections(text: str) -> Dict[str, str]:
    """
    Extracts key sections from the 10-K text using Regex.
    Keys: 'Business', 'Risk Factors', 'MD&A', 'Financial Statements'
    """
    sections = {}
    
    # Patterns for Standard 10-K Items
    # We look for "Item X." followed by the title, with some flexibility
    # Patterns for Standard 10-K Items
    # We look for "Item X." followed by the title, with some flexibility
    # Note: Sometimes they are "Item 8. Financial Statements" or just "Item 8."
    patterns = {
        "Business": r"(?i)(?:Item\s+1\.?|Item\s+1\s*:)\s*Business\b",
        "Risk Factors": r"(?i)(?:Item\s+1A\.?|Item\s+1A\s*:)\s*Risk\s+Factors\b",
        "Properties": r"(?i)(?:Item\s+2\.?|Item\s+2\s*:)\s*Properties\b",
        "Legal Proceedings": r"(?i)(?:Item\s+3\.?|Item\s+3\s*:)\s*Legal\s+Proceedings\b",
        "MD&A": r"(?i)(?:Item\s+7\.?|Item\s+7\s*:)\s*Management.?s\s+Discussion\b",
        "Financial Statements": r"(?i)(?:Item\s+8\.?|Item\s+8\s*:|Financial\s+Statements\s+and\s+Supplementary\s+Data)\s*(?:Financial\s+Statements\b)?",
        "Controls": r"(?i)(?:Item\s+9A\.?|Item\s+9A\s*:)\s*Controls\s+and\s+Procedures\b",
    }
    
    # Find start indices
    positions = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            positions[key] = match.start()
        else:
            positions[key] = -1
            
    # We want Business, Risk Factors, MD&A, Financial Statements
    # Logic: Content for 'Business' is between 'Business' start and 'Risk Factors' start (or Properties)
    
    sorted_items = sorted([(k, p) for k, p in positions.items() if p != -1], key=lambda x: x[1])
    
    for i in range(len(sorted_items)):
        key, start_pos = sorted_items[i]
        
        # Determine end position
        if i < len(sorted_items) - 1:
            end_pos = sorted_items[i+1][1]
        else:
            # Last item, take chunk
            end_pos = start_pos + 50000 
            
        # Extract
        content = text[start_pos:end_pos].strip()
        
        # Clean up the header itself
        # (Optional, but good to save tokens)
        
        if len(content) > 20000:
             # Truncate strictly per section to avoid token blowout
             content = content[:20000] + "\n...[Truncated]..."
             
        sections[key] = content
        
    return sections
