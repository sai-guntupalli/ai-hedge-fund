import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Style, init
import questionary
from src.agents.portfolio_manager import portfolio_management_agent
from src.agents.risk_manager import risk_management_agent
from src.graph.state import AgentState
from src.utils.display import print_trading_output
from src.utils.analysts import ANALYST_ORDER, get_analyst_nodes
from src.utils.progress import progress
from src.utils.visualize import save_graph_as_png
from src.utils.reporting import generate_markdown_report
from src.data.storage import HedgeFundDB
from src.tools.api import get_financial_metrics, get_prices
from src.cli.input import parse_cli_inputs

from src.utils.portfolio_loader import load_holdings

import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)


def parse_hedge_fund_response(response):
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except TypeError as e:
        print(f"Invalid response type (expected string, got {type(response).__name__}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while parsing response: {e}\nResponse: {repr(response)}")
        return None


##### Run the Hedge Fund #####
def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    selected_analysts: list[str] = [],
    model_name: str = "gpt-4.1",
    model_provider: str = "OpenAI",
):
    # Start progress tracking
    progress.start()

    try:
        # Build workflow (default to all analysts when none provided)
        workflow = create_workflow(selected_analysts if selected_analysts else None)
        agent = workflow.compile()

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )

        return {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }
    finally:
        # Stop progress tracking
        progress.stop()


def start(state: AgentState):
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts=None):
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Always add risk and portfolio management
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_manager", portfolio_management_agent)

    # Connect selected analysts to risk management
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_manager")
    workflow.add_edge("portfolio_manager", END)

    workflow.set_entry_point("start_node")
    return workflow


if __name__ == "__main__":
    inputs = parse_cli_inputs(
        description="Run the hedge fund trading system",
        require_tickers=True,
        default_months_back=None,
        include_graph_flag=True,
        include_reasoning_flag=True,
    )

    tickers = inputs.tickers
    selected_analysts = inputs.selected_analysts
    
    # Load holdings if provided
    loaded_portfolio_data = None
    if inputs.holdings_file:
        try:
            loaded_portfolio_data = load_holdings(inputs.holdings_file)
            # Add tickers from holdings to the list (deduplicated)
            tickers = list(set(tickers + loaded_portfolio_data['tickers']))
            print(f"Loaded {len(loaded_portfolio_data['tickers'])} positions from {inputs.holdings_file}")
        except Exception as e:
            print(f"Error loading holdings file: {e}")
            sys.exit(1)

    if not tickers:
        print("No tickers provided or found in holdings file. Exiting.")
        sys.exit(0)

    # If loading from holdings, verify we have a long enough history (5 years request)
    start_date = inputs.start_date
    if inputs.holdings_file and not inputs.raw_args.start_date:
        # User didn't specify start date, but provided holdings. 
        # Requirement: "price details for last 5 years"
        # We override the default (which might be 3 months) to 5 years.
        start_date = (datetime.now() - relativedelta(years=5)).strftime("%Y-%m-%d")
        print(f"Holdings mode: Setting start date to {start_date} (5 years ago)")


    # Construct portfolio here
    portfolio = {
        "cash": inputs.initial_cash,
        "margin_requirement": inputs.margin_requirement,
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,
                "short": 0.0,
            }
            for ticker in tickers
        },
    }

    # Update portfolio with loaded positions
    if loaded_portfolio_data:
        for ticker, pos_data in loaded_portfolio_data['positions'].items():
            if ticker in portfolio['positions']:
                portfolio['positions'][ticker].update(pos_data)

    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=inputs.end_date,
        portfolio=portfolio,
        show_reasoning=inputs.show_reasoning,
        selected_analysts=inputs.selected_analysts,
        model_name=inputs.model_name,
        model_provider=inputs.model_provider,
    )
    
    if inputs.output_file:
        generate_markdown_report(
            result,
            tickers,
            inputs.start_date,
            inputs.end_date,
            inputs.output_file
        )
    else:
        print_trading_output(result)

    # Save to DuckDB
    try:
        db = HedgeFundDB()
        run_id = db.save_analysis_run(
            tickers=tickers,
            start_date=inputs.start_date,
            end_date=inputs.end_date,
            model_name=inputs.model_name,
            model_provider=inputs.model_provider
        )
        
        # Save Decisions
        db.save_portfolio_decisions(run_id, result["decisions"])
        
        # Save Signals
        db.save_agent_signals(run_id, result["analyst_signals"])
        
        # Save Metrics & Prices for each ticker
        # We re-fetch here (cached) to ensure we store what matches the run context
        for ticker in tickers:
            try:
                metrics = get_financial_metrics(ticker, inputs.end_date)
                db.save_financial_metrics(run_id, ticker, metrics)
                
                prices = get_prices(ticker, inputs.start_date, inputs.end_date)
                db.save_prices(run_id, ticker, prices)
            except Exception as e:
                print(f"Error saving data for {ticker}: {e}")
                
        db.close()
        print(f"Analysis results saved to database (Run ID: {run_id})")
    except Exception as e:
        print(f"Error saving to DuckDB: {e}")
