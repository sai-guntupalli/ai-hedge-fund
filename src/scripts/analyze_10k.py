
import argparse
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.tools.sec_tools import get_latest_10k_text
from src.agents.fundamental_analysis import analyze_10k

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Analyze the latest 10-K report for a given ticker.")
    parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("--model", type=str, default="gpt-4o", help="LLM model to use (default: gpt-4o)")
    parser.add_argument("--output", type=str, help="Optional output file to save the report")
    
    args = parser.parse_args()
    
    print(f"--- Starting 10-K Analysis for {args.ticker} ---")
    
    # 1. Fetch Text
    print("Fetching latest 10-K report...")
    text = get_latest_10k_text(args.ticker)
    
    if not text:
        print("Failed to fetch 10-K text. Exiting.")
        sys.exit(1)
        
    print(f"Successfully fetched 10-K text ({len(text)} characters).")
    
    # 2. Analyze
    print(f"Analyzing with {args.model}...")
    analysis = analyze_10k(text, args.ticker, args.model)
    
    # 3. Output
    print("\n" + "="*50)
    print(analysis)
    print("="*50 + "\n")
    
    output_path = args.output
    if not output_path:
        # Default output directory
        output_dir = os.path.join(os.getcwd(), "outputs", "10k_reports")
        os.makedirs(output_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(output_dir, f"{args.ticker}_10k_analysis_{date_str}.md")

    try:
        with open(output_path, "w") as f:
            f.write(analysis)
        print(f"Report saved to {output_path}")
    except Exception as e:
        print(f"Error saving report: {e}")

if __name__ == "__main__":
    main()
