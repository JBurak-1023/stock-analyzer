"""
LLM Client Module - Rate Limit Optimized Version

Designed for accounts with 30k tokens/minute limit.
Uses shorter prompts, minimal outputs, and direct report assembly
instead of a large synthesis call.
"""

import anthropic
from typing import Optional, Dict, Any, List
import time
import sys
from pathlib import Path

# Ensure prompts module is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


def truncate_text(text: str, max_chars: int = 2000) -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('. ')
    if last_period > max_chars * 0.7:
        truncated = truncated[:last_period + 1]
    return truncated


class LLMClient:
    """Rate-limit optimized Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = 3
        self.rate_limit_wait = 65  # seconds to wait after rate limit

    def _call_api(
        self,
        prompt: str,
        use_web_search: bool = False,
        max_tokens: int = 1000,
    ) -> str:
        """Make an API call with rate limit handling."""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "messages": messages,
        }
        
        if use_web_search:
            kwargs["tools"] = [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 3,  # Minimal searches
                }
            ]
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(**kwargs)
                text_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                return "\n".join(text_parts)
                
            except anthropic.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    print(f"Rate limited. Waiting {self.rate_limit_wait}s...")
                    time.sleep(self.rate_limit_wait)
                    continue
                raise e
            except anthropic.APIError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise e
        
        raise Exception("API call failed")

    def analyze_company_overview(self, ticker: str, company_name: str) -> str:
        """Get company overview - CONCISE version."""
        prompt = f"""Analyze {company_name} ({ticker}). Use web search, then provide a BRIEF overview:

1. What the company does (2-3 sentences)
2. Business model (1-2 sentences)  
3. Company stage (pre-revenue/growth/mature)
4. Founded, HQ, CEO

If pre-revenue: What problem they solve and TAM estimate.

Keep response under 400 words. Be direct, no fluff."""

        return self._call_api(prompt, use_web_search=True, max_tokens=800)

    def analyze_financials(self, ticker: str, company_name: str, financial_data: str) -> str:
        """Analyze financials - CONCISE version."""
        # Heavily truncate input data
        financial_data = truncate_text(financial_data, max_chars=2500)
        
        prompt = f"""Financial analysis for {company_name} ({ticker}).

Data:
{financial_data}

Provide BRIEF analysis covering:
1. Revenue & growth (2 sentences)
2. Margins - gross, operating, net (1 sentence each)
3. Balance sheet health (2 sentences)
4. Cash flow (2 sentences)

End with this metrics table:
| Metric | Value | Assessment |
|--------|-------|------------|
| Revenue | $X | - |
| Growth | X% | Strong/Moderate/Weak |
| Gross Margin | X% | - |
| Debt/Equity | X | Low/Moderate/High |
| Free Cash Flow | $X | Positive/Negative |

Keep response under 350 words."""

        return self._call_api(prompt, use_web_search=False, max_tokens=700)

    def analyze_competitive_positioning(self, ticker: str, company_name: str) -> str:
        """Analyze competition - CONCISE version."""
        prompt = f"""Competitive analysis for {company_name} ({ticker}). Use web search.

Provide BRIEFLY:
1. List 3-5 main competitors (name, ticker if public)
2. What differentiates {company_name}? Any moat? (2-3 sentences)
3. Market position - leader/challenger/niche? (1 sentence)
4. Key competitive risk (1-2 sentences)

Keep response under 300 words. Be direct."""

        return self._call_api(prompt, use_web_search=True, max_tokens=600)

    def analyze_sentiment(self, ticker: str, company_name: str) -> str:
        """Analyze sentiment - CONCISE version."""
        prompt = f"""Sentiment analysis for {company_name} ({ticker}). Use web search for recent news.

Provide:
1. Top 3 recent news items (1 sentence each)
2. Overall Sentiment: [Bullish/Neutral/Bearish] - explain in 1-2 sentences
3. Key upcoming catalyst (1 sentence)
4. Notable analyst activity if any (1 sentence)

Keep response under 250 words."""

        return self._call_api(prompt, use_web_search=True, max_tokens=500)

    def analyze_technicals(self, ticker: str, company_name: str, price_data: str) -> str:
        """Technical analysis - CONCISE version."""
        # Heavily truncate price data
        price_data = truncate_text(price_data, max_chars=2000)
        
        prompt = f"""Technical analysis for {company_name} ({ticker}).

Data:
{price_data}

Provide BRIEFLY:
1. Trend: Uptrend/Downtrend/Sideways - how long? (1 sentence)
2. Position vs 50-day and 200-day MAs (1 sentence)
3. Key support and resistance levels (1 sentence)
4. Volume assessment (1 sentence)

Then assign a grade:
**TA Grade: [A/B/C/D/F]**

Grading:
A = Clear uptrend, above MAs, strong volume
B = Generally positive, minor concerns
C = Mixed/sideways
D = Downtrend, losing support
F = Breakdown, below all MAs

**Grade Rationale:** (2 sentences max)

Keep response under 250 words."""

        return self._call_api(prompt, use_web_search=False, max_tokens=500)

    def analyze_supplemental(
        self, ticker: str, company_name: str, source_name: str, content: str
    ) -> str:
        """Analyze supplemental file - CONCISE version."""
        content = truncate_text(content, max_chars=2000)
        
        prompt = f"""Analyze this document for {company_name} ({ticker}).

Source: {source_name}
Content: {content}

Provide:
1. Document type (1 sentence)
2. Key takeaways (3 bullet points max)
3. Thesis impact: Bullish/Bearish/Neutral (1 sentence)

Keep response under 150 words."""

        return self._call_api(prompt, use_web_search=False, max_tokens=300)

    def analyze_supplemental_image(
        self,
        ticker: str,
        company_name: str,
        source_name: str,
        image_data: bytes,
        media_type: str = "image/png",
    ) -> str:
        """Analyze uploaded image."""
        import base64
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text", 
                        "text": f"""Analyze this image for {company_name} ({ticker}).

Provide briefly:
1. What it shows
2. Key insight (1-2 sentences)
3. Bullish/Bearish/Neutral for investment thesis

Keep under 100 words."""
                    },
                ],
            }
        ]
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=250,
                messages=messages,
            )
            return "".join(b.text for b in response.content if hasattr(b, "text"))
        except Exception as e:
            return f"[Image analysis failed: {str(e)}]"

    def create_summary(
        self,
        ticker: str,
        company_name: str,
        overview: str,
        financials: str,
        competitive: str,
        sentiment: str,
        technical: str,
    ) -> str:
        """Create just the bull/bear summary - small focused call."""
        
        # Extract just key points from each section (very aggressive truncation)
        overview_brief = truncate_text(overview, 500)
        financials_brief = truncate_text(financials, 500)
        competitive_brief = truncate_text(competitive, 400)
        sentiment_brief = truncate_text(sentiment, 400)
        technical_brief = truncate_text(technical, 400)
        
        prompt = f"""Based on this analysis of {company_name} ({ticker}), create a summary.

Overview: {overview_brief}
Financials: {financials_brief}
Competitive: {competitive_brief}
Sentiment: {sentiment_brief}
Technical: {technical_brief}

Provide ONLY:

**Bull Case:**
- [point 1]
- [point 2]
- [point 3]

**Bear Case:**
- [point 1]
- [point 2]
- [point 3]

**What to Watch:**
- [catalyst 1]
- [catalyst 2]

Keep each point to 1 sentence. No other text."""

        return self._call_api(prompt, use_web_search=False, max_tokens=400)

    def run_full_analysis(
        self,
        ticker: str,
        company_name: str,
        financial_data: str,
        price_data: str,
        supplemental_contents: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, str]:
        """Run analysis with aggressive rate limit management."""
        
        results = {}
        
        # Each web search call needs significant delay
        # Non-web-search calls need less delay
        
        # Step 1: Company Overview (web search)
        if progress_callback:
            progress_callback("Analyzing company overview...")
        try:
            results["overview"] = self.analyze_company_overview(ticker, company_name)
        except Exception as e:
            results["overview"] = f"[Failed: {e}]"
        
        time.sleep(45)  # Long wait after web search call
        
        # Step 2: Financials (no web search)
        if progress_callback:
            progress_callback("Analyzing financials...")
        try:
            results["financials"] = self.analyze_financials(ticker, company_name, financial_data)
        except Exception as e:
            results["financials"] = f"[Failed: {e}]"
        
        time.sleep(20)  # Shorter wait, no web search
        
        # Step 3: Competitive (web search)
        if progress_callback:
            progress_callback("Analyzing competitive positioning...")
        try:
            results["competitive"] = self.analyze_competitive_positioning(ticker, company_name)
        except Exception as e:
            results["competitive"] = f"[Failed: {e}]"
        
        time.sleep(45)  # Long wait after web search
        
        # Step 4: Sentiment (web search)
        if progress_callback:
            progress_callback("Analyzing sentiment...")
        try:
            results["sentiment"] = self.analyze_sentiment(ticker, company_name)
        except Exception as e:
            results["sentiment"] = f"[Failed: {e}]"
        
        time.sleep(45)  # Long wait after web search
        
        # Step 5: Technical (no web search)
        if progress_callback:
            progress_callback("Performing technical analysis...")
        try:
            results["technical"] = self.analyze_technicals(ticker, company_name, price_data)
        except Exception as e:
            results["technical"] = f"[Failed: {e}]"
        
        # Process supplemental files if any
        supplemental_outputs = []
        if supplemental_contents:
            time.sleep(30)
            for i, item in enumerate(supplemental_contents):
                if progress_callback:
                    progress_callback(f"Analyzing file {i+1}/{len(supplemental_contents)}...")
                try:
                    if item.get("type") == "image":
                        output = self.analyze_supplemental_image(
                            ticker, company_name, item["name"],
                            item["content"], item.get("media_type", "image/png")
                        )
                    else:
                        output = self.analyze_supplemental(
                            ticker, company_name, item["name"], item["content"]
                        )
                    supplemental_outputs.append(f"**{item['name']}**\n{output}")
                except Exception as e:
                    supplemental_outputs.append(f"**{item['name']}**\n[Failed: {e}]")
                time.sleep(20)
        
        results["supplemental"] = "\n\n".join(supplemental_outputs) if supplemental_outputs else ""
        
        # Step 6: Create summary (small call)
        if progress_callback:
            progress_callback("Creating summary...")
        time.sleep(30)
        
        try:
            results["summary"] = self.create_summary(
                ticker, company_name,
                results.get("overview", ""),
                results.get("financials", ""),
                results.get("competitive", ""),
                results.get("sentiment", ""),
                results.get("technical", ""),
            )
        except Exception as e:
            results["summary"] = f"[Summary failed: {e}]"
        
        # Assemble final report directly (NO synthesis API call)
        results["final_report"] = self._assemble_report(ticker, company_name, results)
        
        return results

    def _assemble_report(self, ticker: str, company_name: str, results: Dict[str, str]) -> str:
        """Assemble report directly from sections - no API call needed."""
        
        from datetime import datetime
        
        report = f"""# {company_name} ({ticker})
**Report Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## 1. Company Overview

{results.get('overview', '[Not available]')}

---

## 2. Financial Health

{results.get('financials', '[Not available]')}

---

## 3. Competitive Positioning

{results.get('competitive', '[Not available]')}

---

## 4. Sentiment & News

{results.get('sentiment', '[Not available]')}

---

## 5. Technical Analysis

{results.get('technical', '[Not available]')}

[Chart displayed separately]

---

## 6. Supplemental Analysis

{results.get('supplemental', 'No supplemental materials provided.')}

---

## 7. Summary & Key Considerations

{results.get('summary', '[Not available]')}

---

*This report is for informational purposes only and does not constitute investment advice.*
"""
        return report

    # Keep legacy method for compatibility
    def synthesize_report(self, **kwargs) -> str:
        """Legacy method - now handled by _assemble_report."""
        return "[Report assembled directly - no synthesis call needed]"
