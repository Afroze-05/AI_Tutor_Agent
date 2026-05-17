"""
File Loader Utilities for RAG System
Supports PDF, DOCX, and TXT files
"""
import fitz  # PyMuPDF
import docx
from typing import Optional, Dict, Any
import os


class FileLoader:
    """Handles loading and extracting text from various file types"""
    
    @staticmethod
    def load_pdf(file_path: str) -> Dict[str, Any]:
        """
        Load and extract text from PDF file using PyMuPDF
        Returns text with page numbers
        """
        try:
            doc = fitz.open(file_path)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    text_content.append({
                        'text': text.strip(),
                        'page': page_num + 1,
                        'filename': os.path.basename(file_path)
                    })
            
            doc.close()
            return {
                'success': True,
                'content': text_content,
                'total_pages': len(text_content)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"PDF loading error: {str(e)}"
            }
    
    @staticmethod
    def load_docx(file_path: str) -> Dict[str, Any]:
        """
        Load and extract text from DOCX file
        Returns text with paragraph structure
        """
        try:
            doc = docx.Document(file_path)
            text_content = []
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text:
                    text_content.append({
                        'text': text,
                        'paragraph': para_num + 1,
                        'filename': os.path.basename(file_path)
                    })
            
            return {
                'success': True,
                'content': text_content,
                'total_paragraphs': len(text_content)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"DOCX loading error: {str(e)}"
            }
    
    @staticmethod
    def load_txt(file_path: str) -> Dict[str, Any]:
        """
        Load and extract text from TXT file
        Returns text with line structure
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            text_content = []
            for line_num, line in enumerate(lines):
                text = line.strip()
                if text:
                    text_content.append({
                        'text': text,
                        'line': line_num + 1,
                        'filename': os.path.basename(file_path)
                    })
            
            return {
                'success': True,
                'content': text_content,
                'total_lines': len(text_content)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"TXT loading error: {str(e)}"
            }
    
    @classmethod
    def load_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Main method to load any supported file type
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f"File not found: {file_path}"
            }
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return cls.load_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return cls.load_docx(file_path)
        elif file_extension == '.txt':
            return cls.load_txt(file_path)
        else:
            return {
                'success': False,
                'error': f"Unsupported file type: {file_extension}"
            }
    
    @staticmethod
    def get_supported_extensions() -> list:
        """Returns list of supported file extensions"""
        return ['.pdf', '.docx', '.doc', '.txt']
