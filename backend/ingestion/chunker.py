import re
from typing import List, Dict, Any

class DocumentChunker:
    """
    Chunks document pages into overlapping passages while strictly preserving:
    - page_number
    - section_title
    - start_char and end_char offsets
    - token counts
    """

    def __init__(self, target_chars: int = 1200, overlap_chars: int = 200):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    def chunk_document(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        global_chunk_idx = 0

        for page in parsed_data.get('pages', []):
            page_num = page['page_number']
            page_text = page['text']
            sections = page.get('sections', [{'section_title': 'General', 'char_offset': 0}])

            if not page_text.strip():
                continue

            # Split by paragraph / double newline or sentence boundaries
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', page_text) if p.strip()]
            if not paragraphs:
                paragraphs = [page_text]

            current_chunk_text = ""
            current_start_offset = 0
            page_offset = 0

            for para in paragraphs:
                para_pos = page_text.find(para, page_offset)
                if para_pos == -1:
                    para_pos = page_offset
                page_offset = para_pos + len(para)

                if not current_chunk_text:
                    current_chunk_text = para
                    current_start_offset = para_pos
                elif len(current_chunk_text) + len(para) + 2 <= self.target_chars:
                    current_chunk_text += "\n\n" + para
                else:
                    # Determine section title for this offset
                    section_title = self._get_section_for_offset(sections, current_start_offset)
                    end_offset = current_start_offset + len(current_chunk_text)

                    chunks.append({
                        'chunk_index': global_chunk_idx,
                        'page_number': page_num,
                        'section_title': section_title,
                        'text': current_chunk_text,
                        'start_char': current_start_offset,
                        'end_char': end_offset,
                        'token_count': len(current_chunk_text.split()),
                        'metadata': {
                            'page': page_num,
                            'section': section_title,
                            'char_length': len(current_chunk_text),
                        }
                    })
                    global_chunk_idx += 1

                    # Slide window with overlap
                    overlap_text = current_chunk_text[-self.overlap_chars:] if len(current_chunk_text) > self.overlap_chars else ""
                    current_chunk_text = (overlap_text + "\n\n" + para).strip()
                    current_start_offset = max(0, para_pos - len(overlap_text))

            if current_chunk_text.strip():
                section_title = self._get_section_for_offset(sections, current_start_offset)
                end_offset = current_start_offset + len(current_chunk_text)
                chunks.append({
                    'chunk_index': global_chunk_idx,
                    'page_number': page_num,
                    'section_title': section_title,
                    'text': current_chunk_text,
                    'start_char': current_start_offset,
                    'end_char': end_offset,
                    'token_count': len(current_chunk_text.split()),
                    'metadata': {
                        'page': page_num,
                        'section': section_title,
                        'char_length': len(current_chunk_text),
                    }
                })
                global_chunk_idx += 1

        return chunks

    def _get_section_for_offset(self, sections: List[Dict[str, Any]], offset: int) -> str:
        current_section = "General"
        for s in sections:
            if offset >= s.get('char_offset', 0):
                current_section = s.get('section_title', current_section)
            else:
                break
        return current_section
