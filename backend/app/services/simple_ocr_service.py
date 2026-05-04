"""
Simple Boarding Pass OCR Service
Lightweight OCR implementation without pandas dependency
"""

import cv2
import re
from PIL import Image
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.utils.logger import logger

class SimpleBoardingPassOCR:
    """Simplified OCR service for boarding pass extraction."""
    
    def __init__(self):
        logger.info("📷 Simple Boarding Pass OCR Service initialized")
        
        # Common boarding pass patterns for regex matching
        self.patterns = {
            'flight_number': [
                r'FLIGHT\s*NO\.?\s*([A-Z]{2}\s*\d{3,4})',
                r'([A-Z]{2}\s*\d{3,4})',
                r'FLIGHT\s*([A-Z]{2}\d{3,4})',
                r'FLIGHT\s*([A-Z]{2}\s*\d{3,4})'
            ],
            'passenger_name': [
                r'PASSENGER\s*NAME\s*:?([A-Z\s]+)',
                r'NAME\s*:?([A-Z\s]+)',
                r'([A-Z]+\s+[A-Z\s]+)',
                r'MR\/([A-Z\s\/]+)'
            ],
            'from_to': [
                r'FROM\s*:?([A-Z]{3})\s*TO\s*:?([A-Z]{3})',
                r'([A-Z]{3})\s*→\s*([A-Z]{3})',
                r'([A-Z]{3})\s*-\s*([A-Z]{3})'
            ],
            'date': [
                r'DATE\s*:?(\d{1,2}\s*[A-Z]{3}\s*\d{4})',
                r'DATE\s*:?(\d{1,2}\/\d{1,2}\/\d{4})',
                r'(\d{1,2}\s*[A-Z]{3}\s*\d{4})',
                r'(\d{1,2}\/\d{1,2}\/\d{4})'
            ],
            'time': [
                r'TIME\s*:?(\d{1,2}:\d{2})',
                r'DEP\s*:?(\d{1,2}:\d{2})',
                r'(\d{1,2}:\d{2})'
            ],
            'gate': [
                r'GATE\s*:?([A-Z0-9]+)',
                r'GATE\s*([A-Z0-9]+)',
                r'G([A-Z0-9]+)'
            ],
            'seat': [
                r'SEAT\s*:?([A-Z0-9]+)',
                r'SEAT\s*([A-Z0-9]+)',
                r'([A-Z]\d+[A-Z]?)'
            ],
            'terminal': [
                r'TERMINAL\s*:?([A-Z0-9]+)',
                r'TERMINAL\s*([A-Z0-9]+)',
                r'T([A-Z0-9]+)'
            ],
            'boarding_time': [
                r'BOARDING\s*TIME\s*:?(\d{1,2}:\d{2})',
                r'BOARDING\s*:?(\d{1,2}:\d{2})',
                r'BRD\s*:?(\d{1,2}:\d{2})'
            ]
        }
    
    def preprocess_image(self, image_path: str) -> cv2.Mat:
        """
        Preprocess image for better text extraction.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed OpenCV image
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Noise removal
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Resize for better processing
            height, width = cleaned.shape
            if height < 500:
                scale_factor = 500 / height
                new_width = int(width * scale_factor)
                cleaned = cv2.resize(cleaned, (new_width, 500), interpolation=cv2.INTER_CUBIC)
            
            logger.debug(f"Image preprocessed: {width}x{height} -> {cleaned.shape[1]}x{cleaned.shape[0]}")
            return cleaned
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise
    
    def extract_text_basic(self, image_path: str) -> str:
        """
        Extract text using basic OCR approach.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as string
        """
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Use PIL for basic text extraction (without pytesseract for now)
            # This is a placeholder - in production, you'd use pytesseract or similar
            # For now, we'll simulate text extraction
            
            # Convert to PIL Image
            pil_img = Image.fromarray(processed_img)
            
            # Basic text extraction simulation
            # In a real implementation, you would use pytesseract here
            # For demo purposes, we'll return a template
            text = """
            PASSENGER NAME: DEMO PASSENGER
            FLIGHT NO: AI 123
            FROM: BOM TO: DEL
            DATE: 15 MAY 2024
            TIME: 14:30
            GATE: A12
            SEAT: 23A
            TERMINAL: 2
            BOARDING TIME: 13:45
            """
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.info(f"Basic text extraction completed")
            return text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise
    
    def extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract specific field from text using regex patterns.
        
        Args:
            text: Extracted text
            field_name: Name of the field to extract
            
        Returns:
            Extracted field value or None
        """
        if field_name not in self.patterns:
            logger.warning(f"Unknown field: {field_name}")
            return None
        
        patterns = self.patterns[field_name]
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if field_name == 'from_to' and len(match.groups()) == 2:
                        return f"{match.group(1)} → {match.group(2)}"
                    elif match.groups():
                        return match.group(1).strip()
                    else:
                        return match.group(0).strip()
            except Exception as e:
                logger.debug(f"Pattern failed for {field_name}: {e}")
                continue
        
        return None
    
    def extract_boarding_pass_info(self, image_path: str) -> Dict[str, any]:
        """
        Extract boarding pass information from image.
        
        Args:
            image_path: Path to the boarding pass image
            
        Returns:
            Dictionary with extracted boarding pass information
        """
        try:
            # Extract text from image
            extracted_text = self.extract_text_basic(image_path)
            logger.info(f"Text extracted: {extracted_text[:200]}...")
            
            # Extract structured information
            extracted_info = {
                'raw_text': extracted_text,
                'flight_number': self.extract_field(extracted_text, 'flight_number'),
                'passenger_name': self.extract_field(extracted_text, 'passenger_name'),
                'from_to': self.extract_field(extracted_text, 'from_to'),
                'date': self.extract_field(extracted_text, 'date'),
                'departure_time': self.extract_field(extracted_text, 'time'),
                'gate': self.extract_field(extracted_text, 'gate'),
                'seat': self.extract_field(extracted_text, 'seat'),
                'terminal': self.extract_field(extracted_text, 'terminal'),
                'boarding_time': self.extract_field(extracted_text, 'boarding_time'),
                'timestamp': datetime.now().isoformat(),
                'confidence': self._calculate_confidence(extracted_info),
                'method': 'basic_ocr_simulation'
            }
            
            # Clean up extracted data
            extracted_info = self._clean_extracted_data(extracted_info)
            
            logger.info(f"Boarding pass processed: {extracted_info.get('flight_number', 'Unknown')}")
            return extracted_info
            
        except Exception as e:
            logger.error(f"Boarding pass extraction failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.0,
                'method': 'basic_ocr_simulation'
            }
    
    def _calculate_confidence(self, extracted_info: Dict[str, any]) -> float:
        """Calculate confidence score based on extracted fields."""
        essential_fields = ['flight_number', 'passenger_name', 'from_to', 'date']
        extracted_count = sum(1 for field in essential_fields if extracted_info.get(field))
        return (extracted_count / len(essential_fields)) * 100
    
    def _clean_extracted_data(self, data: Dict[str, any]) -> Dict[str, any]:
        """Clean and format extracted data."""
        cleaned = {}
        
        for key, value in data.items():
            if key in ['raw_text', 'timestamp', 'confidence', 'method']:
                cleaned[key] = value
            elif value and isinstance(value, str):
                # Clean up extracted values
                cleaned_value = re.sub(r'\s+', ' ', value.strip())
                # Remove common artifacts
                cleaned_value = re.sub(r'[^\w\s\-\>\/]', '', cleaned_value)
                if cleaned_value:
                    cleaned[key] = cleaned_value
        
        return cleaned

# Global instance
simple_boarding_pass_ocr = SimpleBoardingPassOCR()

def extract_boarding_pass_simple(image_path: str) -> Dict[str, any]:
    """
    Convenience function to extract boarding pass information using simple OCR.
    
    Args:
        image_path: Path to the boarding pass image
        
    Returns:
        Extracted boarding pass information
    """
    return simple_boarding_pass_ocr.extract_boarding_pass_info(image_path)

# --- Test Cases ---
def _test_simple_ocr():
    """Test the simple OCR service."""
    test_text = """
    PASSENGER NAME: JOHN DOE
    FLIGHT NO: AI 123
    FROM: BOM TO: DEL
    DATE: 15 MAY 2024
    TIME: 14:30
    GATE: A12
    SEAT: 23A
    TERMINAL: 2
    BOARDING TIME: 13:45
    """
    
    ocr = SimpleBoardingPassOCR()
    
    # Test field extraction
    flight = ocr.extract_field(test_text, 'flight_number')
    name = ocr.extract_field(test_text, 'passenger_name')
    from_to = ocr.extract_field(test_text, 'from_to')
    
    print("=== Simple OCR Service Test ===")
    print(f"Flight: {flight}")
    print(f"Name: {name}")
    print(f"Route: {from_to}")

if __name__ == "__main__":
    _test_simple_ocr()
