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

from app.services.offline_ocr_service import extract_boarding_pass_offline, offline_boarding_pass_ocr
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
    image_path = None
    
    try:
        logger.info(f"📷 Boarding pass upload started: {file.filename}, type: {file.content_type}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            logger.warning(f"Invalid file type: {file.content_type}")
            return BoardingPassResponse(
                success=False,
                data={},
                message=f"Invalid file type '{file.content_type}'. Please upload an image file.",
                timestamp=datetime.now().isoformat(),
                confidence=0.0
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            logger.info(f"📷 File read: {len(content)} bytes")
            tmp.write(content)
            image_path = tmp.name
        
        logger.info(f"📷 Temp file created: {image_path}")
        
        # Extract boarding pass information
        logger.info("📷 Starting OCR extraction...")
        result = extract_boarding_pass_offline(image_path)
        logger.info(f"📷 OCR extraction complete: {result.get('success', False)}")
        
        # Clean up temp file
        if image_path and os.path.exists(image_path):
            os.unlink(image_path)
            logger.info("📷 Temp file cleaned up")
        
        if 'error' in result:
            logger.warning(f"📷 OCR extraction failed: {result['error']}")
            return BoardingPassResponse(
                success=False,
                data={},
                message=f"OCR extraction failed: {result['error']}",
                timestamp=result.get('timestamp', datetime.now().isoformat()),
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
        
        logger.info(f"📷 Boarding pass extracted successfully: flight={response_data.get('flight_number')}, gate={response_data.get('gate')}")
        
        response_obj = BoardingPassResponse(
            success=True,
            data=response_data,
            message="Boarding pass extracted successfully",
            timestamp=result.get('timestamp', datetime.now().isoformat()),
            confidence=result.get('confidence', 0.0)
        )
        
        logger.info(f"📷 Returning response: success={response_obj.success}, data_keys={list(response_obj.data.keys())}")
        
        return response_obj
        
    except Exception as e:
        # Clean up temp file on error
        if image_path and os.path.exists(image_path):
            try:
                os.unlink(image_path)
                logger.info("📷 Temp file cleaned up after error")
            except Exception as cleanup_error:
                logger.warning(f"📷 Failed to cleanup temp file: {cleanup_error}")
        
        logger.error(f"📷 Boarding pass OCR failed with exception: {e}", exc_info=True)
        
        # CRITICAL: Return JSON response instead of raising HTTPException
        error_response = BoardingPassResponse(
            success=False,
            data={},
            message=f"OCR processing failed: {str(e)}",
            timestamp=datetime.now().isoformat(),
            confidence=0.0
        )
        
        logger.info(f"📷 Returning error response: {error_response.message}")
        
        return error_response

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
        result = offline_boarding_pass_ocr.extract_boarding_pass_info(image_path)
        
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
                'flight_number': offline_boarding_pass_ocr.extract_field(text, 'flight_number'),
                'dates': offline_boarding_pass_ocr.extract_field(text, 'date'),
                'times': offline_boarding_pass_ocr.extract_field(text, 'time'),
                'locations': offline_boarding_pass_ocr.extract_field(text, 'from_to'),
                'gates': offline_boarding_pass_ocr.extract_field(text, 'gate'),
                'seats': offline_boarding_pass_ocr.extract_field(text, 'seat')
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
                        result = extract_boarding_pass_offline(tmp.name)
                    else:
                        result = offline_boarding_pass_ocr.extract_boarding_pass_info(tmp.name)
                    
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
        'mode': 'offline',
        'supported_formats': offline_boarding_pass_ocr.get_supported_formats(),
        'features': [
            'boarding_pass_extraction',
            'general_text_extraction',
            'batch_processing',
            'structured_data_extraction',
            'completely_offline'
        ],
        'offline_mode': offline_boarding_pass_ocr.is_offline_mode(),
        'timestamp': datetime.now().isoformat()
    }
