"""
LLM Client Module

Handles all interactions with the Claude API, including
web search-enabled calls for qualitative analysis.
"""

import anthropic
from typing import Optional, Dict, Any, List, Generator
import json
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
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _call_api(
        self,
        prompt: str,
        use_web_search: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """
        Make an API call to Claude.
        
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
                    "max_uses": 10,
                }
            ]
        
        # Retry logic
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
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except anthropic.APIError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
        
        raise last_error or Exception("API call failed after retries")

    def analyze_company_overview(self, ticker: str, company_name: str) -> str:
        """
        Get company overview using web search.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            
        Returns:
            Company overview analysis text
        """
        prompt = get_company_overview_prompt(ticker, company_name)
        return self._call_api(prompt, use_web_search=True)

    def analyze_financials(
        self, ticker: str, company_name: str, financial_data: str
    ) -> str:
        """
        Analyze financial data.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            financial_data: Formatted financial data string
            
        Returns:
            Financial analysis text
        """
        prompt = get_financial_analysis_prompt(ticker, company_name, financial_data)
        return self._call_api(prompt, use_web_search=False)

    def analyze_competitive_positioning(self, ticker: str, company_name: str) -> str:
        """
        Analyze competitive landscape using web search.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            
        Returns:
            Competitive analysis text
        """
        prompt = get_competitive_positioning_prompt(ticker, company_name)
        return self._call_api(prompt, use_web_search=True)

    def analyze_sentiment(self, ticker: str, company_name: str) -> str:
        """
        Analyze news and sentiment using web search.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            
        Returns:
            Sentiment analysis text
        """
        prompt = get_sentiment_analysis_prompt(ticker, company_name)
        return self._call_api(prompt, use_web_search=True)

    def analyze_technicals(
        self, ticker: str, company_name: str, price_data: str
    ) -> str:
        """
        Perform technical analysis and assign grade.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            price_data: Formatted price/volume data string
            
        Returns:
            Technical analysis text with grade
        """
        prompt = get_technical_analysis_prompt(ticker, company_name, price_data)
        return self._call_api(prompt, use_web_search=False)

    def analyze_supplemental(
        self, ticker: str, company_name: str, source_name: str, content: str
    ) -> str:
        """
        Analyze supplemental material (uploaded file content).
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            source_name: Name/path of the uploaded file
            content: Extracted content from the file
            
        Returns:
            Supplemental analysis text
        """
        prompt = get_supplemental_analysis_prompt(ticker, company_name, source_name, content)
        return self._call_api(prompt, use_web_search=False)

    def analyze_supplemental_image(
        self,
        ticker: str,
        company_name: str,
        source_name: str,
        image_data: bytes,
        media_type: str = "image/png",
    ) -> str:
        """
        Analyze an uploaded image (e.g., chart screenshot).
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            source_name: Name of the image file
            image_data: Raw image bytes
            media_type: MIME type of the image
            
        Returns:
            Analysis of the image content
        """
        import base64
        
        # Encode image to base64
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
        
        prompt_text = f"""You are analyzing a chart or image uploaded as supplemental research material for {company_name} ({ticker}).

Source: {source_name}

This image was provided as additional context for an investment analysis. Please analyze what you see and extract:

1. **Image Type & Content**
   - What does this image show? (chart, screenshot, data visualization, etc.)
   - What key information is visible?

2. **Key Takeaways**
   - What are the most important insights from this image relevant to an investment thesis?
   - Any notable patterns, levels, or data points?

3. **Thesis Impact**
   - Does this image support a bullish case, bearish case, or is it neutral?

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
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=messages,
        )
        
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        
        return "\n".join(text_parts)

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
        """
        Synthesize all analyses into a final report.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            overview_output: Output from company overview analysis
            financial_output: Output from financial analysis
            competitive_output: Output from competitive analysis
            sentiment_output: Output from sentiment analysis
            ta_output: Output from technical analysis
            supplemental_output: Combined output from supplemental analyses
            
        Returns:
            Final synthesized report text
        """
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
        
        return self._call_api(prompt, use_web_search=False, max_tokens=8192)

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
        Run the complete analysis pipeline.
        
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
        steps = [
            ("overview", "Analyzing company overview...", 
             lambda: self.analyze_company_overview(ticker, company_name)),
            ("financials", "Analyzing financials...", 
             lambda: self.analyze_financials(ticker, company_name, financial_data)),
            ("competitive", "Analyzing competitive positioning...", 
             lambda: self.analyze_competitive_positioning(ticker, company_name)),
            ("sentiment", "Analyzing news and sentiment...", 
             lambda: self.analyze_sentiment(ticker, company_name)),
            ("technical", "Performing technical analysis...", 
             lambda: self.analyze_technicals(ticker, company_name, price_data)),
        ]
        
        # Run main analyses
        for key, message, func in steps:
            if progress_callback:
                progress_callback(message)
            try:
                results[key] = func()
            except Exception as e:
                results[key] = f"[Analysis failed: {str(e)}]"
        
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
        
        supplemental_combined = "\n\n".join(supplemental_outputs) if supplemental_outputs else "No supplemental materials provided."
        results["supplemental"] = supplemental_combined
        
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
