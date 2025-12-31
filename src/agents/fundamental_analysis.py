from src.tools.sec_tools import extract_sections
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.models import get_model

def analyze_10k(text: str, ticker: str, model_name: str = "gpt-4o") -> str:
    """
    Analyzes the text of a 10-K report using an LLM.
    """
    if not text:
        return "No text provided for analysis."

    
    # Identify key sections using regex
    sections = extract_sections(text)
    
    # Construct a targeted context
    # We prioritize: Business, Risk Factors, MD&A, Financial Statements
    context = ""
    
    if "Business" in sections:
        context += f"--- BUSINESS OVERVIEW ---\n{sections['Business'][:10000]}\n\n"
        
    if "Risk Factors" in sections:
        context += f"--- RISK FACTORS ---\n{sections['Risk Factors'][:10000]}\n\n"
        
    if "MD&A" in sections:
        context += f"--- MANAGEMENT'S DISCUSSION & ANALYSIS ---\n{sections['MD&A'][:10000]}\n\n"

    if "Financial Statements" in sections:
        context += f"--- FINANCIAL STATEMENTS ---\n{sections['Financial Statements'][:15000]}\n\n"
        
    # If regex failed to find anything substantial, fallback to raw truncation
    if len(context) < 1000:
        context = text[:30000] + "\n...[Truncated]..."
        

    system_prompt = f"""You are a seasoned fundamental investment analyst. 
    You are analyzing the 10-K annual report for {ticker}.
    
    Your goal is to extract providing a concise but comprehensive summary emphasizing:
    1. Business Overview: What does the company actually do?
    2. Key Risks: What are the top 3-5 material risks?
    3. Management's View: What is the tone of the management's discussion?
    4. Strategic Direction: Where is the company heading?
    5. Key Financial Metrics: Extract the following if available in the text:
       - Total Revenue (latest year)
       - Net Income / Profit (latest year)
       - Earnings Per Share (EPS)
       - Any other notable financial highlights mentioned.
    
    Output your analysis in Markdown format.
    """
    
    user_prompt = f"Here are the relevant sections extracted from the 10-K report:\n\n{context}"
    
    llm = get_model(model_name, "OpenAI")
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        return response.content
    except Exception as e:
        return f"Error during analysis: {e}"
