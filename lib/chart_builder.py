"""
Chart Builder Module

Creates professional candlestick charts with volume and moving averages
using Plotly for display in Streamlit and export to reports.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime


class ChartBuilder:
    """Builds interactive and exportable stock charts using Plotly."""

    def __init__(self, df: pd.DataFrame, ticker: str):
        """
        Initialize chart builder with price data.
        
        Args:
            df: DataFrame with columns: Date, Open, High, Low, Close, Volume
            ticker: Stock ticker symbol for chart title
        """
        self.df = df.copy()
        self.ticker = ticker.upper()
        self._prepare_data()

    def _prepare_data(self):
        """Prepare data and calculate indicators."""
        if self.df.empty:
            return
            
        # Ensure Date column is datetime
        if "Date" in self.df.columns:
            self.df["Date"] = pd.to_datetime(self.df["Date"])
        
        # Calculate moving averages
        self.df["MA50"] = self.df["Close"].rolling(window=50).mean()
        self.df["MA200"] = self.df["Close"].rolling(window=200).mean()
        
        # Calculate average volume for comparison
        self.df["Avg_Volume"] = self.df["Volume"].rolling(window=50).mean()
        
        # Volume colors (green for up days, red for down days)
        self.df["Volume_Color"] = self.df.apply(
            lambda row: "rgba(38, 166, 91, 0.7)" if row["Close"] >= row["Open"] 
            else "rgba(231, 76, 60, 0.7)",
            axis=1
        )

    def create_candlestick_chart(
        self,
        show_volume: bool = True,
        show_ma50: bool = True,
        show_ma200: bool = True,
        height: int = 600,
        period_days: Optional[int] = None,
    ) -> go.Figure:
        """
        Create a candlestick chart with volume and moving averages.
        
        Args:
            show_volume: Whether to show volume subplot
            show_ma50: Whether to show 50-day moving average
            show_ma200: Whether to show 200-day moving average
            height: Chart height in pixels
            period_days: Number of days to show (None = all data)
            
        Returns:
            Plotly Figure object
        """
        if self.df.empty:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No price data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Filter to period if specified
        df = self.df.copy()
        if period_days is not None and len(df) > period_days:
            df = df.tail(period_days)
        
        # Create subplots - 2 rows if showing volume
        if show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=(f"{self.ticker} Price", "Volume")
            )
        else:
            fig = make_subplots(rows=1, cols=1)
        
        # Candlestick trace
        fig.add_trace(
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
                increasing_line_color="rgb(38, 166, 91)",
                decreasing_line_color="rgb(231, 76, 60)",
                increasing_fillcolor="rgba(38, 166, 91, 0.8)",
                decreasing_fillcolor="rgba(231, 76, 60, 0.8)",
            ),
            row=1, col=1
        )
        
        # 50-day MA
        if show_ma50 and "MA50" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["MA50"],
                    name="50-Day MA",
                    line=dict(color="rgba(255, 165, 0, 0.8)", width=1.5),
                    hovertemplate="50-MA: $%{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )
        
        # 200-day MA
        if show_ma200 and "MA200" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["MA200"],
                    name="200-Day MA",
                    line=dict(color="rgba(147, 112, 219, 0.8)", width=1.5),
                    hovertemplate="200-MA: $%{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )
        
        # Volume bars
        if show_volume:
            fig.add_trace(
                go.Bar(
                    x=df["Date"],
                    y=df["Volume"],
                    name="Volume",
                    marker_color=df["Volume_Color"],
                    hovertemplate="Volume: %{y:,.0f}<extra></extra>"
                ),
                row=2, col=1
            )
            
            # Average volume line
            if "Avg_Volume" in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=df["Avg_Volume"],
                        name="50-Day Avg Vol",
                        line=dict(color="rgba(100, 100, 100, 0.5)", width=1, dash="dash"),
                        hovertemplate="Avg Vol: %{y:,.0f}<extra></extra>"
                    ),
                    row=2, col=1
                )
        
        # Layout
        fig.update_layout(
            title=dict(
                text=f"{self.ticker} Stock Analysis",
                x=0.5,
                font=dict(size=18)
            ),
            height=height,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            template="plotly_white",
            margin=dict(l=60, r=40, t=80, b=40),
        )
        
        # Update y-axes
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        # Update x-axes
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128, 128, 128, 0.2)",
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128, 128, 128, 0.2)",
        )
        
        return fig

    def create_simple_line_chart(
        self,
        height: int = 400,
        period_days: Optional[int] = None,
    ) -> go.Figure:
        """
        Create a simple line chart (lighter weight option).
        
        Args:
            height: Chart height in pixels
            period_days: Number of days to show
            
        Returns:
            Plotly Figure object
        """
        if self.df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No price data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
            )
            return fig
        
        df = self.df.copy()
        if period_days is not None and len(df) > period_days:
            df = df.tail(period_days)
        
        fig = go.Figure()
        
        # Main price line
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name="Close Price",
                line=dict(color="rgb(31, 119, 180)", width=2),
                fill="tozeroy",
                fillcolor="rgba(31, 119, 180, 0.1)",
            )
        )
        
        fig.update_layout(
            title=f"{self.ticker} Price History",
            height=height,
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            hovermode="x unified",
        )
        
        return fig

    def get_chart_summary(self) -> dict:
        """
        Get a summary of chart data for text display.
        
        Returns:
            Dictionary with key price statistics
        """
        if self.df.empty:
            return {"error": "No data available"}
        
        latest = self.df.iloc[-1]
        
        summary = {
            "ticker": self.ticker,
            "latest_date": latest["Date"].strftime("%Y-%m-%d") if hasattr(latest["Date"], "strftime") else str(latest["Date"]),
            "current_price": round(latest["Close"], 2),
            "period_high": round(self.df["High"].max(), 2),
            "period_low": round(self.df["Low"].min(), 2),
            "ma50": round(latest["MA50"], 2) if pd.notna(latest.get("MA50")) else None,
            "ma200": round(latest["MA200"], 2) if pd.notna(latest.get("MA200")) else None,
            "avg_volume": int(self.df["Volume"].mean()),
            "latest_volume": int(latest["Volume"]),
        }
        
        # Price position
        if summary["ma50"]:
            summary["above_ma50"] = summary["current_price"] > summary["ma50"]
        if summary["ma200"]:
            summary["above_ma200"] = summary["current_price"] > summary["ma200"]
        
        # Trend determination (simple)
        if len(self.df) >= 20:
            recent_20 = self.df.tail(20)
            start_price = recent_20.iloc[0]["Close"]
            end_price = recent_20.iloc[-1]["Close"]
            summary["20_day_return"] = round(((end_price - start_price) / start_price) * 100, 2)
            
            if summary["20_day_return"] > 5:
                summary["short_term_trend"] = "Uptrend"
            elif summary["20_day_return"] < -5:
                summary["short_term_trend"] = "Downtrend"
            else:
                summary["short_term_trend"] = "Sideways"
        
        return summary

    def export_chart_as_image(self, filepath: str, format: str = "png", **kwargs) -> bool:
        """
        Export chart as a static image file.
        
        Note: Requires kaleido package to be installed.
        
        Args:
            filepath: Output file path
            format: Image format ('png', 'jpg', 'svg', 'pdf')
            **kwargs: Additional arguments passed to create_candlestick_chart
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig = self.create_candlestick_chart(**kwargs)
            fig.write_image(filepath, format=format, scale=2)
            return True
        except Exception as e:
            print(f"Error exporting chart: {e}")
            return False
