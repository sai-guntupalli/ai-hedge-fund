# AI Hedge Fund

This is a proof of concept for an AI-powered hedge fund. The goal of this project is to explore the use of AI to make trading decisions. This project is for **educational** purposes only and is not intended for real trading or investment.

This system employs several agents working together:

1.  **Valuation Agent** - Calculates the intrinsic value of a stock and generates trading signals.
2.  **Sentiment Agent** - Analyzes market sentiment and generates trading signals.
3.  **Fundamentals Agent** - Analyzes fundamental data and generates trading signals.
4.  **Technicals Agent** - Analyzes technical indicators and generates trading signals.
5.  **Guru Agents** - Mimics the strategies of legendary investors:
    *   Aswath Damodaran, Ben Graham, Bill Ackman, Cathie Wood, Charlie Munger, Michael Burry, Mohnish Pabrai, Peter Lynch, Phil Fisher, Rakesh Jhunjhunwala, Stanley Druckenmiller, Warren Buffett.
6.  **Risk Manager** - Calculates risk metrics and sets position limits.
7.  **Portfolio Manager** - Makes final trading decisions and generates orders.

<img width="1042" alt="Screenshot 2025-03-22 at 6 19 07 PM" src="https://github.com/user-attachments/assets/cbae3dcf-b571-490d-b0ad-3f0f035ac0d4" />

## Disclaimer

This project is for **educational and research purposes only**.

-   Not intended for real trading or investment
-   No investment advice or guarantees provided
-   Creator assumes no liability for financial losses
-   Consult a financial advisor for investment decisions
-   Past performance does not indicate future results

By using this software, you agree to use it solely for learning purposes.

## Table of Contents

-   [Features](#features)
-   [Installation](#installation)
-   [Usage](#usage)
    -   [Hedge Fund Simulation](#1-hedge-fund-simulation)
    -   [10-K Report Analysis](#2-10-k-report-analysis)
    -   [Backtesting](#3-backtesting)
-   [Data Providers](#data-providers)
-   [Project Structure](#project-structure)
-   [Contributing](#how-to-contribute)
-   [License](#license)

## Features

*   **Multi-Agent Architecture**: Uses LangGraph to coordinate multiple specialized AI agents.
*   **Fundamental & Technical Analysis**: Combines quantitative metrics with technical indicators.
*   **Sentiment Analysis**: Incorporates news and insider trading signals.
*   **10-K Report Analysis**: Automatically downloads and analyzes SEC 10-K filings using LLMs to extract strategic insights and financial metrics.
*   **Portfolio Management**: Optimizes portfolio allocations based on risk constraints.
*   **Data Persistence**:  Results, signals, and market data are automatically saved to a local **DuckDB** database (`hedge_fund.db`) for future analysis.
*   **Reporting**: Generates detailed Markdown reports with analysis justification.

## Installation

This project uses [`uv`](https://github.com/astral-sh/uv) limit dependency management.

### 1. Clone the Repository

```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

### 2. Install Dependencies

Ensure you have `uv` installed. If not:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then align your environment:
```bash
uv sync
```

### 3. Set up API keys

Create a `.env` file for your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```bash
# LLM Provider (at least one is required)
OPENAI_API_KEY=your-key
# ANTHROPIC_API_KEY=your-key
# GROQ_API_KEY=your-key

# Financial Data (Optional for big caps, required for others)
FINANCIAL_DATASETS_API_KEY=your-key
```

## Usage

### 1. Hedge Fund Simulation

Run the main system to generate trading decisions for a list of tickers.

```bash
uv run src/main.py --ticker AAPL,MSFT,NVDA
```

**Options:**

*   `--ticker`: Comma-separated list of symbols (e.g. `AAPL,MSFT`).
*   `--start-date`: Start date for historical data (YYYY-MM-DD).
*   `--end-date`: End date for historical data (YYYY-MM-DD).
*   `--show-reasoning`: Print detailed agent reasoning to the console.
*   `--output`: Save the analysis to a Markdown file (e.g. `--output report.md`).
*   `--holdings`: Load initial portfolio from a JSON file (e.g. `--holdings portfolio.json`).
*   `--model`: Specify LLM model (default: `gpt-4o`).

**Example with Output:**

```bash
uv run src/main.py --ticker AAPL,MSFT --output outputs/analysis.md --show-reasoning
```

### 2. 10-K Report Analysis

Download and analyze the latest 10-K annual report for a specific company using an LLM.

```bash
uv run src/scripts/analyze_10k.py AAPL
```

This will:
1.  Fetch the latest 10-K URL from SEC EDGAR.
2.  Download and cache the raw HTML to `data/10k/`.
3.  Analyze the Business, Risks, MD&A, and Financial Statements sections.
4.  Save a Markdown report to `outputs/10k_reports/`.

**Options:**
*   `--model`: Specify LLM model (default: `gpt-4o`).
*   `--output`: Custom path for the output file.

### 3. Backtesting

Run a backtest simulation over a historical period.

```bash
uv run backtester --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01
```

## Data Providers

You can choose between two data providers:

1.  **Financial Datasets** (Default): High quality structured data. Requires API Key for most symbols.
2.  **YFinance**: Free data. Good for testing major US stocks.

To use YFinance, set it in `.env` or prepend to command:

```bash
DATA_PROVIDER=yfinance uv run src/main.py --ticker AAPL
```

## Project Structure

*   `src/agents/`: Definitions for all 18+ investment agents.
*   `src/tools/`: Utilities for fetching market data (prices, financials, SEC filings).
*   `src/graph/`: LangGraph workflow definitions.
*   `src/scripts/`: Standalone scripts (like `analyze_10k.py`).
*   `data/`: Storage for cached 10-K files and the DuckDB database.
*   `outputs/`: Generated reports.

## How to Contribute

1.  Fork the repository
2.  Create a feature branch
3.  Commit your changes
4.  Push to the branch
5.  Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
