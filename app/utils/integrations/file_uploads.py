"""
LangGraph Studio File Upload Integration

Optional integration for handling file uploads in LangGraph Studio.
This combines message parsing and file processing for document uploads.

Only used when document upload features are needed in the mortgage workflow.
"""

import base64
import io
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ==== FILE PROCESSING UTILITIES ====

def extract_text_from_data_url(data_url: str) -> Tuple[str, str, str]:
    """
    Extract text content from a data URL (base64 encoded file)
    
    Args:
        data_url: Data URL in format 'data:mime/type;base64,content'
        
    Returns:
        Tuple of (extracted_text, file_type, original_filename)
    """
    try:
        # Parse data URL
        if not data_url.startswith('data:'):
            return data_url, 'text', 'text_input.txt'
            
        # Extract mime type and content
        header, content = data_url.split(',', 1)
        mime_type = header.split(';')[0].replace('data:', '')
        
        # Decode base64 content
        file_bytes = base64.b64decode(content)
        
        # Determine file type and extract text
        if 'pdf' in mime_type.lower():
            return _extract_text_from_pdf_bytes(file_bytes), 'pdf', 'uploaded.pdf'
        elif 'image' in mime_type.lower():
            return _extract_text_from_image_bytes(file_bytes), 'image', 'uploaded.jpg'
        elif 'text' in mime_type.lower():
            return file_bytes.decode('utf-8'), 'text', 'uploaded.txt'
        else:
            # Try to decode as text first
            try:
                return file_bytes.decode('utf-8'), 'text', 'uploaded.txt'
            except:
                return f"[Binary file of type {mime_type}, size {len(file_bytes)} bytes]", 'binary', 'uploaded.bin'
                
    except Exception as e:
        logger.error(f"Error processing data URL: {e}")
        return f"[Error processing file: {str(e)}]", 'error', 'error.txt'


def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using available libraries"""
    try:
        # Try PyPDF2 first
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            return '\n'.join(text_content)
        except ImportError:
            pass
            
        # Try pdfplumber as alternative
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text_content = []
                for page in pdf.pages:
                    text_content.append(page.extract_text() or '')
                return '\n'.join(text_content)
        except ImportError:
            pass
            
        # Fallback - return placeholder text
        return f"[PDF Document - {len(pdf_bytes)} bytes. PDF text extraction libraries not available. Please install PyPDF2 or pdfplumber]"
        
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return f"[PDF Document - Error extracting text: {str(e)}]"


def _extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Extract text from image bytes using OCR with format conversion support"""
    try:
        # Try pytesseract for OCR
        try:
            import pytesseract
            from PIL import Image
            
            # First, try to open and convert image to OCR-compatible format
            try:
                image = Image.open(io.BytesIO(image_bytes))
                
                # Convert unsupported formats (AVIF, HEIC, WebP) to JPEG for OCR
                if hasattr(image, 'format') and image.format in ['AVIF', 'HEIC', 'WEBP']:
                    print(f"🔄 Converting {image.format} format to JPEG for OCR processing")
                    # Convert to RGB if necessary (handles transparency)
                    if image.mode not in ('RGB', 'L'):
                        image = image.convert('RGB')
                    
                    # Save as JPEG in memory
                    jpeg_buffer = io.BytesIO()
                    image.save(jpeg_buffer, format='JPEG', quality=90)
                    jpeg_buffer.seek(0)
                    
                    # Reopen as JPEG
                    image = Image.open(jpeg_buffer)
                    
                elif image.format not in ['JPEG', 'PNG', 'TIFF', 'BMP', 'GIF']:
                    # Handle unknown/unsupported formats
                    print(f"🔄 Converting unknown format to JPEG for OCR processing")
                    if image.mode not in ('RGB', 'L'):
                        image = image.convert('RGB')
                    
                    # Save as JPEG in memory
                    jpeg_buffer = io.BytesIO()
                    image.save(jpeg_buffer, format='JPEG', quality=90)
                    jpeg_buffer.seek(0)
                    
                    # Reopen as JPEG
                    image = Image.open(jpeg_buffer)
                
                # Perform OCR on the (possibly converted) image
                extracted_text = pytesseract.image_to_string(image)
                result_text = extracted_text.strip()
                
                if result_text:
                    print(f"✅ OCR successful: extracted {len(result_text)} characters")
                    return result_text
                else:
                    return "[Image Document - OCR completed but no text detected in image]"
                    
            except Exception as conversion_error:
                # If image processing fails, provide detailed error
                logger.error(f"Image processing/conversion error: {conversion_error}")
                return f"[Image Document - Could not process image format: {str(conversion_error)}]"
                
        except ImportError:
            return f"[Image Document - {len(image_bytes)} bytes. OCR libraries not available. Please install pytesseract and PIL]"
            
    except Exception as e:
        logger.error(f"Error extracting image text: {e}")
        return f"[Image Document - Error extracting text: {str(e)}]"


def parse_multimodal_content(message_content) -> Dict[str, any]:
    """
    Parse LangGraph Studio multimodal message content
    
    Args:
        message_content: Raw content from LangGraph Studio message
        
    Returns:
        Dict with 'text', 'files', and 'has_uploads' keys
    """
    result = {
        'text': '',
        'files': [],
        'has_uploads': False,
        'file_contents': []  # Extracted text content from files
    }
    
    # DEBUG: Minimal logging
    if isinstance(message_content, list):
        image_count = len([item for item in message_content if isinstance(item, dict) and item.get('type') == 'image'])
        if image_count > 0:
            print(f"🔍 Processing {image_count} uploaded images")
    
    try:
        if isinstance(message_content, str):
            # Simple string content
            result['text'] = message_content
            return result
            
        elif isinstance(message_content, list):
            # LangGraph Studio multimodal format
            for item in message_content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        result['text'] += item.get('text', '')
                    elif item.get('type') == 'image':
                        # LangGraph Studio image format detected
                        result['has_uploads'] = True
                        
                        # Extract raw base64 data (no data URL prefix)
                        raw_data = item.get('data', '')
                        
                        if raw_data:
                            # Convert to proper data URL format for processing
                            # Try to determine image type from base64 header
                            if raw_data.startswith('iVBOR'):
                                data_url = f"data:image/png;base64,{raw_data}"
                            elif raw_data.startswith('/9j/'):
                                data_url = f"data:image/jpeg;base64,{raw_data}"  
                            elif raw_data.startswith('AAAA'):
                                # Could be HEIC/AVIF or other format - default to JPEG
                                data_url = f"data:image/jpeg;base64,{raw_data}"
                            else:
                                # Default to JPEG for unknown formats
                                data_url = f"data:image/jpeg;base64,{raw_data}"
                            
                            print(f"🔍 OCR processing image: {len(raw_data)} bytes")
                            
                            # Process the uploaded file
                            extracted_text, file_type, filename = extract_text_from_data_url(data_url)
                            
                            file_info = {
                                'filename': filename,
                                'type': file_type,
                                'size': len(raw_data),
                                'extracted_text': extracted_text
                            }
                            
                            result['files'].append(file_info)
                            result['file_contents'].append(extracted_text)
                            
                            logger.info(f"Processed uploaded file: {filename} ({file_type})")
                    elif 'url' in item or 'image_url' in item:
                        # File upload detected
                        result['has_uploads'] = True
                        
                        # Extract the data URL
                        data_url = item.get('url') or item.get('image_url', {}).get('url', '')
                        
                        if data_url:
                            # Process the uploaded file
                            extracted_text, file_type, filename = extract_text_from_data_url(data_url)
                            
                            file_info = {
                                'filename': filename,
                                'type': file_type,
                                'size': len(data_url),
                                'extracted_text': extracted_text
                            }
                            
                            result['files'].append(file_info)
                            result['file_contents'].append(extracted_text)
                            
                            logger.info(f"Processed uploaded file: {filename} ({file_type})")
                elif isinstance(item, str):
                    result['text'] += item
                    
        else:
            # Fallback - convert to string
            result['text'] = str(message_content)
            
    except Exception as e:
        logger.error(f"Error parsing multimodal content: {e}")
        result['text'] = str(message_content)
        
    return result


# ==== MESSAGE PARSING FOR LANGGRAPH ====

def extract_message_content_and_files(message: Any) -> Dict[str, Any]:
    """
    Extract content and files from LangGraph message - AGENTIC APPROACH
    Exposes file content to agents so they can reason about it
    
    Args:
        message: LangGraph message object
        
    Returns:
        Dict with all content visible to agents for intelligent processing
    """
    
    # Extract raw content from message
    raw_content = None
    if hasattr(message, 'content'):
        raw_content = message.content
    elif isinstance(message, dict):
        raw_content = message.get('content', '')
    else:
        raw_content = str(message)
    
    # DEBUG: Minimal logging for file uploads
    if isinstance(raw_content, list) and any(item.get('type') == 'image' for item in raw_content if isinstance(item, dict)):
        print(f"🔍 File upload detected: {len([item for item in raw_content if isinstance(item, dict) and item.get('type') == 'image'])} files")
    
    # Parse multimodal content
    parsed = parse_multimodal_content(raw_content)
    
    # AGENTIC: Combine all content so agents can see everything and reason
    full_context = parsed['text']
    
    if parsed['has_uploads']:
        full_context += "\n\n📋 **UPLOADED DOCUMENTS:**\n"
        for i, file_info in enumerate(parsed['files'], 1):
            full_context += f"\n**Document {i}: {file_info['filename']}**\n"
            full_context += f"Type: {file_info['type']}\n"
            full_context += f"Content:\n{file_info['extracted_text']}\n"
            full_context += "---\n"
    
    return {
        'full_content': full_context,  # Everything for agent reasoning
        'text_only': parsed['text'],
        'has_files': parsed['has_uploads'],
        'files': parsed['files'],
        'file_count': len(parsed['files']),
        'routing_hint': 'documents' if parsed['has_uploads'] else 'general'
    }


# ==== HELPER UTILITIES ====

def create_document_processing_input(parsed_content: Dict) -> str:
    """
    Create input string for document processing tools from parsed content
    
    Args:
        parsed_content: Result from parse_multimodal_content
        
    Returns:
        Formatted string for document processing tools
    """
    if not parsed_content['has_uploads']:
        return parsed_content['text']
    
    # Format for document processing
    document_sections = []
    
    if parsed_content['text'].strip():
        document_sections.append(f"User Message: {parsed_content['text'].strip()}")
    
    for i, file_info in enumerate(parsed_content['files'], 1):
        document_sections.append(f"""
Document {i}:
- Filename: {file_info['filename']}
- Type: {file_info['type']}
- Content: {file_info['extracted_text'][:2000]}{'...' if len(file_info['extracted_text']) > 2000 else ''}
""")
    
    return '\n'.join(document_sections)


def get_uploaded_files_summary(parsed_content: Dict) -> str:
    """Get a summary of uploaded files for user feedback"""
    if not parsed_content['has_uploads']:
        return ""
    
    summaries = []
    for file_info in parsed_content['files']:
        text_preview = file_info['extracted_text'][:100].replace('\n', ' ')
        summaries.append(f"📄 {file_info['filename']} ({file_info['type']}) - {text_preview}...")
    
    return f"Received {len(parsed_content['files'])} uploaded document(s):\n" + '\n'.join(summaries)
