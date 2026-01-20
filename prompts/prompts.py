"""
Stock Analysis Report Generator - LLM Prompts

All prompts are designed to be used sequentially, with each producing
focused output that feeds into the final synthesis.
"""


def get_company_overview_prompt(ticker: str, company_name: str) -> str:
    """Prompt 1: Establish what the company does, business model, and key context."""
    return f"""You are analyzing {company_name} ({ticker}) for an investment research report.

Using web search, gather current information about this company and provide:

1. **Business Description** (2-3 paragraphs)
   - What does the company do?
   - What are their primary products or services?
   - What is their business model (how do they make money)?
   - What markets/geographies do they operate in?

2. **Company Stage**
   - Is this company pre-revenue, early-stage, growth, or mature?
   - When was it founded? When did it go public (if applicable)?

3. **Key Facts**
   - Headquarters location
   - Number of employees (approximate)
   - Current CEO

If this is a PRE-REVENUE company, additionally address:
- What specific problem is this company trying to solve?
- What are the potential applications of their technology/product?
- What is the estimated total addressable market (TAM)?
- What stage of development are they in (R&D, clinical trials, pilot customers, etc.)?

Write in a neutral, informative tone. Do not include investment recommendations in this section."""


def get_financial_analysis_prompt(ticker: str, company_name: str, financial_data: str) -> str:
    """Prompt 2: Analyze financial health using quantitative data."""
    return f"""You are a financial analyst reviewing {company_name} ({ticker}).

Here is the financial data:

<financial_data>
{financial_data}
</financial_data>

Analyze this data and provide:

1. **Revenue Analysis**
   - Current revenue (TTM or most recent annual)
   - Revenue growth rate (YoY, and trend over 3-5 years if available)
   - Revenue concentration risks (if discernible)

2. **Profitability**
   - Gross margin
   - Operating margin
   - Net margin
   - Trend direction (improving, stable, declining)

3. **Balance Sheet Health**
   - Total debt vs. equity (debt-to-equity ratio)
   - Current ratio (current assets / current liabilities)
   - Cash and cash equivalents
   - Assessment: Is the balance sheet strong, adequate, or concerning?

4. **Cash Flow**
   - Operating cash flow (is it positive?)
   - Free cash flow
   - Cash flow vs. net income (quality of earnings check)

5. **Key Metrics Table**
   Format as a simple table:
   | Metric | Value | Assessment |
   |--------|-------|------------|
   | Revenue (TTM) | $X | — |
   | Revenue Growth (YoY) | X% | Strong/Moderate/Weak |
   | Gross Margin | X% | — |
   | Net Margin | X% | — |
   | Debt/Equity | X.X | Low/Moderate/High |
   | Current Ratio | X.X | Healthy/Adequate/Tight |
   | Free Cash Flow | $X | Positive/Negative |

If data is missing or the company is pre-revenue, note what's unavailable and focus on:
- Cash runway (how long can they operate at current burn rate?)
- Funding history and last raise
- Path to profitability (if stated)

Be precise with numbers. If you're uncertain about a figure, say so rather than guessing."""


def get_competitive_positioning_prompt(ticker: str, company_name: str) -> str:
    """Prompt 3: Understand the competitive landscape and differentiation."""
    return f"""You are researching the competitive landscape for {company_name} ({ticker}).

Using web search, analyze:

1. **Direct Competitors**
   - List the main competitors (aim for 3-7 companies)
   - For each, briefly note: name, ticker (if public), and how they compete

2. **Competitive Differentiation**
   - What, if anything, makes {company_name} different from competitors?
   - Do they have any sustainable competitive advantages (moats)?
     Consider: brand, network effects, switching costs, patents/IP, cost advantages, regulatory advantages
   - If no clear moat exists, state that plainly

3. **Market Position**
   - Estimated market share (if available)
   - Are they a leader, challenger, or niche player?

4. **Competitive Risks**
   - What threats do competitors pose?
   - Any emerging competitors or disruptive threats?
   - Is the competitive environment intensifying or stable?

Be honest about uncertainty. If competitive advantages are weak or unclear, say so. Avoid cheerleading language.

Format as flowing paragraphs, not bullet points (except for the competitor list)."""


def get_sentiment_analysis_prompt(ticker: str, company_name: str) -> str:
    """Prompt 4: Assess recent news and market sentiment."""
    return f"""You are conducting a sentiment analysis for {company_name} ({ticker}).

Using web search, find recent news from the past 30 days and analyze:

1. **Recent News Summary**
   - Summarize the 3-5 most significant news items
   - For each: one sentence on what happened, and why it matters

2. **Sentiment Assessment**
   Based on the news flow and market commentary, assess overall sentiment:
   
   - **Bullish**: Predominantly positive news, analyst upgrades, positive catalysts ahead
   - **Neutral**: Mixed news, no strong directional bias, wait-and-see mode
   - **Bearish**: Predominantly negative news, analyst downgrades, concerns mounting
   
   State your assessment clearly: "Overall Sentiment: [Bullish/Neutral/Bearish]"
   Then explain why in 2-3 sentences.

3. **Key Catalysts**
   - Upcoming events that could move the stock (earnings, product launches, regulatory decisions, etc.)
   - Any known risks on the horizon

4. **Notable Analyst Activity** (if found)
   - Recent upgrades/downgrades
   - Price target changes
   - Any notable institutional activity

If news is sparse (common for smaller companies), note that and focus on whatever is available."""


def get_technical_analysis_prompt(ticker: str, company_name: str, price_data: str) -> str:
    """Prompt 5: Assess chart structure and provide a letter grade."""
    return f"""You are a technical analyst reviewing {company_name} ({ticker}).

Here is the historical price and volume data:

<price_data>
{price_data}
</price_data>

Analyze this data and provide:

1. **Trend Assessment**
   - What is the primary trend? (Uptrend / Downtrend / Sideways)
   - How long has this trend been in place?
   - Is the stock above or below its 50-day and 200-day moving averages?

2. **Key Levels**
   - Identify significant support levels (price floors where buying has emerged)
   - Identify significant resistance levels (price ceilings where selling has emerged)
   - Note the current price relative to these levels

3. **Volume Analysis**
   - Is volume increasing or decreasing overall?
   - On recent up days, is volume above or below average?
   - On recent down days, is volume above or below average?
   - Does volume confirm or diverge from price action?

4. **Chart Structure**
   - Any notable patterns forming? (consolidation, breakout, breakdown, etc.)
   - Is price action constructive or deteriorating?

5. **TA Grade**
   
   Assign a letter grade using this rubric:
   
   | Grade | Criteria |
   |-------|----------|
   | A | Clear uptrend, increasing volume on up days, above key MAs, constructive patterns |
   | B | Generally positive with minor concerns (weakening volume, near resistance) |
   | C | Mixed signals, range-bound, no clear trend |
   | D | Downtrend, weak volume on bounces, losing support levels |
   | F | Breakdown, capitulation volume, below all major MAs, no visible support |

   **TA Grade: [Letter]**
   
   **Grade Rationale:** [2-3 sentences explaining why you assigned this grade]

Keep analysis grounded in the data provided. Avoid overly bullish or bearish bias. If the data is limited, note that and provide what assessment you can."""


def get_supplemental_analysis_prompt(
    ticker: str, company_name: str, source_name: str, content: str
) -> str:
    """Prompt 6: Extract insights from user-uploaded files or links."""
    return f"""You are analyzing supplemental research material for {company_name} ({ticker}).

Source: {source_name}

<content>
{content}
</content>

This content was provided as additional context for an investment analysis. Review it and extract:

1. **Source Type & Credibility**
   - What type of document is this? (analyst report, news article, company filing, chart screenshot, data export, etc.)
   - How credible/authoritative is this source?

2. **Key Takeaways**
   - What are the 3-5 most important points from this document relevant to an investment thesis?
   - Are there any specific numbers, forecasts, or claims that stand out?

3. **Thesis Impact**
   - Does this content support a bullish case, bearish case, or is it neutral?
   - Does it reveal anything not likely to be found in standard public sources?

4. **Caveats**
   - Any concerns about the information (outdated, biased source, unverified claims)?
   - What's missing that would make this more useful?

Be concise. Focus on what's actionable or insightful for investment analysis."""


def get_synthesis_prompt(
    ticker: str,
    company_name: str,
    overview_output: str,
    financial_output: str,
    competitive_output: str,
    sentiment_output: str,
    ta_output: str,
    supplemental_output: str = "No supplemental materials provided.",
) -> str:
    """Prompt 7: Assemble all analysis into a cohesive final report."""
    return f"""You are compiling a final investment research report for {company_name} ({ticker}).

You have completed the following analyses:

<company_overview>
{overview_output}
</company_overview>

<financial_analysis>
{financial_output}
</financial_analysis>

<competitive_positioning>
{competitive_output}
</competitive_positioning>

<sentiment_analysis>
{sentiment_output}
</sentiment_analysis>

<technical_analysis>
{ta_output}
</technical_analysis>

<supplemental_analysis>
{supplemental_output}
</supplemental_analysis>

Compile these into a final report using this exact structure:

---

# {company_name} ({ticker})
**Report Generated:** [Current Date]

---

## 1. Company Overview
[Insert company overview, edited for flow and conciseness]

## 2. Financial Health
[Insert financial analysis, including the key metrics table]

## 3. Competitive Positioning
[Insert competitive analysis]

## 4. Sentiment & News
[Insert sentiment analysis]

## 5. Technical Analysis
[Insert TA summary]

**TA Grade: [Letter]**

[Note: Chart will be inserted separately]

## 6. Supplemental Analysis
[If supplemental materials were provided, insert that analysis here. If none, write "No supplemental materials provided."]

## 7. Summary & Key Considerations

**Bull Case:**
- [Point 1]
- [Point 2]
- [Point 3]

**Bear Case:**
- [Point 1]
- [Point 2]
- [Point 3]

**What to Watch:**
- [Key catalyst or decision point 1]
- [Key catalyst or decision point 2]

---

**Sources:** [List all sources used across all analyses]

---

Guidelines for synthesis:
- Remove redundancy across sections
- Ensure consistent tone throughout
- Do not add new analysis; work only with what's provided
- If sections conflict, note the discrepancy rather than hiding it
- Keep the report factual and balanced; avoid promotional language
- Total report length should be 1,500-2,500 words"""
