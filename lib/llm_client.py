"""
LLM Client Module - LITE VERSION (No Web Search)

Designed for accounts with 30k tokens/minute limit.
Does NOT use web search - relies on yfinance data and Claude's knowledge.
This keeps token usage minimal and avoids rate limits.
"""

import anthropic
from typing import Optional, Dict, Any, List
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class LLMClient:
    """Lite Claude API client - no web search, minimal tokens."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _call_api(self, prompt: str, max_tokens: int = 800) -> str:
        """Make a simple API call - no web search."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in response.content if hasattr(b, "text"))
        except anthropic.RateLimitError:
            # Wait and retry once
            time.sleep(65)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in response.content if hasattr(b, "text"))

    def run_full_analysis(
        self,
        ticker: str,
        company_name: str,
        financial_data: str,
        price_data: str,
        supplemental_contents: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, str]:
        """
        Run complete analysis using only 2 API calls total.
        
        Call 1: Analyze financials + technicals from data
        Call 2: Generate summary and competitive context
        """
        
        results = {}
        
        # Truncate inputs aggressively
        financial_data = financial_data[:3000] if len(financial_data) > 3000 else financial_data
        price_data = price_data[:2000] if len(price_data) > 2000 else price_data
        
        # === CALL 1: Data Analysis (financials + technicals) ===
        if progress_callback:
            progress_callback("Analyzing financial and price data...")
        
        prompt1 = f"""Analyze this data for {company_name} ({ticker}).

FINANCIAL DATA:
{financial_data}

PRICE DATA:
{price_data}

Provide analysis in this EXACT format:

## Company Overview
Based on the data, {company_name} operates in the [sector] industry. [2-3 sentences about the company based on what you know and the data provided.]

## Financial Health
[Analyze revenue, margins, balance sheet from the data above. 4-5 sentences.]

Key Metrics:
| Metric | Value |
|--------|-------|
| Revenue | [from data] |
| Gross Margin | [from data] |
| Debt/Equity | [from data] |
| Free Cash Flow | [from data] |

## Technical Analysis
[Analyze price trend, MAs, volume from the data. 3-4 sentences.]

**TA Grade: [A/B/C/D/F]**
(A=strong uptrend above MAs, B=positive with concerns, C=sideways, D=downtrend, F=breakdown)

**Rationale:** [1-2 sentences]

Keep total response under 600 words."""

        try:
            analysis1 = self._call_api(prompt1, max_tokens=1000)
            results["data_analysis"] = analysis1
        except Exception as e:
            results["data_analysis"] = f"[Analysis failed: {e}]"
        
        # Wait before second call
        time.sleep(30)
        
        # === CALL 2: Context + Summary ===
        if progress_callback:
            progress_callback("Generating competitive analysis and summary...")
        
        prompt2 = f"""For {company_name} ({ticker}), provide:

## Competitive Positioning
Based on your knowledge of {company_name}:
- List 3-4 main competitors
- What differentiates {company_name}? (2 sentences)
- Market position: leader/challenger/niche player? (1 sentence)
- Key competitive risk (1 sentence)

## Recent Context
Note: Unable to search current news. Based on your training knowledge up to early 2025:
- What are typical catalysts or concerns for this company/sector?
- Any known upcoming events or trends? (2-3 sentences)

## Summary

**Bull Case:**
- [point 1]
- [point 2]
- [point 3]

**Bear Case:**
- [point 1]
- [point 2]  
- [point 3]

**What to Watch:**
- [item 1]
- [item 2]

Keep total response under 400 words."""

        try:
            analysis2 = self._call_api(prompt2, max_tokens=700)
            results["context_analysis"] = analysis2
        except Exception as e:
            results["context_analysis"] = f"[Analysis failed: {e}]"
        
        # Process supplemental files if any (one call per file, with delays)
        supplemental_outputs = []
        if supplemental_contents:
            time.sleep(30)
            for i, item in enumerate(supplemental_contents):
                if progress_callback:
                    progress_callback(f"Analyzing uploaded file {i+1}...")
                
                if item.get("type") == "image":
                    output = self._analyze_image(ticker, company_name, item)
                else:
                    content = item.get("content", "")[:2000]
                    prompt = f"""Briefly analyze this document for {company_name} ({ticker}):

{content}

Provide in under 100 words:
1. What this document is
2. Key takeaway for investment thesis
3. Bullish/Bearish/Neutral impact"""
                    
                    try:
                        output = self._call_api(prompt, max_tokens=200)
                    except Exception as e:
                        output = f"[Failed: {e}]"
                
                supplemental_outputs.append(f"**{item.get('name', 'File')}:**\n{output}")
                
                if i < len(supplemental_contents) - 1:
                    time.sleep(30)
        
        results["supplemental"] = "\n\n".join(supplemental_outputs) if supplemental_outputs else ""
        
        # Assemble final report (no API call)
        results["final_report"] = self._assemble_report(ticker, company_name, results)
        
        # Store individual sections for compatibility with UI
        results["overview"] = results.get("data_analysis", "").split("## Financial")[0] if "## Financial" in results.get("data_analysis", "") else results.get("data_analysis", "")
        results["financials"] = self._extract_section(results.get("data_analysis", ""), "Financial Health")
        results["technical"] = self._extract_section(results.get("data_analysis", ""), "Technical Analysis")
        results["competitive"] = self._extract_section(results.get("context_analysis", ""), "Competitive Positioning")
        results["sentiment"] = self._extract_section(results.get("context_analysis", ""), "Recent Context")
        
        return results

    def _analyze_image(self, ticker: str, company_name: str, item: dict) -> str:
        """Analyze an uploaded image."""
        import base64
        
        try:
            image_b64 = base64.standard_b64encode(item["content"]).decode("utf-8")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": item.get("media_type", "image/png"),
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"Briefly describe this image for {company_name} ({ticker}) analysis. What does it show and what's the key insight? (under 75 words)"
                        },
                    ],
                }],
            )
            return "".join(b.text for b in response.content if hasattr(b, "text"))
        except Exception as e:
            return f"[Image analysis failed: {e}]"

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from the analysis text."""
        if section_name not in text:
            return ""
        
        start = text.find(f"## {section_name}")
        if start == -1:
            start = text.find(section_name)
        if start == -1:
            return ""
        
        # Find next section
        next_section = text.find("## ", start + 5)
        if next_section == -1:
            return text[start:]
        return text[start:next_section]

    def _assemble_report(self, ticker: str, company_name: str, results: Dict[str, str]) -> str:
        """Assemble the final report from analysis results."""
        
        data_analysis = results.get("data_analysis", "[Analysis not available]")
        context_analysis = results.get("context_analysis", "[Analysis not available]")
        supplemental = results.get("supplemental", "")
        
        report = f"""# {company_name} ({ticker})
**Report Generated:** {datetime.now().strftime("%B %d, %Y")}

*Note: This report uses financial data from Yahoo Finance and Claude's training knowledge. Real-time news search was not used to stay within API rate limits.*

---

{data_analysis}

---

{context_analysis}

---

## Supplemental Analysis

{supplemental if supplemental else "No supplemental materials provided."}

---

*This report is for informational purposes only and does not constitute investment advice.*
"""
        return report

    # Legacy methods for compatibility
    def analyze_company_overview(self, ticker: str, company_name: str) -> str:
        return "[Included in main analysis]"
    
    def analyze_financials(self, ticker: str, company_name: str, financial_data: str) -> str:
        return "[Included in main analysis]"
    
    def analyze_competitive_positioning(self, ticker: str, company_name: str) -> str:
        return "[Included in main analysis]"
    
    def analyze_sentiment(self, ticker: str, company_name: str) -> str:
        return "[Included in main analysis]"
    
    def analyze_technicals(self, ticker: str, company_name: str, price_data: str) -> str:
        return "[Included in main analysis]"
    
    def synthesize_report(self, **kwargs) -> str:
        return "[Report assembled directly]"
