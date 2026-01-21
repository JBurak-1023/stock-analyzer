"""
Data Fetcher Module

Wraps yfinance to fetch price history, volume, and financial data.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any


class DataFetcher:
    """Fetches stock data from Yahoo Finance via yfinance."""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper().strip()
        self._stock = None
        self._info: Optional[Dict] = None
        self._history: Optional[pd.DataFrame] = None
        self._financials: Optional[Dict] = None

    @property
    def stock(self):
        if self._stock is None:
            self._stock = yf.Ticker(self.ticker)
        return self._stock

    def get_stock_info(self) -> Dict[str, Any]:
        if self._info is None:
            try:
                self._info = self.stock.info
                if not self._info or len(self._info) < 5:
                    self._info = {"symbol": self.ticker, "shortName": self.ticker}
            except Exception as e:
                self._info = {"error": str(e), "symbol": self.ticker}
        return self._info

    def get_price_history(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        if self._history is None or self._history.empty:
            try:
                self._history = yf.download(
                    self.ticker, 
                    period=period, 
                    interval=interval,
                    progress=False,
                    auto_adjust=True
                )
                
                if self._history.empty:
                    self._history = self.stock.history(period=period, interval=interval)
                
                if not self._history.empty:
                    self._history = self._history.reset_index()
                    if 'Datetime' in self._history.columns:
                        self._history = self._history.rename(columns={'Datetime': 'Date'})
                    
                    # Flatten column names if MultiIndex (happens with yf.download)
                    if isinstance(self._history.columns, pd.MultiIndex):
                        self._history.columns = [col[0] if isinstance(col, tuple) else col for col in self._history.columns]
                        
            except Exception as e:
                print(f"Error fetching price history: {e}")
                self._history = pd.DataFrame()
                
        return self._history

    def get_financial_data(self) -> Dict[str, Any]:
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
            }

            try:
                income_stmt = self.stock.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    latest = income_stmt.iloc[:, 0]
                    financials["income_statement"] = {
                        "total_revenue": self._safe_get(latest, "Total Revenue"),
                        "gross_profit": self._safe_get(latest, "Gross Profit"),
                        "operating_income": self._safe_get(latest, "Operating Income"),
                        "net_income": self._safe_get(latest, "Net Income"),
                    }
            except:
                pass

            try:
                balance = self.stock.balance_sheet
                if balance is not None and not balance.empty:
                    latest = balance.iloc[:, 0]
                    financials["balance_sheet"] = {
                        "total_assets": self._safe_get(latest, "Total Assets"),
                        "total_equity": self._safe_get(latest, "Stockholders Equity"),
                        "current_assets": self._safe_get(latest, "Current Assets"),
                        "current_liabilities": self._safe_get(latest, "Current Liabilities"),
                        "cash_and_equivalents": self._safe_get(latest, "Cash And Cash Equivalents"),
                        "total_debt": self._safe_get(latest, "Total Debt"),
                    }
            except:
                pass

            try:
                cashflow = self.stock.cashflow
                if cashflow is not None and not cashflow.empty:
                    latest = cashflow.iloc[:, 0]
                    financials["cash_flow"] = {
                        "operating_cash_flow": self._safe_get(latest, "Operating Cash Flow"),
                        "free_cash_flow": self._safe_get(latest, "Free Cash Flow"),
                    }
            except:
                pass

        except Exception as e:
            financials["error"] = str(e)

        self._financials = financials
        return financials

    def _safe_get(self, series: pd.Series, key: str) -> Optional[float]:
        try:
            value = series.get(key)
            if value is None or pd.isna(value):
                return None
            return float(value)
        except:
            return None

    def format_financial_data_for_llm(self) -> str:
        data = self.get_financial_data()
        info = self.get_stock_info()
        
        def fmt_num(val, prefix=""):
            if val is None:
                return "N/A"
            try:
                num = float(val)
                if abs(num) >= 1e9:
                    return f"{prefix}{num/1e9:.2f}B"
                elif abs(num) >= 1e6:
                    return f"{prefix}{num/1e6:.2f}M"
                else:
                    return f"{prefix}{num:.2f}"
            except:
                return "N/A"

        def fmt_pct(val):
            if val is None:
                return "N/A"
            try:
                return f"{float(val) * 100:.2f}%"
            except:
                return "N/A"

        def fmt_ratio(val):
            if val is None:
                return "N/A"
            try:
                return f"{float(val):.2f}"
            except:
                return "N/A"

        metrics = data.get("key_metrics", {})
        
        lines = [
            f"Financial Data for {self.ticker}",
            f"Company: {info.get('longName', info.get('shortName', 'N/A'))}",
            f"Sector: {info.get('sector', 'N/A')}",
            f"Industry: {info.get('industry', 'N/A')}",
            "",
            "=== KEY METRICS ===",
            f"Market Cap: {fmt_num(metrics.get('market_cap'), '$')}",
            f"Revenue (TTM): {fmt_num(metrics.get('total_revenue'), '$')}",
            f"Revenue Growth: {fmt_pct(metrics.get('revenue_growth'))}",
            "",
            "=== VALUATION ===",
            f"P/E (Trailing): {fmt_ratio(metrics.get('trailing_pe'))}",
            f"P/E (Forward): {fmt_ratio(metrics.get('forward_pe'))}",
            f"PEG Ratio: {fmt_ratio(metrics.get('peg_ratio'))}",
            f"Price/Book: {fmt_ratio(metrics.get('price_to_book'))}",
            f"Price/Sales: {fmt_ratio(metrics.get('price_to_sales'))}",
            "",
            "=== PROFITABILITY ===",
            f"Gross Margin: {fmt_pct(metrics.get('gross_margins'))}",
            f"Operating Margin: {fmt_pct(metrics.get('operating_margins'))}",
            f"Profit Margin: {fmt_pct(metrics.get('profit_margins'))}",
            f"ROE: {fmt_pct(metrics.get('return_on_equity'))}",
            "",
            "=== BALANCE SHEET ===",
            f"Total Cash: {fmt_num(metrics.get('total_cash'), '$')}",
            f"Total Debt: {fmt_num(metrics.get('total_debt'), '$')}",
            f"Debt/Equity: {fmt_ratio(metrics.get('debt_to_equity'))}",
            f"Current Ratio: {fmt_ratio(metrics.get('current_ratio'))}",
            "",
            "=== CASH FLOW ===",
            f"Operating Cash Flow: {fmt_num(metrics.get('operating_cash_flow'), '$')}",
            f"Free Cash Flow: {fmt_num(metrics.get('free_cash_flow'), '$')}",
            "",
            "=== TRADING ===",
            f"52-Week High: {fmt_num(metrics.get('52_week_high'), '$')}",
            f"52-Week Low: {fmt_num(metrics.get('52_week_low'), '$')}",
            f"50-Day Avg: {fmt_num(metrics.get('50_day_average'), '$')}",
            f"200-Day Avg: {fmt_num(metrics.get('200_day_average'), '$')}",
            f"Beta: {fmt_ratio(metrics.get('beta'))}",
        ]

        return "\n".join(lines)

    def format_price_data_for_llm(self, days: int = 60) -> str:
        df = self.get_price_history()
        
        if df.empty:
            return "Price data unavailable."
        
        # Ensure we have the right columns
        required_cols = ['Close', 'High', 'Low', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                return f"Price data missing column: {col}"
        
        # Calculate moving averages
        df = df.copy()
        df["MA50"] = df["Close"].rolling(window=50, min_periods=1).mean()
        df["MA200"] = df["Close"].rolling(window=200, min_periods=1).mean()
        
        recent = df.tail(days).copy()
        
        if recent.empty:
            return "No recent price data available."
        
        lines = [
            f"Price Data for {self.ticker}",
            f"Period: Last {len(recent)} trading days",
            "",
            "=== CURRENT STATUS ===",
        ]
        
        # Get latest values safely
        latest = recent.iloc[-1]
        current_price = float(latest["Close"])
        
        if len(recent) > 1:
            prev = recent.iloc[-2]
            prev_close = float(prev["Close"])
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        else:
            prev_close = current_price
            change = 0
            change_pct = 0
        
        lines.extend([
            f"Current Price: ${current_price:.2f}",
            f"Previous Close: ${prev_close:.2f}",
            f"Change: ${change:.2f} ({change_pct:+.2f}%)",
        ])
        
        # Moving averages
        ma50 = latest.get("MA50")
        ma200 = latest.get("MA200")
        
        lines.append("")
        lines.append("=== MOVING AVERAGES ===")
        
        if ma50 is not None and not pd.isna(ma50):
            ma50_val = float(ma50)
            lines.append(f"50-Day MA: ${ma50_val:.2f}")
            pct_from_50 = ((current_price - ma50_val) / ma50_val) * 100
            lines.append(f"Price vs 50-MA: {pct_from_50:+.2f}%")
        else:
            lines.append("50-Day MA: N/A")
            
        if ma200 is not None and not pd.isna(ma200):
            ma200_val = float(ma200)
            lines.append(f"200-Day MA: ${ma200_val:.2f}")
            pct_from_200 = ((current_price - ma200_val) / ma200_val) * 100
            lines.append(f"Price vs 200-MA: {pct_from_200:+.2f}%")
        else:
            lines.append("200-Day MA: N/A")
        
        # Period stats
        lines.extend([
            "",
            "=== PERIOD STATISTICS ===",
            f"Period High: ${float(recent['High'].max()):.2f}",
            f"Period Low: ${float(recent['Low'].min()):.2f}",
            f"Average Volume: {int(recent['Volume'].mean()):,}",
        ])
        
        # Recent trend
        if len(recent) >= 20:
            last_20 = recent.tail(20)
            start_price = float(last_20.iloc[0]["Close"])
            end_price = float(last_20.iloc[-1]["Close"])
            period_return = ((end_price - start_price) / start_price) * 100 if start_price != 0 else 0
            
            closes = last_20["Close"].diff()
            up_days = int((closes > 0).sum())
            down_days = int((closes < 0).sum())
            
            lines.extend([
                "",
                "=== LAST 20 DAYS ===",
                f"Return: {period_return:+.2f}%",
                f"Up Days: {up_days}",
                f"Down Days: {down_days}",
            ])
        
        return "\n".join(lines)

    def is_pre_revenue(self, threshold: float = 1_000_000) -> bool:
        metrics = self.get_financial_data().get("key_metrics", {})
        revenue = metrics.get("total_revenue")
        
        if revenue is None:
            return True
        
        try:
            return float(revenue) < threshold
        except:
            return True
