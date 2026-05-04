"""
Boarding Pass OCR Service
Extracts structured information from boarding pass images using OCR
"""

import cv2
import pytesseract
import re
from PIL import Image
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.utils.logger import logger

class BoardingPassOCR:
    """OCR service for extracting boarding pass information."""
    
    def __init__(self):
        logger.info("📷 Boarding Pass OCR Service initialized")
        
        # Common boarding pass patterns
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
        Preprocess image for better OCR accuracy.
        
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
            
            # Apply adaptive thresholding for better text detection
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Noise removal
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Resize for better OCR (scale up if too small)
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
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as string
        """
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Extract text using Tesseract
            # Use custom config for better accuracy on boarding passes
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:/- '
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.info(f"OCR extracted {len(text)} characters from image")
            return text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract specific field from OCR text using regex patterns.
        
        Args:
            text: OCR extracted text
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
                    # Handle different capture group scenarios
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
        Extract complete boarding pass information from image.
        
        Args:
            image_path: Path to the boarding pass image
            
        Returns:
            Dictionary with extracted boarding pass information
        """
        try:
            # Extract text from image
            ocr_text = self.extract_text(image_path)
            logger.info(f"OCR Text: {ocr_text[:200]}...")
            
            # Extract structured information
            extracted_info = {
                'raw_text': ocr_text,
                'flight_number': self.extract_field(ocr_text, 'flight_number'),
                'passenger_name': self.extract_field(ocr_text, 'passenger_name'),
                'from_to': self.extract_field(ocr_text, 'from_to'),
                'date': self.extract_field(ocr_text, 'date'),
                'departure_time': self.extract_field(ocr_text, 'time'),
                'gate': self.extract_field(ocr_text, 'gate'),
                'seat': self.extract_field(ocr_text, 'seat'),
                'terminal': self.extract_field(ocr_text, 'terminal'),
                'boarding_time': self.extract_field(ocr_text, 'boarding_time'),
                'timestamp': datetime.now().isoformat(),
                'confidence': self._calculate_confidence(extracted_info)
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
                'confidence': 0.0
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
            if key == 'raw_text' or key == 'timestamp' or key == 'confidence':
                cleaned[key] = value
            elif value and isinstance(value, str):
                # Clean up extracted values
                cleaned_value = re.sub(r'\s+', ' ', value.strip())
                # Remove common OCR artifacts
                cleaned_value = re.sub(r'[^\w\s\-\>\/]', '', cleaned_value)
                if cleaned_value:
                    cleaned[key] = cleaned_value
        
        return cleaned
    
    def process_multiple_images(self, image_paths: List[str]) -> List[Dict[str, any]]:
        """
        Process multiple boarding pass images.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of extracted boarding pass information
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
                result = self.extract_boarding_pass_info(image_path)
                result['image_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process image {i+1}: {e}")
                results.append({
                    'error': str(e),
                    'image_index': i,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 0.0
                })
        
        return results

# Global instance
boarding_pass_ocr = BoardingPassOCR()

def extract_boarding_pass(image_path: str) -> Dict[str, any]:
    """
    Convenience function to extract boarding pass information.
    
    Args:
        image_path: Path to the boarding pass image
        
    Returns:
        Extracted boarding pass information
    """
    return boarding_pass_ocr.extract_boarding_pass_info(image_path)

# --- Test Cases ---
def _test_ocr_service():
    """Test the OCR service with sample data."""
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
    
    ocr = BoardingPassOCR()
    
    # Test field extraction
    flight = ocr.extract_field(test_text, 'flight_number')
    name = ocr.extract_field(test_text, 'passenger_name')
    from_to = ocr.extract_field(test_text, 'from_to')
    
    print("=== OCR Service Test ===")
    print(f"Flight: {flight}")
    print(f"Name: {name}")
    print(f"Route: {from_to}")

if __name__ == "__main__":
    _test_ocr_service()
