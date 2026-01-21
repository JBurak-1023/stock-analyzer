"""
LLM Client Module - DEEP ANALYSIS VERSION

Prioritizes depth over speed. Makes 4 focused API calls with delays
between them to stay within 30k tokens/minute rate limit.

Total time: ~4-5 minutes for a comprehensive report.
"""

import anthropic
from typing import Optional, Dict, Any, List
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class LLMClient:
    """Claude API client optimized for deep analysis within rate limits."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.call_delay = 60  # seconds between calls to reset rate limit

    def _call_api(self, prompt: str, max_tokens: int = 1500) -> str:
        """Make API call with retry on rate limit."""
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                return "".join(b.text for b in response.content if hasattr(b, "text"))
            except anthropic.RateLimitError:
                if attempt < 2:
                    time.sleep(65)
                    continue
                raise
        return "[API call failed]"

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
        Run comprehensive analysis with 4 focused API calls.
        
        Call 1: Deep Financial Analysis
        Call 2: Technical Analysis  
        Call 3: Competitive Moat Analysis
        Call 4: Investment Summary
        """
        
        results = {}
        
        # ==========================================
        # CALL 1: DEEP FINANCIAL ANALYSIS
        # ==========================================
        if progress_callback:
            progress_callback("Performing deep financial analysis (1/4)...")
        
        financial_prompt = f"""You are a financial analyst performing due diligence on {company_name} ({ticker}).

Here is the financial data:

{financial_data}

Provide a THOROUGH financial analysis covering:

## Revenue & Growth Analysis
- Current revenue scale and trajectory
- Year-over-year growth rate assessment
- Revenue quality: Is growth organic or acquisition-driven? Recurring vs one-time?
- Sustainability of growth rate

## Profitability Deep Dive
- Gross margin: What does it tell us about pricing power and cost structure?
- Operating margin: How efficient is the business? Trend direction?
- Net margin: After all costs, what drops to the bottom line?
- Compare margins to what you'd expect for this industry

## Balance Sheet Strength
- Debt levels: Is the debt/equity ratio concerning or manageable?
- Liquidity: Can they meet short-term obligations (current ratio)?
- Cash position: How much runway do they have?
- Any red flags (high debt + declining revenue, etc.)?

## Cash Flow Quality
- Is operating cash flow positive and growing?
- Free cash flow: Can they fund growth internally or need external capital?
- Cash flow vs Net Income: Are earnings "real" or accounting-driven?
- Capital allocation: Are they investing in growth, paying dividends, buying back shares?

## Financial Health Score
Rate the overall financial health: STRONG / ADEQUATE / CONCERNING / WEAK
Explain your rating in 2-3 sentences.

## Key Metrics Summary Table
| Metric | Value | Assessment |
|--------|-------|------------|
| Revenue | [value] | [context] |
| Revenue Growth | [value] | Strong (>15%) / Moderate (5-15%) / Weak (<5%) |
| Gross Margin | [value] | [vs industry expectation] |
| Operating Margin | [value] | [trend] |
| Net Margin | [value] | [assessment] |
| Debt/Equity | [value] | Low (<0.5) / Moderate (0.5-1.5) / High (>1.5) |
| Current Ratio | [value] | Healthy (>1.5) / Adequate (1-1.5) / Tight (<1) |
| Free Cash Flow | [value] | [positive/negative, trend] |

Be specific with numbers. Identify any concerns or standout positives."""

        try:
            results["financials"] = self._call_api(financial_prompt, max_tokens=1800)
        except Exception as e:
            results["financials"] = f"[Financial analysis failed: {e}]"
        
        # Wait for rate limit reset
        if progress_callback:
            progress_callback("Waiting for rate limit reset...")
        time.sleep(self.call_delay)
        
        # ==========================================
        # CALL 2: TECHNICAL ANALYSIS
        # ==========================================
        if progress_callback:
            progress_callback("Performing technical analysis (2/4)...")
        
        ta_prompt = f"""You are a technical analyst reviewing {company_name} ({ticker}).

Here is the price and volume data:

{price_data}

Provide a THOROUGH technical analysis:

## Primary Trend Assessment
- What is the dominant trend? (Strong Uptrend / Uptrend / Sideways / Downtrend / Strong Downtrend)
- How long has this trend been in place?
- Is the trend accelerating, stable, or weakening?

## Moving Average Analysis
- Position relative to 50-day MA: Above/Below, by how much?
- Position relative to 200-day MA: Above/Below, by how much?
- MA alignment: Are the 50 and 200 MAs trending in the same direction?
- Any recent MA crossovers (golden cross / death cross)?

## Support & Resistance
- Key support level(s): Where has buying emerged? How strong?
- Key resistance level(s): Where has selling emerged?
- Current price position: Near support, near resistance, or mid-range?
- Risk/reward from current level

## Volume Analysis
- Volume trend: Increasing, decreasing, or stable?
- Volume on up days vs down days: Which has conviction?
- Any unusual volume spikes? What do they indicate?
- Does volume confirm or diverge from price action?

## Chart Structure
- Any recognizable patterns? (consolidation, breakout, breakdown, base-building, etc.)
- Is price action constructive (higher lows) or deteriorating (lower highs)?
- Volatility assessment: Tight range or wide swings?

## Technical Grade: [A / B / C / D / F]

Grading Criteria:
- A: Strong uptrend, above rising MAs, volume confirms, constructive pattern
- B: Uptrend with minor concerns (weakening momentum, approaching resistance)
- C: Sideways/mixed, no clear trend, conflicting signals
- D: Downtrend, below MAs, weak volume on bounces
- F: Breakdown, below all MAs, capitulation signals, no visible support

**Grade: [LETTER]**

**Rationale:** [3-4 sentences explaining the grade with specific reference to the data]

**Key Levels to Watch:**
- Upside target: $[X] (reason)
- Downside risk: $[X] (reason)"""

        try:
            results["technical"] = self._call_api(ta_prompt, max_tokens=1600)
        except Exception as e:
            results["technical"] = f"[Technical analysis failed: {e}]"
        
        # Wait for rate limit reset
        if progress_callback:
            progress_callback("Waiting for rate limit reset...")
        time.sleep(self.call_delay)
        
        # ==========================================
        # CALL 3: COMPETITIVE MOAT ANALYSIS
        # ==========================================
        if progress_callback:
            progress_callback("Analyzing competitive positioning & moat (3/4)...")
        
        moat_prompt = f"""You are analyzing the competitive position and moat of {company_name} ({ticker}).

Based on your knowledge of this company and its industry, provide:

## Business Overview
- What does {company_name} do? (2-3 sentences)
- What is their primary source of revenue?
- What industry/sector do they operate in?

## Competitive Moat Analysis

Evaluate each potential moat source:

**Brand Power:** Does {company_name} have brand recognition that commands premium pricing or customer loyalty?
- Assessment: Strong / Moderate / Weak / None
- Evidence:

**Network Effects:** Does the product/service become more valuable as more people use it?
- Assessment: Strong / Moderate / Weak / None
- Evidence:

**Switching Costs:** How difficult/costly is it for customers to switch to a competitor?
- Assessment: Strong / Moderate / Weak / None
- Evidence:

**Cost Advantages:** Can they produce/deliver at lower cost than competitors?
- Assessment: Strong / Moderate / Weak / None
- Evidence:

**Intangible Assets:** Patents, licenses, regulatory approvals that block competition?
- Assessment: Strong / Moderate / Weak / None
- Evidence:

**Overall Moat Rating:** Wide / Narrow / None
Explanation: (2-3 sentences)

## Competitive Landscape

**Direct Competitors:**
1. [Competitor 1] - [How they compete, relative strength]
2. [Competitor 2] - [How they compete, relative strength]
3. [Competitor 3] - [How they compete, relative strength]

**{company_name}'s Competitive Position:** Leader / Strong Challenger / Niche Player / Struggling

**Emerging Threats:** Any disruptors or new entrants that could threaten the business?

## Key Competitive Risks
1. [Risk 1]
2. [Risk 2]

## Durable Competitive Advantage?
Can {company_name} sustain its market position over 5-10 years? Why or why not? (2-3 sentences)"""

        try:
            results["competitive"] = self._call_api(moat_prompt, max_tokens=1600)
        except Exception as e:
            results["competitive"] = f"[Competitive analysis failed: {e}]"
        
        # Wait for rate limit reset
        if progress_callback:
            progress_callback("Waiting for rate limit reset...")
        time.sleep(self.call_delay)
        
        # ==========================================
        # CALL 4: INVESTMENT SUMMARY
        # ==========================================
        if progress_callback:
            progress_callback("Generating investment summary (4/4)...")
        
        # Truncate previous results for summary context
        fin_summary = results.get("financials", "")[:1500]
        ta_summary = results.get("technical", "")[:1000]
        comp_summary = results.get("competitive", "")[:1000]
        
        summary_prompt = f"""Based on this analysis of {company_name} ({ticker}), create an investment summary.

Financial Analysis Summary:
{fin_summary}

Technical Analysis Summary:
{ta_summary}

Competitive Analysis Summary:
{comp_summary}

Provide:

## Investment Thesis Summary
In 2-3 sentences, what's the core investment case for or against {company_name}?

## Bull Case (Why to Buy)
- [Strongest bullish point with specific reasoning]
- [Second bullish point]
- [Third bullish point]

## Bear Case (Why to Avoid)
- [Strongest bearish point with specific reasoning]
- [Second bearish point]
- [Third bearish point]

## Key Metrics to Monitor
What specific numbers should an investor track to validate or invalidate the thesis?
1. [Metric 1] - Current: [X], Watch for: [threshold]
2. [Metric 2] - Current: [X], Watch for: [threshold]
3. [Metric 3] - Current: [X], Watch for: [threshold]

## Catalysts & Risks
**Near-term catalysts (next 6 months):**
- [Catalyst 1]
- [Catalyst 2]

**Key risks to monitor:**
- [Risk 1]
- [Risk 2]

## Overall Assessment
Combining financials, technicals, and competitive position:
**Investment Outlook:** Bullish / Cautiously Bullish / Neutral / Cautiously Bearish / Bearish

**Rationale:** (2-3 sentences)

Note: This analysis uses financial data from Yahoo Finance and does not include real-time news. Always verify with current information before making investment decisions."""

        try:
            results["summary"] = self._call_api(summary_prompt, max_tokens=1400)
        except Exception as e:
            results["summary"] = f"[Summary failed: {e}]"
        
        # ==========================================
        # PROCESS SUPPLEMENTAL FILES (if any)
        # ==========================================
        supplemental_outputs = []
        if supplemental_contents:
            time.sleep(45)
            for i, item in enumerate(supplemental_contents):
                if progress_callback:
                    progress_callback(f"Analyzing uploaded file {i+1}...")
                
                if item.get("type") == "image":
                    output = self._analyze_image(ticker, company_name, item)
                else:
                    content = item.get("content", "")[:3000]
                    prompt = f"""Analyze this document for {company_name} ({ticker}) investment research:

{content}

Provide:
1. **Document Type:** What is this?
2. **Key Insights:** 3-5 most important points for investment thesis
3. **Numbers/Data:** Any specific figures that matter
4. **Thesis Impact:** Bullish / Bearish / Neutral signal, and why

Keep response focused and actionable."""
                    
                    try:
                        output = self._call_api(prompt, max_tokens=600)
                    except Exception as e:
                        output = f"[Failed: {e}]"
                
                supplemental_outputs.append(f"### {item.get('name', 'Uploaded File')}\n{output}")
                
                if i < len(supplemental_contents) - 1:
                    time.sleep(45)
        
        results["supplemental"] = "\n\n".join(supplemental_outputs) if supplemental_outputs else ""
        
        # ==========================================
        # ASSEMBLE FINAL REPORT
        # ==========================================
        results["final_report"] = self._assemble_report(ticker, company_name, results)
        
        # Store section references for UI compatibility
        results["overview"] = results.get("competitive", "").split("## Competitive Moat")[0] if "## Competitive Moat" in results.get("competitive", "") else ""
        results["sentiment"] = "See Summary section for market outlook and catalysts."
        
        return results

    def _analyze_image(self, ticker: str, company_name: str, item: dict) -> str:
        """Analyze uploaded image."""
        import base64
        
        try:
            image_b64 = base64.standard_b64encode(item["content"]).decode("utf-8")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=400,
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
                            "text": f"""Analyze this image for {company_name} ({ticker}) investment research.

1. What does this image show?
2. Key observations relevant to investment thesis
3. Any specific levels, patterns, or data points of note
4. Bullish/Bearish/Neutral implication"""
                        },
                    ],
                }],
            )
            return "".join(b.text for b in response.content if hasattr(b, "text"))
        except Exception as e:
            return f"[Image analysis failed: {e}]"

    def _assemble_report(self, ticker: str, company_name: str, results: Dict[str, str]) -> str:
        """Assemble the final report from all analysis sections."""
        
        supplemental = results.get("supplemental", "")
        supplemental_section = supplemental if supplemental else "No supplemental materials provided."
        
        report = f"""# {company_name} ({ticker})
**Investment Research Report**
**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Executive Summary

{results.get('summary', '[Summary not available]')}

---

## Financial Analysis

{results.get('financials', '[Financial analysis not available]')}

---

## Technical Analysis

{results.get('technical', '[Technical analysis not available]')}

---

## Competitive Position & Moat

{results.get('competitive', '[Competitive analysis not available]')}

---

## Supplemental Analysis

{supplemental_section}

---

*Disclaimer: This report is for informational purposes only and does not constitute investment advice. Financial data sourced from Yahoo Finance. Analysis based on Claude's training knowledge through early 2025 and does not include real-time news. Always conduct your own due diligence and consult a financial advisor before making investment decisions.*
"""
        return report

    # Legacy method stubs for compatibility
    def analyze_company_overview(self, *args, **kwargs): return "[See full report]"
    def analyze_financials(self, *args, **kwargs): return "[See full report]"
    def analyze_competitive_positioning(self, *args, **kwargs): return "[See full report]"
    def analyze_sentiment(self, *args, **kwargs): return "[See full report]"
    def analyze_technicals(self, *args, **kwargs): return "[See full report]"
    def synthesize_report(self, *args, **kwargs): return "[See full report]"

