"""
Data Fetcher Module

Wraps yfinance to fetch price history, volume, and financial data.
Includes error handling and data formatting for downstream use.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import json
import requests


# Fix for Streamlit Cloud - set headers to avoid blocking
yf.pdr_override()

# Monkey-patch to add headers (helps avoid Yahoo blocking cloud IPs)
import yfinance.data as _yf_data
_yf_data.YfData.user_agent_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


class DataFetcher:
    """Fetches stock data from Yahoo Finance via yfinance."""

    def __init__(self, ticker: str):
        """
        Initialize the data fetcher with a ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
        """
        self.ticker = ticker.upper().strip()
        self._stock = None
        self._info: Optional[Dict] = None
        self._history: Optional[pd.DataFrame] = None
        self._financials: Optional[Dict] = None

    @property
    def stock(self):
        """Lazy load the yfinance Ticker object."""
        if self._stock is None:
            self._stock = yf.Ticker(self.ticker)
        return self._stock

    def get_stock_info(self) -> Dict[str, Any]:
        """
        Get basic stock information.
        
        Returns:
            Dictionary with stock info (name, sector, industry, etc.)
        """
        if self._info is None:
            try:
                self._info = self.stock.info
                # Check if we got valid data
                if not self._info or self._info.get('regularMarketPrice') is None:
                    # Try a backup approach
                    self._info = self._fetch_info_backup()
            except Exception as e:
                print(f"Error fetching stock info: {e}")
                self._info = {"error": str(e)}
        return self._info

    def _fetch_info_backup(self) -> Dict[str, Any]:
        """Backup method to fetch basic info if main method fails."""
        try:
            # Try to at least get price data
            hist = self.stock.history(period="5d")
            if not hist.empty:
                return {
                    "regularMarketPrice": hist['Close'].iloc[-1],
                    "symbol": self.ticker,
                    "shortName": self.ticker,
                }
        except:
            pass
        return {"error": "Could not fetch stock info"}

    def get_price_history(
        self, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical price and volume data.
        
        Args:
            period: Time period ('6mo', '1y', '2y', '5y', 'max')
            interval: Data interval ('1d', '1wk', '1mo')
            
        Returns:
            DataFrame with OHLCV data
        """
        if self._history is None or self._history.empty:
            try:
                # Method 1: Standard approach
                self._history = self.stock.history(period=period, interval=interval)
                
                # If empty, try download method
                if self._history.empty:
                    self._history = yf.download(
                        self.ticker, 
                        period=period, 
                        interval=interval,
                        progress=False,
                        auto_adjust=True
                    )
                
                # Reset index to make Date a column
                if not self._history.empty:
                    self._history = self._history.reset_index()
                    # Ensure column name is 'Date'
                    if 'Datetime' in self._history.columns:
                        self._history = self._history.rename(columns={'Datetime': 'Date'})
                        
            except Exception as e:
                print(f"Error fetching price history: {e}")
                self._history = pd.DataFrame()
                
        return self._history

    def get_financial_data(self) -> Dict[str, Any]:
        """
        Fetch financial statements and key metrics.
        
        Returns:
            Dictionary containing income statement, balance sheet, 
            cash flow, and key ratios
        """
        if self._financials is not None:
            return self._financials

        financials = {
            "income_statement": {},
            "balance_sheet": {},
            "cash_flow": {},
            "key_metrics": {},
        }

        try:
            info = self.get_stock_info()
            
            # Key metrics from info
            financials["key_metrics"] = {
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                "profit_margins": info.get("profitMargins"),
                "gross_margins": info.get("grossMargins"),
                "operating_margins": info.get("operatingMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "debt_to_equity": info.get("debtToEquity"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "free_cash_flow": info.get("freeCashflow"),
                "operating_cash_flow": info.get("operatingCashflow"),
                "total_cash": info.get("totalCash"),
                "total_debt": info.get("totalDebt"),
                "total_revenue": info.get("totalRevenue"),
                "revenue_per_share": info.get("revenuePerShare"),
                "dividend_yield": info.get("dividendYield"),
                "payout_ratio": info.get("payoutRatio"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "50_day_average": info.get("fiftyDayAverage"),
                "200_day_average": info.get("twoHundredDayAverage"),
                "shares_outstanding": info.get("sharesOutstanding"),
                "float_shares": info.get("floatShares"),
                "shares_short": info.get("sharesShort"),
                "short_ratio": info.get("shortRatio"),
            }

            # Income statement
            try:
                income_stmt = self.stock.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    # Get most recent year's data
                    latest = income_stmt.iloc[:, 0]
                    financials["income_statement"] = {
                        "total_revenue": self._safe_get(latest, "Total Revenue"),
                        "gross_profit": self._safe_get(latest, "Gross Profit"),
                        "operating_income": self._safe_get(latest, "Operating Income"),
                        "net_income": self._safe_get(latest, "Net Income"),
                        "ebitda": self._safe_get(latest, "EBITDA"),
                    }
                    # Get historical for trends
                    financials["income_statement"]["historical_revenue"] = self._get_historical_series(
                        income_stmt, "Total Revenue"
                    )
            except Exception as e:
                financials["income_statement"]["error"] = str(e)

            # Balance sheet
            try:
                balance = self.stock.balance_sheet
                if balance is not None and not balance.empty:
                    latest = balance.iloc[:, 0]
                    financials["balance_sheet"] = {
                        "total_assets": self._safe_get(latest, "Total Assets"),
                        "total_liabilities": self._safe_get(latest, "Total Liabilities Net Minority Interest"),
                        "total_equity": self._safe_get(latest, "Stockholders Equity"),
                        "current_assets": self._safe_get(latest, "Current Assets"),
                        "current_liabilities": self._safe_get(latest, "Current Liabilities"),
                        "cash_and_equivalents": self._safe_get(latest, "Cash And Cash Equivalents"),
                        "total_debt": self._safe_get(latest, "Total Debt"),
                        "long_term_debt": self._safe_get(latest, "Long Term Debt"),
                    }
            except Exception as e:
                financials["balance_sheet"]["error"] = str(e)

            # Cash flow
            try:
                cashflow = self.stock.cashflow
                if cashflow is not None and not cashflow.empty:
                    latest = cashflow.iloc[:, 0]
                    financials["cash_flow"] = {
                        "operating_cash_flow": self._safe_get(latest, "Operating Cash Flow"),
                        "capital_expenditure": self._safe_get(latest, "Capital Expenditure"),
                        "free_cash_flow": self._safe_get(latest, "Free Cash Flow"),
                        "dividends_paid": self._safe_get(latest, "Cash Dividends Paid"),
                    }
            except Exception as e:
                financials["cash_flow"]["error"] = str(e)

        except Exception as e:
            financials["error"] = str(e)

        self._financials = financials
        return financials

    def _safe_get(self, series: pd.Series, key: str) -> Optional[float]:
        """Safely get a value from a pandas Series."""
        try:
            value = series.get(key)
            if pd.isna(value):
                return None
            return float(value)
        except (KeyError, TypeError, ValueError):
            return None

    def _get_historical_series(self, df: pd.DataFrame, row_name: str) -> Dict[str, float]:
        """Extract historical values for a given metric."""
        result = {}
        try:
            if row_name in df.index:
                for col in df.columns:
                    date_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
                    value = df.loc[row_name, col]
                    if not pd.isna(value):
                        result[date_str] = float(value)
        except Exception:
            pass
        return result

    def format_financial_data_for_llm(self) -> str:
        """
        Format financial data as a string for LLM consumption.
        
        Returns:
            Formatted string with key financial metrics
        """
        data = self.get_financial_data()
        info = self.get_stock_info()
        
        lines = [
            f"Financial Data for {self.ticker}",
            f"Company: {info.get('longName', info.get('shortName', 'N/A'))}",
            f"Sector: {info.get('sector', 'N/A')}",
            f"Industry: {info.get('industry', 'N/A')}",
            "",
            "=== KEY METRICS ===",
        ]

        metrics = data.get("key_metrics", {})
        
        def fmt_num(val, prefix="", suffix="", divisor=1):
            if val is None:
                return "N/A"
            try:
                num = float(val) / divisor
                if abs(num) >= 1e9:
                    return f"{prefix}{num/1e9:.2f}B{suffix}"
                elif abs(num) >= 1e6:
                    return f"{prefix}{num/1e6:.2f}M{suffix}"
                elif abs(num) >= 1e3:
                    return f"{prefix}{num/1e3:.2f}K{suffix}"
                else:
                    return f"{prefix}{num:.2f}{suffix}"
            except (TypeError, ValueError):
                return "N/A"

        def fmt_pct(val):
            if val is None:
                return "N/A"
            try:
                return f"{float(val) * 100:.2f}%"
            except (TypeError, ValueError):
                return "N/A"

        def fmt_ratio(val):
            if val is None:
                return "N/A"
            try:
                return f"{float(val):.2f}"
            except (TypeError, ValueError):
                return "N/A"

        lines.extend([
            f"Market Cap: {fmt_num(metrics.get('market_cap'), prefix='$')}",
            f"Enterprise Value: {fmt_num(metrics.get('enterprise_value'), prefix='$')}",
            f"Total Revenue (TTM): {fmt_num(metrics.get('total_revenue'), prefix='$')}",
            f"Revenue Growth (YoY): {fmt_pct(metrics.get('revenue_growth'))}",
            "",
            "=== VALUATION ===",
            f"P/E (Trailing): {fmt_ratio(metrics.get('trailing_pe'))}",
            f"P/E (Forward): {fmt_ratio(metrics.get('forward_pe'))}",
            f"PEG Ratio: {fmt_ratio(metrics.get('peg_ratio'))}",
            f"Price/Book: {fmt_ratio(metrics.get('price_to_book'))}",
            f"Price/Sales: {fmt_ratio(metrics.get('price_to_sales'))}",
            f"EV/Revenue: {fmt_ratio(metrics.get('enterprise_to_revenue'))}",
            f"EV/EBITDA: {fmt_ratio(metrics.get('enterprise_to_ebitda'))}",
            "",
            "=== PROFITABILITY ===",
            f"Gross Margin: {fmt_pct(metrics.get('gross_margins'))}",
            f"Operating Margin: {fmt_pct(metrics.get('operating_margins'))}",
            f"Profit Margin: {fmt_pct(metrics.get('profit_margins'))}",
            f"Return on Equity: {fmt_pct(metrics.get('return_on_equity'))}",
            f"Return on Assets: {fmt_pct(metrics.get('return_on_assets'))}",
            "",
            "=== BALANCE SHEET ===",
            f"Total Cash: {fmt_num(metrics.get('total_cash'), prefix='$')}",
            f"Total Debt: {fmt_num(metrics.get('total_debt'), prefix='$')}",
            f"Debt/Equity: {fmt_ratio(metrics.get('debt_to_equity'))}",
            f"Current Ratio: {fmt_ratio(metrics.get('current_ratio'))}",
            f"Quick Ratio: {fmt_ratio(metrics.get('quick_ratio'))}",
            "",
            "=== CASH FLOW ===",
            f"Operating Cash Flow: {fmt_num(metrics.get('operating_cash_flow'), prefix='$')}",
            f"Free Cash Flow: {fmt_num(metrics.get('free_cash_flow'), prefix='$')}",
            "",
            "=== TRADING INFO ===",
            f"52-Week High: {fmt_num(metrics.get('52_week_high'), prefix='$')}",
            f"52-Week Low: {fmt_num(metrics.get('52_week_low'), prefix='$')}",
            f"50-Day Average: {fmt_num(metrics.get('50_day_average'), prefix='$')}",
            f"200-Day Average: {fmt_num(metrics.get('200_day_average'), prefix='$')}",
            f"Beta: {fmt_ratio(metrics.get('beta'))}",
            "",
            "=== DIVIDENDS ===",
            f"Dividend Yield: {fmt_pct(metrics.get('dividend_yield'))}",
            f"Payout Ratio: {fmt_pct(metrics.get('payout_ratio'))}",
        ])

        # Add income statement details if available
        income = data.get("income_statement", {})
        if income and "error" not in income:
            lines.extend([
                "",
                "=== INCOME STATEMENT (Most Recent) ===",
                f"Total Revenue: {fmt_num(income.get('total_revenue'), prefix='$')}",
                f"Gross Profit: {fmt_num(income.get('gross_profit'), prefix='$')}",
                f"Operating Income: {fmt_num(income.get('operating_income'), prefix='$')}",
                f"Net Income: {fmt_num(income.get('net_income'), prefix='$')}",
                f"EBITDA: {fmt_num(income.get('ebitda'), prefix='$')}",
            ])
            
            # Historical revenue if available
            hist_rev = income.get("historical_revenue", {})
            if hist_rev:
                lines.append("")
                lines.append("Historical Revenue:")
                for date, value in sorted(hist_rev.items(), reverse=True)[:4]:
                    lines.append(f"  {date}: {fmt_num(value, prefix='$')}")

        # Add balance sheet details if available
        balance = data.get("balance_sheet", {})
        if balance and "error" not in balance:
            lines.extend([
                "",
                "=== BALANCE SHEET (Most Recent) ===",
                f"Total Assets: {fmt_num(balance.get('total_assets'), prefix='$')}",
                f"Total Liabilities: {fmt_num(balance.get('total_liabilities'), prefix='$')}",
                f"Stockholders Equity: {fmt_num(balance.get('total_equity'), prefix='$')}",
                f"Current Assets: {fmt_num(balance.get('current_assets'), prefix='$')}",
                f"Current Liabilities: {fmt_num(balance.get('current_liabilities'), prefix='$')}",
                f"Cash & Equivalents: {fmt_num(balance.get('cash_and_equivalents'), prefix='$')}",
                f"Long-term Debt: {fmt_num(balance.get('long_term_debt'), prefix='$')}",
            ])

        # Add cash flow details if available
        cf = data.get("cash_flow", {})
        if cf and "error" not in cf:
            lines.extend([
                "",
                "=== CASH FLOW (Most Recent) ===",
                f"Operating Cash Flow: {fmt_num(cf.get('operating_cash_flow'), prefix='$')}",
                f"Capital Expenditure: {fmt_num(cf.get('capital_expenditure'), prefix='$')}",
                f"Free Cash Flow: {fmt_num(cf.get('free_cash_flow'), prefix='$')}",
                f"Dividends Paid: {fmt_num(cf.get('dividends_paid'), prefix='$')}",
            ])

        return "\n".join(lines)

    def format_price_data_for_llm(self, days: int = 90) -> str:
        """
        Format recent price/volume data for LLM technical analysis.
        
        Args:
            days: Number of trading days to include (default 90 ~= 4 months)
            
        Returns:
            Formatted string with price and volume data
        """
        df = self.get_price_history()
        
        if df.empty:
            return "Price data unavailable."
        
        # Get recent data
        recent = df.tail(days).copy()
        
        # Calculate moving averages on full dataset first
        df_full = self.get_price_history()
        df_full["MA50"] = df_full["Close"].rolling(window=50).mean()
        df_full["MA200"] = df_full["Close"].rolling(window=200).mean()
        df_full["Avg_Volume"] = df_full["Volume"].rolling(window=50).mean()
        
        # Get recent with MAs
        recent = df_full.tail(days).copy()
        
        lines = [
            f"Price and Volume Data for {self.ticker}",
            f"Period: Last {len(recent)} trading days",
            "",
            "=== CURRENT STATUS ===",
        ]
        
        if not recent.empty:
            latest = recent.iloc[-1]
            prev = recent.iloc[-2] if len(recent) > 1 else latest
            
            current_price = latest["Close"]
            prev_close = prev["Close"]
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            lines.extend([
                f"Current Price: ${current_price:.2f}",
                f"Previous Close: ${prev_close:.2f}",
                f"Change: ${change:.2f} ({change_pct:+.2f}%)",
                f"Day's High: ${latest['High']:.2f}",
                f"Day's Low: ${latest['Low']:.2f}",
                f"Volume: {int(latest['Volume']):,}",
                f"50-Day Average Volume: {int(latest['Avg_Volume']):,}" if pd.notna(latest.get('Avg_Volume')) else "",
                "",
                "=== MOVING AVERAGES ===",
                f"50-Day MA: ${latest['MA50']:.2f}" if pd.notna(latest.get('MA50')) else "50-Day MA: N/A (insufficient data)",
                f"200-Day MA: ${latest['MA200']:.2f}" if pd.notna(latest.get('MA200')) else "200-Day MA: N/A (insufficient data)",
            ])
            
            # Position relative to MAs
            if pd.notna(latest.get('MA50')):
                pct_from_50 = ((current_price - latest['MA50']) / latest['MA50']) * 100
                lines.append(f"Price vs 50-MA: {pct_from_50:+.2f}%")
            if pd.notna(latest.get('MA200')):
                pct_from_200 = ((current_price - latest['MA200']) / latest['MA200']) * 100
                lines.append(f"Price vs 200-MA: {pct_from_200:+.2f}%")
        
        # Calculate period statistics
        lines.extend([
            "",
            "=== PERIOD STATISTICS ===",
            f"Period High: ${recent['High'].max():.2f}",
            f"Period Low: ${recent['Low'].min():.2f}",
            f"Average Close: ${recent['Close'].mean():.2f}",
            f"Average Volume: {int(recent['Volume'].mean()):,}",
        ])
        
        # Recent price action summary (last 20 days)
        last_20 = recent.tail(20)
        if len(last_20) >= 2:
            start_price = last_20.iloc[0]["Close"]
            end_price = last_20.iloc[-1]["Close"]
            period_return = ((end_price - start_price) / start_price) * 100
            
            up_days = (last_20["Close"].diff() > 0).sum()
            down_days = (last_20["Close"].diff() < 0).sum()
            
            avg_vol = last_20["Volume"].mean()
            up_day_vol = last_20[last_20["Close"].diff() > 0]["Volume"].mean()
            down_day_vol = last_20[last_20["Close"].diff() < 0]["Volume"].mean()
            
            lines.extend([
                "",
                "=== LAST 20 DAYS ===",
                f"Return: {period_return:+.2f}%",
                f"Up Days: {up_days}",
                f"Down Days: {down_days}",
                f"Avg Volume on Up Days: {int(up_day_vol):,}" if pd.notna(up_day_vol) else "Avg Volume on Up Days: N/A",
                f"Avg Volume on Down Days: {int(down_day_vol):,}" if pd.notna(down_day_vol) else "Avg Volume on Down Days: N/A",
            ])
        
        # Daily data summary (last 10 days)
        lines.extend([
            "",
            "=== RECENT DAILY DATA (Last 10 Days) ===",
            "Date | Open | High | Low | Close | Volume | Change%"
        ])
        
        last_10 = recent.tail(10)
        for i, (_, row) in enumerate(last_10.iterrows()):
            date_str = row["Date"].strftime("%Y-%m-%d") if hasattr(row["Date"], "strftime") else str(row["Date"])[:10]
            
            # Calculate daily change
            if i > 0:
                prev_close = last_10.iloc[i-1]["Close"]
                daily_change = ((row["Close"] - prev_close) / prev_close) * 100
            else:
                daily_change = 0
            
            lines.append(
                f"{date_str} | ${row['Open']:.2f} | ${row['High']:.2f} | "
                f"${row['Low']:.2f} | ${row['Close']:.2f} | {int(row['Volume']):,} | {daily_change:+.2f}%"
            )
        
        return "\n".join(lines)

    def is_pre_revenue(self, threshold: float = 1_000_000) -> bool:
        """
        Check if company is pre-revenue or early-stage.
        
        Args:
            threshold: Revenue threshold below which company is considered pre-revenue
            
        Returns:
            True if company appears to be pre-revenue
        """
        metrics = self.get_financial_data().get("key_metrics", {})
        revenue = metrics.get("total_revenue")
        
        if revenue is None:
            return True
        
        try:
            return float(revenue) < threshold
        except (TypeError, ValueError):
            return True

