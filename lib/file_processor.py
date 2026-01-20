"""
File Processor Module

Handles extraction of content from various file types:
- PDFs: Extract text
- Images: Return bytes for vision analysis
- CSV/Excel: Parse and summarize
- Text files: Read content
"""

import io
from typing import Dict, Any, Optional, Union, BinaryIO
from pathlib import Path


class FileProcessor:
    """Processes uploaded files for LLM analysis."""

    SUPPORTED_EXTENSIONS = {
        "pdf": "document",
        "png": "image",
        "jpg": "image",
        "jpeg": "image",
        "gif": "image",
        "webp": "image",
        "csv": "data",
        "xlsx": "data",
        "xls": "data",
        "txt": "text",
        "md": "text",
    }

    IMAGE_MIME_TYPES = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }

    def __init__(self):
        """Initialize the file processor."""
        pass

    def get_file_type(self, filename: str) -> Optional[str]:
        """
        Determine the type category of a file.
        
        Args:
            filename: Name of the file
            
        Returns:
            Type category ('document', 'image', 'data', 'text') or None
        """
        ext = Path(filename).suffix.lower().lstrip(".")
        return self.SUPPORTED_EXTENSIONS.get(ext)

    def process_file(
        self, file_content: Union[bytes, BinaryIO], filename: str
    ) -> Dict[str, Any]:
        """
        Process an uploaded file and extract content.
        
        Args:
            file_content: File content as bytes or file-like object
            filename: Name of the file
            
        Returns:
            Dictionary with:
                - name: filename
                - type: 'text', 'image', or 'data'
                - content: extracted content (text string or image bytes)
                - media_type: MIME type for images
                - error: error message if processing failed
        """
        result = {"name": filename, "type": None, "content": None}
        
        # Convert to bytes if needed
        if hasattr(file_content, "read"):
            file_bytes = file_content.read()
            if hasattr(file_content, "seek"):
                file_content.seek(0)  # Reset for potential re-read
        else:
            file_bytes = file_content
        
        ext = Path(filename).suffix.lower().lstrip(".")
        file_type = self.get_file_type(filename)
        
        if file_type is None:
            result["error"] = f"Unsupported file type: .{ext}"
            return result
        
        try:
            if file_type == "document":
                result["type"] = "text"
                result["content"] = self._extract_pdf_text(file_bytes)
            
            elif file_type == "image":
                result["type"] = "image"
                result["content"] = file_bytes
                result["media_type"] = self.IMAGE_MIME_TYPES.get(ext, "image/png")
            
            elif file_type == "data":
                result["type"] = "text"
                if ext == "csv":
                    result["content"] = self._extract_csv_text(file_bytes)
                else:
                    result["content"] = self._extract_excel_text(file_bytes)
            
            elif file_type == "text":
                result["type"] = "text"
                result["content"] = file_bytes.decode("utf-8", errors="replace")
            
        except Exception as e:
            result["error"] = f"Error processing file: {str(e)}"
        
        return result

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_bytes: PDF file content
            
        Returns:
            Extracted text
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
            
            if not text_parts:
                return "[PDF contained no extractable text. It may be image-based.]"
            
            return "\n\n".join(text_parts)
            
        except ImportError:
            return "[PyPDF2 not installed. Cannot extract PDF text.]"
        except Exception as e:
            return f"[Error extracting PDF text: {str(e)}]"

    def _extract_csv_text(self, file_bytes: bytes) -> str:
        """
        Extract and summarize CSV content.
        
        Args:
            file_bytes: CSV file content
            
        Returns:
            Formatted summary of CSV data
        """
        try:
            import pandas as pd
            
            df = pd.read_csv(io.BytesIO(file_bytes))
            
            lines = [
                f"CSV Data Summary",
                f"Rows: {len(df)}",
                f"Columns: {len(df.columns)}",
                f"Column names: {', '.join(df.columns.tolist())}",
                "",
                "Data types:",
            ]
            
            for col in df.columns:
                lines.append(f"  {col}: {df[col].dtype}")
            
            lines.extend([
                "",
                "First 10 rows:",
                df.head(10).to_string(),
            ])
            
            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                lines.extend([
                    "",
                    "Numeric column statistics:",
                    df[numeric_cols].describe().to_string(),
                ])
            
            return "\n".join(lines)
            
        except ImportError:
            return "[pandas not installed. Cannot process CSV.]"
        except Exception as e:
            return f"[Error processing CSV: {str(e)}]"

    def _extract_excel_text(self, file_bytes: bytes) -> str:
        """
        Extract and summarize Excel content.
        
        Args:
            file_bytes: Excel file content
            
        Returns:
            Formatted summary of Excel data
        """
        try:
            import pandas as pd
            
            # Read all sheets
            xlsx = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = xlsx.sheet_names
            
            lines = [
                f"Excel File Summary",
                f"Number of sheets: {len(sheet_names)}",
                f"Sheet names: {', '.join(sheet_names)}",
            ]
            
            for sheet_name in sheet_names:
                df = pd.read_excel(xlsx, sheet_name=sheet_name)
                
                lines.extend([
                    "",
                    f"=== Sheet: {sheet_name} ===",
                    f"Rows: {len(df)}",
                    f"Columns: {len(df.columns)}",
                    f"Column names: {', '.join(df.columns.astype(str).tolist())}",
                    "",
                    "First 10 rows:",
                    df.head(10).to_string(),
                ])
            
            return "\n".join(lines)
            
        except ImportError:
            return "[pandas/openpyxl not installed. Cannot process Excel.]"
        except Exception as e:
            return f"[Error processing Excel: {str(e)}]"

    def process_multiple_files(
        self, files: list
    ) -> list:
        """
        Process multiple files.
        
        Args:
            files: List of tuples (file_content, filename) or Streamlit UploadedFile objects
            
        Returns:
            List of processed file dictionaries
        """
        results = []
        
        for file in files:
            if hasattr(file, "name"):
                # Streamlit UploadedFile object
                result = self.process_file(file.read(), file.name)
                file.seek(0)  # Reset for potential re-read
            else:
                # Tuple of (content, filename)
                content, filename = file
                result = self.process_file(content, filename)
            
            results.append(result)
        
        return results

    def is_supported(self, filename: str) -> bool:
        """
        Check if a file type is supported.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if supported, False otherwise
        """
        return self.get_file_type(filename) is not None

    @classmethod
    def get_supported_extensions(cls) -> list:
        """Get list of supported file extensions."""
        return list(cls.SUPPORTED_EXTENSIONS.keys())
