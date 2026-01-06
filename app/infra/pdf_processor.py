"""
Procesador de PDFs con streaming real usando pypdf.
Más compatible que PyMuPDF con diferentes tipos de PDFs.
"""
from pypdf import PdfReader
from typing import List, Dict, Any, Generator
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class PdfProcessor:
    """
    Procesador de PDFs optimizado para streaming con pypdf.
    """
    
    def extract_pages_streaming(self, pdf_file_or_bytes) -> Generator[Dict, None, None]:
        """
        Extraer páginas una por una (verdadero streaming).
        
        Args:
            pdf_file_or_bytes: GridFS file object o bytes del PDF
        
        Yields:
            Dict con información de cada página
        """
        # Si es GridFS file, leer bytes
        if hasattr(pdf_file_or_bytes, 'read'):
            pdf_bytes = pdf_file_or_bytes.read()
        else:
            pdf_bytes = pdf_file_or_bytes
        
        # Abrir PDF con pypdf
        reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        
        logger.info(f"📄 PDF opened: {total_pages} pages")
        
        # Procesar página por página
        for page_num, page in enumerate(reader.pages, start=1):
            # Extraer texto de esta página
            page_text = page.extract_text()
            
            # Metadata de la página
            page_box = page.mediabox
            page_metadata = {
                'width': float(page_box.width),
                'height': float(page_box.height),
                'page_number': page_num,
                'total_pages': total_pages,
            }
            
            # Log para diagnóstico
            text_len = len(page_text) if page_text else 0
            logger.debug(f"Page {page_num}: {text_len} chars")
            
            yield {
                'page_number': page_num,
                'total_pages': total_pages,
                'text': page_text or "",  # Asegurar que nunca sea None
                'metadata': page_metadata
            }
            
            # Liberar página
            del page_text
        
        # Liberar PDF
        del pdf_bytes
        import gc
        gc.collect()
    
    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extraer todo el texto del PDF (legacy).
        """
        text_parts = []
        
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            logger.info(f"📄 Processing PDF with {len(reader.pages)} pages")
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                if text:
                    text_parts.append(f"\n--- Página {page_num} ---\n")
                    text_parts.append(text)
            
            logger.info(f"✅ Extracted text from {len(reader.pages)} pages")
        
        except Exception as e:
            logger.error(f"❌ Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to process PDF: {str(e)}")
        
        return "\n".join(text_parts)
    
    def extract_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extraer metadatos del PDF.
        """
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            metadata = reader.metadata
            
            return {
                "pages": len(reader.pages),
                "title": metadata.get("/Title"),
                "author": metadata.get("/Author"),
                "subject": metadata.get("/Subject"),
                "creator": metadata.get("/Creator"),
                "producer": metadata.get("/Producer"),
            }
        
        except Exception as e:
            logger.error(f"❌ Error extracting metadata: {e}")
            return {"pages": 0}
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Dividir texto en chunks de tamaño aproximado.
        """
        if not text or not text.strip():
            logger.warning("⚠️  Empty text received for chunking")
            return []
        
        # Aproximación: 1 token ≈ 4 caracteres
        chars_per_chunk = chunk_size * 4
        
        # Dividir por párrafos primero
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            para_size = len(paragraph)
            
            # Si el párrafo solo excede el tamaño
            if para_size > chars_per_chunk:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Dividir párrafo largo por oraciones
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if current_size + len(sentence) > chars_per_chunk:
                        if current_chunk:
                            chunks.append('\n\n'.join(current_chunk))
                        current_chunk = [sentence]
                        current_size = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_size += len(sentence)
            
            # Si agregar el párrafo excede el tamaño
            elif current_size + para_size > chars_per_chunk:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = para_size
            
            # Agregar párrafo al chunk actual
            else:
                current_chunk.append(paragraph)
                current_size += para_size
        
        # Agregar último chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        logger.info(f"📦 Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
