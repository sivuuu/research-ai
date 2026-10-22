import os
import re
from typing import Dict, List, Any, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class DocumentParser:
    """Extracts text, section headings, and metadata from research documents."""

    SECTION_HEADER_REGEX = re.compile(
        r'^(?:(?:\d+\.|\d+\.\d+|[I|V|X]+\.)\s+)?([A-Z][A-Za-z0-9\s,\-–:]{2,60})$'
    )

    @classmethod
    def parse(cls, file_path: str, file_type: str = 'pdf') -> Dict[str, Any]:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.pdf' or file_type == 'pdf':
            return cls._parse_pdf(file_path)
        else:
            return cls._parse_text(file_path)

    @classmethod
    def _parse_pdf(cls, file_path: str) -> Dict[str, Any]:
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")

        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_data = []

        # Extract PDF metadata if present
        pdf_meta = doc.metadata or {}
        raw_title = (pdf_meta.get('title') or '').strip()
        raw_author = (pdf_meta.get('author') or '').strip()
        raw_creation_date = (pdf_meta.get('creationDate') or '').strip()

        title = None
        authors = []
        abstract = ""

        # Filter out generic placeholder titles like "Untitled" or PDF software names
        if raw_title and len(raw_title) > 3 and not raw_title.lower().startswith(('untitled', 'microsoft word', 'latex')):
            title = raw_title

        if raw_author and len(raw_author) > 2:
            # Authors can be comma or semicolon separated
            authors = [a.strip() for a in re.split(r'[,;]|\band\b', raw_author) if a.strip()]

        current_section = "Introduction"

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text("text")

            # Try to infer title & abstract from page 1 if metadata was missing
            if page_idx == 0:
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if not title and lines:
                    # Often the first non-empty lines are the title
                    title_candidate = lines[0]
                    if len(lines) > 1 and len(lines[0]) < 40 and not lines[0].lower().startswith('arxiv'):
                        title_candidate = f"{lines[0]} {lines[1]}"
                    title = title_candidate

                # Look for Abstract
                abstract_match = re.search(r'abstract[\s:—\-]*(.*?)(?:1\.?\s+|introduction|\n\n[A-Z0-9])', text, re.IGNORECASE | re.DOTALL)
                if abstract_match:
                    abstract = abstract_match.group(1).strip()
                    abstract = re.sub(r'\s+', ' ', abstract)[:1500]

            # Detect sections within the page
            page_sections = cls._extract_page_sections(text, default_section=current_section)
            if page_sections:
                current_section = page_sections[-1]['section_title']

            pages_data.append({
                'page_number': page_num,
                'text': text,
                'sections': page_sections,
            })

        doc.close()

        # If title still not determined, use basename without extension
        if not title:
            base = os.path.basename(file_path)
            title = os.path.splitext(base)[0].replace('_', ' ').replace('-', ' ').title()

        return {
            'title': title,
            'authors': authors,  # Empty if unavailable - never invented
            'publication_date': None,  # Marked None if unavailable
            'publication_details': pdf_meta.get('subject') or None,
            'abstract': abstract,
            'total_pages': total_pages,
            'pages': pages_data,
        }

    @classmethod
    def _parse_text(cls, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        lines = [line.strip() for line in content.split('\n') if line.strip()]
        title = lines[0] if lines else os.path.basename(file_path)
        authors = []
        abstract = ""

        # Check for header metadata like "Title: ... Authors: ..."
        title_m = re.search(r'^Title:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if title_m:
            title = title_m.group(1).strip()

        authors_m = re.search(r'^Authors?:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if authors_m:
            authors = [a.strip() for a in re.split(r'[,;]|\band\b', authors_m.group(1)) if a.strip()]

        abstract_m = re.search(r'abstract[\s:—\-]*(.*?)(?:1\.?\s+|introduction|\n\n[#A-Z0-9])', content, re.IGNORECASE | re.DOTALL)
        if abstract_m:
            abstract = re.sub(r'\s+', ' ', abstract_m.group(1).strip())[:1500]

        # Break text into synthetic pages (~3000 chars per page)
        page_size = 3000
        total_pages = max(1, (len(content) + page_size - 1) // page_size)
        pages_data = []

        for p in range(total_pages):
            start = p * page_size
            end = min(len(content), (p + 1) * page_size)
            page_text = content[start:end]
            sections = cls._extract_page_sections(page_text, default_section="Overview")
            pages_data.append({
                'page_number': p + 1,
                'text': page_text,
                'sections': sections,
            })

        return {
            'title': title,
            'authors': authors,
            'publication_date': None,
            'publication_details': None,
            'abstract': abstract,
            'total_pages': total_pages,
            'pages': pages_data,
        }

    @classmethod
    def _extract_page_sections(cls, text: str, default_section: str = "General") -> List[Dict[str, Any]]:
        sections = []
        lines = text.split('\n')
        char_pos = 0

        for line in lines:
            trimmed = line.strip()
            if cls.SECTION_HEADER_REGEX.match(trimmed) and len(trimmed) < 60:
                sections.append({
                    'section_title': trimmed,
                    'char_offset': char_pos,
                })
            char_pos += len(line) + 1

        if not sections:
            sections.append({
                'section_title': default_section,
                'char_offset': 0,
            })
        return sections
