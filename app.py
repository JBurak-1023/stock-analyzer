"""
Stock Analysis Report Generator

A Streamlit application that generates comprehensive stock analysis reports
using data from yfinance and analysis from Claude AI.
"""

import streamlit as st
import sys
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.data_fetcher import DataFetcher
from lib.chart_builder import ChartBuilder
from lib.llm_client import LLMClient
from lib.file_processor import FileProcessor
from lib.report_generator import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Report Generator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #718096;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #3182ce;
    }
    .report-section {
        background-color: #f7fafc;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #c6f6d5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #38a169;
    }
    .warning-box {
        background-color: #fefcbf;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #d69e2e;
    }
    .error-box {
        background-color: #fed7d7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #e53e3e;
    }
</style>
""", unsafe_allow_html=True)


def check_api_key() -> bool:
    """Check if API key is configured."""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("⚠️ Anthropic API key not configured. Please add it to your Streamlit secrets.")
        st.markdown("""
        **To configure your API key:**
        
        1. **Local development:** Create `.streamlit/secrets.toml` with:
           ```
           ANTHROPIC_API_KEY = "your-api-key-here"
           ```
        
        2. **Streamlit Cloud:** Go to App Settings → Secrets and add:
           ```
           ANTHROPIC_API_KEY = "your-api-key-here"
           ```
        
        Get your API key from [console.anthropic.com](https://console.anthropic.com)
        """)
        return False
    return True


def main():
    """Main application."""
    
    # Header
    st.markdown('<p class="main-header">📈 Stock Analysis Report Generator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate comprehensive investment research reports powered by AI</p>', unsafe_allow_html=True)
    
    # Check API key
    if not check_api_key():
        return
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📋 Report Settings")
        
        # Ticker input
        ticker = st.text_input(
            "Stock Ticker",
            placeholder="e.g., AAPL",
            help="Enter the stock ticker symbol"
        ).upper().strip()
        
        # Company name input
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Apple Inc.",
            help="Enter the full company name"
        ).strip()
        
        st.divider()
        
        # Chart settings
        st.subheader("📊 Chart Settings")
        chart_period = st.selectbox(
            "Historical Period",
            options=["6mo", "1y", "2y", "5y"],
            index=1,
            help="How much historical data to show"
        )
        
        show_ma50 = st.checkbox("Show 50-Day MA", value=True)
        show_ma200 = st.checkbox("Show 200-Day MA", value=True)
        
        st.divider()
        
        # File uploads
        st.subheader("📎 Supplemental Files")
        uploaded_files = st.file_uploader(
            "Upload research materials",
            type=["pdf", "png", "jpg", "jpeg", "csv", "xlsx", "txt", "md"],
            accept_multiple_files=True,
            help="Upload analyst reports, charts, or data files"
        )
        
        if uploaded_files:
            st.caption(f"📁 {len(uploaded_files)} file(s) uploaded")
            for f in uploaded_files:
                st.caption(f"  • {f.name}")
        
        st.divider()
        
        # Generate button
        generate_button = st.button(
            "🚀 Generate Report",
            type="primary",
            use_container_width=True,
            disabled=not (ticker and company_name)
        )
        
        if not ticker or not company_name:
            st.caption("Enter ticker and company name to generate report")
    
    # Main content area
    if generate_button and ticker and company_name:
        run_analysis(ticker, company_name, chart_period, show_ma50, show_ma200, uploaded_files)
    else:
        # Show welcome/instructions
        show_welcome()


def show_welcome():
    """Display welcome message and instructions."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### How to Use
        
        1. **Enter a ticker symbol** (e.g., AAPL, MSFT, GOOGL)
        2. **Enter the company name** (e.g., Apple Inc.)
        3. **Optionally upload files** like analyst reports or chart screenshots
        4. **Click Generate Report** to create your analysis
        
        The report will include:
        - Company overview and business model
        - Financial health analysis
        - Competitive positioning
        - News and sentiment analysis
        - Technical analysis with price chart
        - Analysis of any uploaded materials
        - Summary with bull/bear cases
        """)
    
    with col2:
        st.markdown("""
        ### Supported File Types
        
        📄 **Documents**
        - PDF files
        
        🖼️ **Images**
        - PNG, JPG, JPEG
        - Chart screenshots
        
        📊 **Data**
        - CSV files
        - Excel files (.xlsx)
        
        📝 **Text**
        - Plain text (.txt)
        - Markdown (.md)
        """)


def run_analysis(
    ticker: str,
    company_name: str,
    chart_period: str,
    show_ma50: bool,
    show_ma200: bool,
    uploaded_files: list
):
    """Run the full analysis pipeline."""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(message: str, progress: float):
        status_text.text(message)
        progress_bar.progress(progress)
    
    try:
        # Initialize components
        update_progress("Initializing...", 0.05)
        
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        data_fetcher = DataFetcher(ticker)
        file_processor = FileProcessor()
        llm_client = LLMClient(api_key)
        
        # Fetch price data
        update_progress("Fetching price data...", 0.10)
        price_history = data_fetcher.get_price_history(period=chart_period)
        
        if price_history.empty:
            st.error(f"❌ Could not fetch data for ticker: {ticker}")
            st.info("Please verify the ticker symbol is correct and try again.")
            return
        
        # Fetch financial data
        update_progress("Fetching financial data...", 0.15)
        financial_data = data_fetcher.format_financial_data_for_llm()
        price_data = data_fetcher.format_price_data_for_llm()
        
        # Check if pre-revenue
        is_pre_revenue = data_fetcher.is_pre_revenue()
        if is_pre_revenue:
            st.info("ℹ️ This appears to be a pre-revenue company. Analysis will focus on growth potential.")
        
        # Build chart
        update_progress("Building chart...", 0.20)
        chart_builder = ChartBuilder(price_history, ticker)
        chart_fig = chart_builder.create_candlestick_chart(
            show_ma50=show_ma50,
            show_ma200=show_ma200,
            height=500
        )
        
        # Process uploaded files
        supplemental_contents = []
        if uploaded_files:
            update_progress("Processing uploaded files...", 0.25)
            processed_files = file_processor.process_multiple_files(uploaded_files)
            
            for pf in processed_files:
                if "error" in pf:
                    st.warning(f"⚠️ Could not process {pf['name']}: {pf['error']}")
                else:
                    supplemental_contents.append(pf)
        
        # Create progress callback for LLM
        llm_steps = [
            ("overview", 0.35),
            ("financials", 0.45),
            ("competitive", 0.55),
            ("sentiment", 0.65),
            ("technical", 0.75),
            ("supplemental", 0.85),
            ("synthesis", 0.95),
        ]
        step_index = [0]
        
        def llm_progress(message: str):
            idx = min(step_index[0], len(llm_steps) - 1)
            update_progress(message, llm_steps[idx][1])
            step_index[0] += 1
        
        # Run LLM analysis
        update_progress("Starting AI analysis...", 0.30)
        
        results = llm_client.run_full_analysis(
            ticker=ticker,
            company_name=company_name,
            financial_data=financial_data,
            price_data=price_data,
            supplemental_contents=supplemental_contents if supplemental_contents else None,
            progress_callback=llm_progress,
        )
        
        # Generate report
        update_progress("Generating report...", 0.95)
        
        report_gen = ReportGenerator(ticker, company_name)
        report_components = report_gen.generate_report_for_streamlit(
            report_content=results.get("final_report", "Report generation failed."),
            chart_figure=chart_fig,
        )
        
        # Complete
        update_progress("Complete!", 1.0)
        progress_bar.empty()
        status_text.empty()
        
        # Display results
        display_report(ticker, company_name, report_components, results, chart_fig)
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.exception(e)


def display_report(
    ticker: str,
    company_name: str,
    report_components: dict,
    analysis_results: dict,
    chart_fig
):
    """Display the generated report."""
    
    st.success(f"✅ Report generated successfully for {company_name} ({ticker})")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📄 Full Report", "📊 Chart", "🔍 Raw Analysis"])
    
    with tab1:
        # Display the formatted report
        st.markdown(report_components.get("markdown", "No report content"))
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # HTML download
            html_content = report_components.get("html", "")
            st.download_button(
                label="📥 Download HTML Report",
                data=html_content,
                file_name=f"{ticker}_analysis_report.html",
                mime="text/html",
            )
        
        with col2:
            # Markdown download
            md_content = report_components.get("markdown", "")
            st.download_button(
                label="📥 Download Markdown",
                data=md_content,
                file_name=f"{ticker}_analysis_report.md",
                mime="text/markdown",
            )
    
    with tab2:
        # Display interactive chart
        st.plotly_chart(chart_fig, use_container_width=True)
        
        # Chart summary
        chart_builder = ChartBuilder(DataFetcher(ticker).get_price_history(), ticker)
        summary = chart_builder.get_chart_summary()
        
        if "error" not in summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", f"${summary.get('current_price', 'N/A')}")
            with col2:
                st.metric("Period High", f"${summary.get('period_high', 'N/A')}")
            with col3:
                st.metric("Period Low", f"${summary.get('period_low', 'N/A')}")
            with col4:
                ret = summary.get('20_day_return')
                if ret is not None:
                    st.metric("20-Day Return", f"{ret:+.2f}%")
    
    with tab3:
        # Show individual analysis sections
        st.subheader("Individual Analysis Sections")
        
        sections = [
            ("Company Overview", "overview"),
            ("Financial Analysis", "financials"),
            ("Competitive Positioning", "competitive"),
            ("Sentiment & News", "sentiment"),
            ("Technical Analysis", "technical"),
            ("Supplemental Analysis", "supplemental"),
        ]
        
        for title, key in sections:
            with st.expander(title):
                content = analysis_results.get(key, "Not available")
                st.markdown(content)


if __name__ == "__main__":
    main()
