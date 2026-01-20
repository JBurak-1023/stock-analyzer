# Stock Analysis Report Generator

A personal stock research tool that generates comprehensive investment analysis reports. Enter a ticker symbol, optionally upload supporting materials, and receive a structured report covering fundamentals, sentiment, competitive positioning, and technical analysis.

## Features

- **Company Overview**: Business model, products, markets, key facts
- **Financial Analysis**: Revenue, margins, balance sheet, cash flow with key metrics table
- **Competitive Positioning**: Competitors, moats, market position, risks
- **Sentiment & News**: Recent news, sentiment assessment, catalysts
- **Technical Analysis**: Trend, support/resistance, volume analysis with letter grade (A-F)
- **Supplemental Analysis**: Analysis of any uploaded documents or images
- **Interactive Charts**: Candlestick charts with 50/200-day moving averages

## Quick Start

### Prerequisites

1. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
2. **Anthropic API Key** - [Get one here](https://console.anthropic.com/)

### Local Setup

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**
   ```bash
   # Create the secrets file
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   
   # Edit the file and add your API key
   # Replace "your-api-key-here" with your actual Anthropic API key
   ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser** to `http://localhost:8501`

## Deploy to Streamlit Cloud (Free)

1. **Push your code to GitHub**
   - Create a new repository on GitHub
   - Push this folder to the repository
   - **Important**: Do NOT include your `secrets.toml` file (it should be in `.gitignore`)

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository and `app.py`
   - Click "Deploy"

3. **Add your API key**
   - Go to your app's Settings (⚙️ icon)
   - Click "Secrets"
   - Add:
     ```
     ANTHROPIC_API_KEY = "your-actual-api-key"
     ```
   - Click "Save"

4. **Your app is live!** Share the URL with... yourself 😄

## Usage

1. **Enter a stock ticker** (e.g., AAPL, MSFT, GOOGL)
2. **Enter the company name** (e.g., Apple Inc.)
3. **Adjust chart settings** if desired
4. **Upload files** (optional):
   - PDF analyst reports
   - Chart screenshots from TradingView
   - CSV/Excel data files
   - Text files with notes
5. **Click "Generate Report"**
6. **Wait 60-90 seconds** for the analysis to complete
7. **Review your report** and download as HTML or Markdown

## Supported File Types

| Type | Extensions | Use Case |
|------|------------|----------|
| Documents | `.pdf` | Analyst reports, SEC filings |
| Images | `.png`, `.jpg`, `.jpeg` | Chart screenshots, annotations |
| Data | `.csv`, `.xlsx` | Financial data, custom metrics |
| Text | `.txt`, `.md` | Notes, summaries |

## Cost Estimate

Claude API costs approximately **$0.10-0.50 per report** depending on:
- Company complexity
- Amount of news to analyze
- Number of uploaded files
- Response lengths

At 10 reports/week, expect around **$4-20/month**.

## Project Structure

```
stock-analyzer/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── lib/
│   ├── __init__.py
│   ├── data_fetcher.py     # Yahoo Finance data retrieval
│   ├── chart_builder.py    # Plotly chart generation
│   ├── llm_client.py       # Claude API integration
│   ├── file_processor.py   # PDF/image/CSV processing
│   └── report_generator.py # HTML/PDF report generation
├── prompts/
│   ├── __init__.py
│   └── prompts.py          # All 7 analysis prompts
└── .streamlit/
    └── secrets.toml.example # API key template
```

## Troubleshooting

### "API key not configured"
- Make sure you've created `.streamlit/secrets.toml`
- Check that your API key is valid at [console.anthropic.com](https://console.anthropic.com)

### "Could not fetch data for ticker"
- Verify the ticker symbol is correct (use uppercase)
- Some tickers (OTC, foreign exchanges) may not be available

### "Rate limit exceeded"
- The app has built-in retry logic, but heavy use may hit limits
- Wait a minute and try again

### Charts not displaying
- Try refreshing the page
- Check browser console for JavaScript errors

### PDF export not working
- WeasyPrint requires system dependencies that may not be available on all platforms
- Use HTML download instead and print to PDF from your browser

## Customization

### Modifying Prompts
Edit `prompts/prompts.py` to customize:
- What information each section requests
- The TA grading criteria
- Report format and structure

### Changing Chart Style
Edit `lib/chart_builder.py` to:
- Add more technical indicators
- Change colors and styling
- Adjust moving average periods

### Adding Data Sources
Edit `lib/data_fetcher.py` to:
- Add Alpha Vantage integration
- Include additional financial metrics
- Pull data from other sources

## Limitations

- **Data freshness**: yfinance data may be delayed 15-20 minutes
- **Coverage**: Some small-cap or international stocks may have limited data
- **Pre-revenue companies**: Financial analysis will be limited
- **Not investment advice**: This tool is for research purposes only

## License

This is a personal tool. Use at your own risk. Not financial advice.

---

Built with ❤️ using Streamlit, yfinance, Plotly, and Claude AI
