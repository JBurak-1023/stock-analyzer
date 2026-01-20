"""
Report Generator Module

Assembles the final report in HTML format and optionally exports to PDF.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import re


class ReportGenerator:
    """Generates formatted HTML reports from analysis outputs."""

    def __init__(self, ticker: str, company_name: str):
        """
        Initialize the report generator.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
        """
        self.ticker = ticker.upper()
        self.company_name = company_name

    def markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert markdown text to HTML.
        
        Simple conversion for common markdown elements.
        
        Args:
            markdown_text: Markdown formatted text
            
        Returns:
            HTML formatted text
        """
        html = markdown_text
        
        # Headers
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        
        # Bullet lists - handle nested
        lines = html.split("\n")
        in_list = False
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                if not in_list:
                    new_lines.append("<ul>")
                    in_list = True
                new_lines.append(f"<li>{stripped[2:]}</li>")
            else:
                if in_list:
                    new_lines.append("</ul>")
                    in_list = False
                new_lines.append(line)
        
        if in_list:
            new_lines.append("</ul>")
        
        html = "\n".join(new_lines)
        
        # Tables
        html = self._convert_tables(html)
        
        # Horizontal rules
        html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)
        
        # Paragraphs - wrap non-tagged text blocks
        paragraphs = html.split("\n\n")
        formatted_paragraphs = []
        
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith("<"):
                # Check if it's a single line that might be part of a list or header
                if not any(p.startswith(tag) for tag in ["<h", "<ul", "<ol", "<li", "<table", "<hr"]):
                    p = f"<p>{p}</p>"
            formatted_paragraphs.append(p)
        
        html = "\n\n".join(formatted_paragraphs)
        
        return html

    def _convert_tables(self, text: str) -> str:
        """Convert markdown tables to HTML tables."""
        lines = text.split("\n")
        result = []
        table_lines = []
        in_table = False
        
        for line in lines:
            # Check if this looks like a table row
            if "|" in line and line.strip().startswith("|"):
                in_table = True
                table_lines.append(line)
            else:
                if in_table:
                    # Process collected table
                    result.append(self._process_table(table_lines))
                    table_lines = []
                    in_table = False
                result.append(line)
        
        # Handle table at end of text
        if in_table and table_lines:
            result.append(self._process_table(table_lines))
        
        return "\n".join(result)

    def _process_table(self, lines: list) -> str:
        """Convert markdown table lines to HTML table."""
        if not lines:
            return ""
        
        html_lines = ['<table class="data-table">']
        
        for i, line in enumerate(lines):
            # Skip separator line (|---|---|)
            if re.match(r"^\|[-:\s|]+\|$", line.strip()):
                continue
            
            cells = [c.strip() for c in line.split("|")[1:-1]]
            
            if i == 0:
                html_lines.append("<thead><tr>")
                for cell in cells:
                    html_lines.append(f"<th>{cell}</th>")
                html_lines.append("</tr></thead><tbody>")
            else:
                html_lines.append("<tr>")
                for cell in cells:
                    html_lines.append(f"<td>{cell}</td>")
                html_lines.append("</tr>")
        
        html_lines.append("</tbody></table>")
        return "\n".join(html_lines)

    def generate_html_report(
        self,
        report_content: str,
        chart_html: Optional[str] = None,
        include_styles: bool = True,
    ) -> str:
        """
        Generate a complete HTML report.
        
        Args:
            report_content: The synthesized report content (markdown)
            chart_html: Optional Plotly chart HTML to embed
            include_styles: Whether to include CSS styles
            
        Returns:
            Complete HTML document
        """
        # Convert markdown to HTML
        content_html = self.markdown_to_html(report_content)
        
        # Insert chart if provided
        if chart_html:
            # Find the Technical Analysis section and insert chart after TA Grade
            chart_placeholder = "[Note: Chart will be inserted separately]"
            if chart_placeholder in content_html:
                content_html = content_html.replace(
                    chart_placeholder,
                    f'<div class="chart-container">{chart_html}</div>'
                )
            else:
                # Try to insert after Technical Analysis section
                ta_marker = "Technical Analysis"
                if ta_marker in content_html:
                    # Insert chart div after the section
                    insert_pos = content_html.find("</h2>", content_html.find(ta_marker))
                    if insert_pos > 0:
                        content_html = (
                            content_html[:insert_pos + 5] +
                            f'\n<div class="chart-container">{chart_html}</div>\n' +
                            content_html[insert_pos + 5:]
                        )
        
        styles = self._get_styles() if include_styles else ""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.company_name} ({self.ticker}) - Stock Analysis Report</title>
    {styles}
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <h1>{self.company_name} ({self.ticker})</h1>
            <p class="report-date">Report Generated: {datetime.now().strftime("%B %d, %Y")}</p>
        </header>
        
        <main class="report-content">
            {content_html}
        </main>
        
        <footer class="report-footer">
            <p>Generated by Stock Analysis Report Generator</p>
            <p class="disclaimer">This report is for informational purposes only and does not constitute investment advice.</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html

    def _get_styles(self) -> str:
        """Get CSS styles for the report."""
        return """
    <style>
        :root {
            --primary-color: #1a365d;
            --secondary-color: #2c5282;
            --accent-color: #3182ce;
            --success-color: #38a169;
            --warning-color: #d69e2e;
            --danger-color: #e53e3e;
            --text-color: #2d3748;
            --light-bg: #f7fafc;
            --border-color: #e2e8f0;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-color);
            background-color: #fff;
        }
        
        .report-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
        }
        
        .report-header {
            text-align: center;
            padding-bottom: 30px;
            border-bottom: 3px solid var(--primary-color);
            margin-bottom: 30px;
        }
        
        .report-header h1 {
            font-size: 28px;
            color: var(--primary-color);
            margin-bottom: 10px;
        }
        
        .report-date {
            color: #718096;
            font-size: 14px;
        }
        
        h1 { font-size: 24px; color: var(--primary-color); margin: 30px 0 15px 0; }
        h2 { font-size: 20px; color: var(--secondary-color); margin: 25px 0 15px 0; border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }
        h3 { font-size: 16px; color: var(--text-color); margin: 20px 0 10px 0; }
        
        p {
            margin-bottom: 12px;
        }
        
        strong {
            color: var(--primary-color);
        }
        
        ul {
            margin: 15px 0;
            padding-left: 25px;
        }
        
        li {
            margin-bottom: 8px;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
        }
        
        .data-table th,
        .data-table td {
            padding: 10px 12px;
            text-align: left;
            border: 1px solid var(--border-color);
        }
        
        .data-table th {
            background-color: var(--light-bg);
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .data-table tr:nth-child(even) {
            background-color: #fafafa;
        }
        
        .chart-container {
            margin: 25px 0;
            padding: 15px;
            background-color: var(--light-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 30px 0;
        }
        
        .report-footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: #718096;
            font-size: 12px;
        }
        
        .disclaimer {
            font-style: italic;
            margin-top: 10px;
        }
        
        /* Grade styling */
        .grade-a { color: var(--success-color); font-weight: bold; }
        .grade-b { color: #48bb78; font-weight: bold; }
        .grade-c { color: var(--warning-color); font-weight: bold; }
        .grade-d { color: #ed8936; font-weight: bold; }
        .grade-f { color: var(--danger-color); font-weight: bold; }
        
        /* Print styles */
        @media print {
            body {
                font-size: 11px;
            }
            
            .report-container {
                max-width: 100%;
                padding: 20px;
            }
            
            .chart-container {
                page-break-inside: avoid;
            }
            
            h2 {
                page-break-after: avoid;
            }
        }
    </style>"""

    def export_to_pdf(self, html_content: str, output_path: str) -> bool:
        """
        Export HTML report to PDF.
        
        Args:
            html_content: Complete HTML document
            output_path: Path for output PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from weasyprint import HTML, CSS
            
            # Create PDF from HTML
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(output_path)
            
            return True
            
        except ImportError:
            print("WeasyPrint not installed. Cannot export to PDF.")
            return False
        except Exception as e:
            print(f"Error exporting to PDF: {e}")
            return False

    def generate_report_for_streamlit(
        self,
        report_content: str,
        chart_figure=None,
    ) -> Dict[str, Any]:
        """
        Generate report components for Streamlit display.
        
        Args:
            report_content: The synthesized report content
            chart_figure: Optional Plotly figure object
            
        Returns:
            Dictionary with 'html' and 'chart' keys for Streamlit rendering
        """
        # Get chart HTML if figure provided
        chart_html = None
        if chart_figure is not None:
            try:
                chart_html = chart_figure.to_html(
                    include_plotlyjs="cdn",
                    full_html=False,
                    config={"responsive": True}
                )
            except Exception as e:
                print(f"Error converting chart to HTML: {e}")
        
        # Generate full HTML
        html = self.generate_html_report(report_content, chart_html)
        
        return {
            "html": html,
            "chart": chart_figure,
            "markdown": report_content,
        }
