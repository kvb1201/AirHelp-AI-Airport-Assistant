"""
OCR API Endpoint
Handles boarding pass image processing and text extraction
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
from datetime import datetime

from app.services.simple_ocr_service import extract_boarding_pass_simple, simple_boarding_pass_ocr
from app.utils.logger import logger

router = APIRouter()

class BoardingPassResponse(BaseModel):
    """Response model for boarding pass extraction."""
    success: bool
    data: dict
    message: str
    timestamp: str
    confidence: float

class OCRResponse(BaseModel):
    """Response model for general OCR processing."""
    success: bool
    extracted_text: str
    structured_data: dict
    message: str
    timestamp: str

@router.post("/ocr/boarding-pass", response_model=BoardingPassResponse)
async def extract_boarding_pass_endpoint(
    file: UploadFile = File(...),
    return_raw_text: bool = Form(False)
):
    """
    Extract boarding pass information from uploaded image.
    
    Args:
        file: Image file of boarding pass
        return_raw_text: Whether to return raw OCR text
        
    Returns:
        Structured boarding pass information
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type, image expected.")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        image_path = tmp.name
    
    try:
        # Extract boarding pass information
        result = extract_boarding_pass_simple(image_path)
        
        # Clean up temp file
        os.unlink(image_path)
        
        if 'error' in result:
            return BoardingPassResponse(
                success=False,
                data={},
                message=f"OCR extraction failed: {result['error']}",
                timestamp=result['timestamp'],
                confidence=result.get('confidence', 0.0)
            )
        
        # Prepare response data
        response_data = {
            'flight_number': result.get('flight_number'),
            'passenger_name': result.get('passenger_name'),
            'from_to': result.get('from_to'),
            'date': result.get('date'),
            'departure_time': result.get('departure_time'),
            'gate': result.get('gate'),
            'seat': result.get('seat'),
            'terminal': result.get('terminal'),
            'boarding_time': result.get('boarding_time'),
        }
        
        # Add raw text if requested
        if return_raw_text:
            response_data['raw_text'] = result.get('raw_text', '')
        
        return BoardingPassResponse(
            success=True,
            data=response_data,
            message="Boarding pass extracted successfully",
            timestamp=result['timestamp'],
            confidence=result.get('confidence', 0.0)
        )
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(image_path):
            os.unlink(image_path)
        
        logger.error(f"Boarding pass OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@router.post("/ocr/general", response_model=OCRResponse)
async def general_ocr_endpoint(
    file: UploadFile = File(...),
    extract_structured: bool = Form(True)
):
    """
    General OCR endpoint for any image text extraction.
    
    Args:
        file: Image file to process
        extract_structured: Whether to attempt structured data extraction
        
    Returns:
        Extracted text and structured data
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type, image expected.")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        image_path = tmp.name
    
    try:
        # Extract text using OCR service
        result = simple_boarding_pass_ocr.extract_boarding_pass_info(image_path)
        
        # Clean up temp file
        os.unlink(image_path)
        
        if 'error' in result:
            return OCRResponse(
                success=False,
                extracted_text="",
                structured_data={},
                message=f"OCR extraction failed: {result['error']}",
                timestamp=result['timestamp']
            )
        
        # Prepare structured data if requested
        structured_data = {}
        if extract_structured:
            # Try to extract common patterns
            text = result.get('raw_text', '')
            structured_data = {
                'flight_number': boarding_pass_ocr.extract_field(text, 'flight_number'),
                'dates': boarding_pass_ocr.extract_field(text, 'date'),
                'times': boarding_pass_ocr.extract_field(text, 'time'),
                'locations': boarding_pass_ocr.extract_field(text, 'from_to'),
                'gates': boarding_pass_ocr.extract_field(text, 'gate'),
                'seats': boarding_pass_ocr.extract_field(text, 'seat')
            }
            # Remove None values
            structured_data = {k: v for k, v in structured_data.items() if v is not None}
        
        return OCRResponse(
            success=True,
            extracted_text=result.get('raw_text', ''),
            structured_data=structured_data,
            message="Text extracted successfully",
            timestamp=result['timestamp']
        )
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(image_path):
            os.unlink(image_path)
        
        logger.error(f"General OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@router.post("/ocr/batch")
async def batch_ocr_endpoint(
    files: List[UploadFile] = File(...),
    extract_boarding_passes: bool = Form(True)
):
    """
    Process multiple images in batch.
    
    Args:
        files: List of image files
        extract_boarding_passes: Whether to extract boarding pass info
        
    Returns:
        List of extraction results
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    temp_files = []
    
    try:
        # Save all files temporarily
        for file in files:
            if not file.content_type.startswith("image/"):
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Invalid file type, image expected'
                })
                continue
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                content = await file.read()
                tmp.write(content)
                temp_files.append(tmp.name)
                
                # Process the file
                try:
                    if extract_boarding_passes:
                        result = extract_boarding_pass_simple(tmp.name)
                    else:
                        result = simple_boarding_pass_ocr.extract_boarding_pass_info(tmp.name)
                    
                    results.append({
                        'filename': file.filename,
                        'success': 'error' not in result,
                        'data': result,
                        'confidence': result.get('confidence', 0.0)
                    })
                except Exception as e:
                    logger.error(f"Failed to process {file.filename}: {e}")
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    })
        
        return {
            'success': True,
            'results': results,
            'processed': len(results),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")
    
    finally:
        # Clean up all temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")

@router.get("/ocr/status")
async def ocr_status():
    """Check OCR service status."""
    return {
        'status': 'active',
        'service': 'Boarding Pass OCR',
        'supported_formats': ['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        'features': [
            'boarding_pass_extraction',
            'general_text_extraction',
            'batch_processing',
            'structured_data_extraction'
        ],
        'timestamp': datetime.now().isoformat()
    }
