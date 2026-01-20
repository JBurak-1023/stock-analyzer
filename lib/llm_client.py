"""
LLM Client Module

Handles all interactions with the Claude API, including
web search-enabled calls for qualitative analysis.

Includes rate limit handling and output truncation for efficiency.
"""

import anthropic
from typing import Optional, Dict, Any, List
import time
import sys
from pathlib import Path

# Ensure prompts module is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts.prompts import (
    get_company_overview_prompt,
    get_financial_analysis_prompt,
    get_competitive_positioning_prompt,
    get_sentiment_analysis_prompt,
    get_technical_analysis_prompt,
    get_supplemental_analysis_prompt,
    get_synthesis_prompt,
)


def truncate_text(text: str, max_chars: int = 4000) -> str:
    """
    Truncate text to a maximum character length, preserving complete sentences.
    
    Args:
        text: Text to truncate
        max_chars: Maximum characters to keep
        
    Returns:
        Truncated text with indicator if truncated
    """
    if len(text) <= max_chars:
        return text
    
    # Find a good break point (end of sentence)
    truncated = text[:max_chars]
    
    # Try to break at sentence end
    for end_char in ['. ', '.\n', '! ', '?\n']:
        last_period = truncated.rfind(end_char)
        if last_period > max_chars * 0.7:  # Only if we keep at least 70%
            truncated = truncated[:last_period + 1]
            break
    
    return truncated + "\n\n[... output truncated for efficiency ...]"


class LLMClient:
    """Client for Claude API interactions with web search support."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-sonnet-4-20250514)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = 5
        self.base_delay = 5  # Base delay between calls in seconds
        self.rate_limit_delay = 65  # Wait time when rate limited (just over 1 minute)

    def _call_api(
        self,
        prompt: str,
        use_web_search: bool = False,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """
        Make an API call to Claude with rate limit handling.
        
        Args:
            prompt: The prompt to send
            use_web_search: Whether to enable web search tool
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            
        Returns:
            Text response from Claude
        """
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        # Add web search tool if requested
        if use_web_search:
            kwargs["tools"] = [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,  # Reduced from 10 to limit token usage
                }
            ]
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(**kwargs)
                
                # Extract text from response
                text_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                
                return "\n".join(text_parts)
                
            except anthropic.RateLimitError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait longer for rate limits - need to wait for the minute to reset
                    wait_time = self.rate_limit_delay
                    print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                continue
            except anthropic.APIError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (2 ** attempt)
                    print(f"API error. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                continue
        
        raise last_error or Exception("API call failed after retries")

    def analyze_company_overview(self, ticker: str, company_name: str) -> str:
        """Get company overview using web search."""
        prompt = get_company_overview_prompt(ticker, company_name)
        return self._call_api(prompt, use_web_search=True, max_tokens=1500)

    def analyze_financials(
        self, ticker: str, company_name: str, financial_data: str
    ) -> str:
        """Analyze financial data."""
        # Truncate financial data if too long
        financial_data = truncate_text(financial_data, max_chars=6000)
        prompt = get_financial_analysis_prompt(ticker, company_name, financial_data)
        return self._call_api(prompt, use_web_search=False, max_tokens=1500)

    def analyze_competitive_positioning(self, ticker: str, company_name: str) -> str:
        """Analyze competitive landscape using web search."""
        prompt = get_competitive_positioning_prompt(ticker, company_name)
        return self._call_api(prompt, use_web_search=True, max_tokens=1500)

    def analyze_sentiment(self, ticker: str, company_name: str) -> str:
        """Analyze news and sentiment using web search."""
        prompt = get_sentiment_analysis_prompt(ticker, company_name)
        return self._call_api(prompt, use_web_search=True, max_tokens=1500)

    def analyze_technicals(
        self, ticker: str, company_name: str, price_data: str
    ) -> str:
        """Perform technical analysis and assign grade."""
        # Truncate price data if too long
        price_data = truncate_text(price_data, max_chars=4000)
        prompt = get_technical_analysis_prompt(ticker, company_name, price_data)
        return self._call_api(prompt, use_web_search=False, max_tokens=1500)

    def analyze_supplemental(
        self, ticker: str, company_name: str, source_name: str, content: str
    ) -> str:
        """Analyze supplemental material (uploaded file content)."""
        # Truncate content if too long
        content = truncate_text(content, max_chars=5000)
        prompt = get_supplemental_analysis_prompt(ticker, company_name, source_name, content)
        return self._call_api(prompt, use_web_search=False, max_tokens=1000)

    def analyze_supplemental_image(
        self,
        ticker: str,
        company_name: str,
        source_name: str,
        image_data: bytes,
        media_type: str = "image/png",
    ) -> str:
        """Analyze an uploaded image (e.g., chart screenshot)."""
        import base64
        
        # Encode image to base64
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
        
        prompt_text = f"""You are analyzing a chart or image uploaded as supplemental research material for {company_name} ({ticker}).

Source: {source_name}

This image was provided as additional context for an investment analysis. Please analyze what you see and extract:

1. **Image Type & Content** - What does this image show?
2. **Key Takeaways** - Most important insights relevant to an investment thesis
3. **Thesis Impact** - Does this support a bullish case, bearish case, or neutral?

Be concise and focus on actionable insights."""

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
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    messages=messages,
                )
                
                text_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                
                return "\n".join(text_parts)
            except anthropic.RateLimitError:
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay)
                    continue
                raise
        
        return "[Image analysis failed]"

    def synthesize_report(
        self,
        ticker: str,
        company_name: str,
        overview_output: str,
        financial_output: str,
        competitive_output: str,
        sentiment_output: str,
        ta_output: str,
        supplemental_output: str = "No supplemental materials provided.",
    ) -> str:
        """Synthesize all analyses into a final report."""
        
        # Truncate all inputs to keep synthesis prompt manageable
        overview_output = truncate_text(overview_output, max_chars=3000)
        financial_output = truncate_text(financial_output, max_chars=3000)
        competitive_output = truncate_text(competitive_output, max_chars=2500)
        sentiment_output = truncate_text(sentiment_output, max_chars=2500)
        ta_output = truncate_text(ta_output, max_chars=2500)
        supplemental_output = truncate_text(supplemental_output, max_chars=2000)
        
        prompt = get_synthesis_prompt(
            ticker=ticker,
            company_name=company_name,
            overview_output=overview_output,
            financial_output=financial_output,
            competitive_output=competitive_output,
            sentiment_output=sentiment_output,
            ta_output=ta_output,
            supplemental_output=supplemental_output,
        )
        
        return self._call_api(prompt, use_web_search=False, max_tokens=4000)

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
        Run the complete analysis pipeline with rate limit handling.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            financial_data: Formatted financial data string
            price_data: Formatted price/volume data string
            supplemental_contents: List of dicts with 'name', 'content', 'type' keys
            progress_callback: Optional function to call with progress updates
            
        Returns:
            Dictionary with all analysis outputs and final report
        """
        results = {}
        
        # Define steps with delays between them to avoid rate limits
        # Delay is in seconds - spread calls over multiple minutes
        steps = [
            ("overview", "Analyzing company overview...", 
             lambda: self.analyze_company_overview(ticker, company_name), 15),
            ("financials", "Analyzing financials...", 
             lambda: self.analyze_financials(ticker, company_name, financial_data), 10),
            ("competitive", "Analyzing competitive positioning...", 
             lambda: self.analyze_competitive_positioning(ticker, company_name), 15),
            ("sentiment", "Analyzing news and sentiment...", 
             lambda: self.analyze_sentiment(ticker, company_name), 15),
            ("technical", "Performing technical analysis...", 
             lambda: self.analyze_technicals(ticker, company_name, price_data), 10),
        ]
        
        # Run main analyses with delays between each
        for i, (key, message, func, delay) in enumerate(steps):
            if progress_callback:
                progress_callback(message)
            try:
                results[key] = func()
            except Exception as e:
                results[key] = f"[Analysis failed: {str(e)}]"
            
            # Add delay before next call (except after last one)
            if i < len(steps) - 1:
                time.sleep(delay)
        
        # Process supplemental materials
        supplemental_outputs = []
        if supplemental_contents:
            for i, item in enumerate(supplemental_contents):
                if progress_callback:
                    progress_callback(f"Analyzing supplemental file {i+1}/{len(supplemental_contents)}...")
                
                try:
                    if item.get("type") == "image":
                        output = self.analyze_supplemental_image(
                            ticker, company_name,
                            item["name"],
                            item["content"],
                            item.get("media_type", "image/png")
                        )
                    else:
                        output = self.analyze_supplemental(
                            ticker, company_name,
                            item["name"],
                            item["content"]
                        )
                    supplemental_outputs.append(f"### {item['name']}\n{output}")
                except Exception as e:
                    supplemental_outputs.append(f"### {item['name']}\n[Analysis failed: {str(e)}]")
                
                # Delay between supplemental files
                if i < len(supplemental_contents) - 1:
                    time.sleep(10)
        
        supplemental_combined = "\n\n".join(supplemental_outputs) if supplemental_outputs else "No supplemental materials provided."
        results["supplemental"] = supplemental_combined
        
        # Wait before synthesis to ensure rate limit window resets
        if progress_callback:
            progress_callback("Preparing final synthesis (waiting for rate limit reset)...")
        time.sleep(20)
        
        # Synthesize final report
        if progress_callback:
            progress_callback("Synthesizing final report...")
        
        try:
            results["final_report"] = self.synthesize_report(
                ticker=ticker,
                company_name=company_name,
                overview_output=results.get("overview", "[Not available]"),
                financial_output=results.get("financials", "[Not available]"),
                competitive_output=results.get("competitive", "[Not available]"),
                sentiment_output=results.get("sentiment", "[Not available]"),
                ta_output=results.get("technical", "[Not available]"),
                supplemental_output=supplemental_combined,
            )
        except Exception as e:
            results["final_report"] = f"[Report synthesis failed: {str(e)}]"
        
        return results
