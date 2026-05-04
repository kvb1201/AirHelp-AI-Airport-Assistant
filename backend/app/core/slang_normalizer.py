"""
Airport Slang Normalizer
Cleans and normalizes Hindi/Hinglish slang and common airport terms
"""

import re
from typing import Dict, List
from rapidfuzz import process, fuzz
from app.utils.logger import logger

# Comprehensive Airport Slang & Common Hinglish Terms
AIRPORT_SLANG_MAP = {
    # Directional & Locational (Hinglish/Gujarati)
    "kahan hai": "where is", "kidhar hai": "where is", "kyan che": "where is",
    "kahan": "where", "kidhar": "where", "kyan": "what",
    "idhar": "here", "udhar": "there", "baaju mein": "next to",
    "paas mein": "nearby", "door": "far", "saamne": "in front",
    
    # Facilities & Services
    "vashroom": "washroom", "shauchalay": "toilet", "baathroom": "restroom",
    "bathroom": "restroom", "toilet": "washroom", "washroom": "washroom",
    "paani": "water", "peene ka paani": "drinking water", "pani": "water",
    "paisa": "currency exchange", "atm machine": "atm", "atm": "atm",
    "chargar": "charging station", "plug": "power outlet", "charging": "charging station",
    "wifi password": "internet access", "wifi": "internet", "shanti room": "prayer room",
    "prayer room": "prayer room",
    
    # Travel & Logistics
    "samaan": "baggage", "beg": "bag", "peti": "suitcase",
    "gadi": "trolley", "reha": "trolley", "pahiya wala": "trolley",
    "trolley": "trolley", "luggage": "baggage", "baggage": "baggage",
    "boarding pas": "boarding pass", "tikkat": "ticket", "ticket": "ticket",
    "line": "queue", "bheed": "crowd", "deri": "delay",
    "checking": "security check", "counter": "desk", "check in counter": "check-in desk",
    "security check": "security checkpoint", "checkpoint": "security checkpoint",
    
    # Food & Shopping
    "bhook": "food/restaurant", "bhookh": "hungry", "khana": "food", "nasta": "snacks",
    "nasta": "breakfast", "breakfast": "breakfast", "chai": "tea", "coffee": "cafe",
    "chai": "tea", "tea": "tea", "daru": "liquor shop", "duti fri": "duty free",
    "duty free": "duty free", "tappu": "gift shop", "sasta": "cheap/discount",
    "offer": "rewards", "dukan": "store", "shop": "store", "restaurant": "restaurant",
    
    # Emergency & Assistance
    "madad": "help", "sahayta": "assistance", "tabiyat": "medical emergency",
    "kho gaya": "lost", "mil nahi raha": "cannot find", "help": "help",
    "emergency": "emergency", "medical": "medical", "doctor": "doctor",
    
    # Common Questions & Phrases
    "hello": "hello", "namaste": "hello", "hi": "hi", "hey": "hi",
    "thank you": "thank you", "dhanyavad": "thank you", "thanks": "thanks",
    "please": "please", "kripya": "please", "excuse me": "excuse me",
    "sorry": "sorry", "maaf": "sorry", "good morning": "good morning",
    "good evening": "good evening", "bye": "bye", "alvida": "goodbye",
    
    # Airport Specific
    "gate": "gate", "gate number": "gate number", "terminal": "terminal",
    "terminal 1": "terminal 1", "terminal 2": "terminal 2", "flight": "flight",
    "flight status": "flight status", "departure": "departure", "arrival": "arrival",
    "boarding": "boarding", "boarding time": "boarding time", "delayed": "delayed",
    "on time": "on time", "cancelled": "cancelled", "check in": "check in",
    
    # Transportation
    "taxi": "taxi", "cab": "taxi", "uber": "uber", "bus": "bus",
    "train": "train", "metro": "metro", "parking": "parking",
    "pickup": "pickup", "drop": "drop", "shuttle": "shuttle",
    "airport shuttle": "airport shuttle"
}

class SlangNormalizer:
    """Normalizes Hindi/Hinglish slang and common airport terms."""
    
    def __init__(self):
        self.slang_map = AIRPORT_SLANG_MAP
        logger.info("🔤 Slang Normalizer initialized with {} mappings".format(len(self.slang_map)))
    
    def is_hinglish_input(self, text: str) -> bool:
        """
        Detect if input is likely Hinglish/Hindi mixed.
        """
        hinglish_indicators = [
            'hai', 'hain', 'kahan', 'kidhar', 'kyan', 'mujhe', 'aapko', 
            'samaan', 'khana', 'paani', 'madad', 'kho', 'mil',
            'bhook', 'nasta', 'chai', 'duti', 'vashroom', 'gate'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in hinglish_indicators)
    
    def clean_slang(self, user_input: str) -> str:
        """
        Cleans messy input and maps common slang to standardized English terms.
        
        Args:
            user_input: Raw user input (text or transcribed speech)
            
        Returns:
            Cleaned, standardized English text
        """
        if not user_input or not user_input.strip():
            return user_input
            
        # 1. Lowercase and strip extra whitespace
        text = user_input.lower().strip()
        
        # 2. Basic regex cleaning (remove extra special chars, normalize spaces)
        text = re.sub(r'[^\w\s]', ' ', text)  # Replace non-word chars with space
        text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
        
        # 3. Direct phrase matching (for multi-word slang)
        cleaned_text = text
        for slang_phrase, standard_phrase in self.slang_map.items():
            if ' ' in slang_phrase:  # Multi-word phrase
                cleaned_text = cleaned_text.replace(slang_phrase, standard_phrase)
        
        # 4. Word-by-word processing with fuzzy matching
        words = cleaned_text.split()
        cleaned_words = []
        
        for word in words:
            # Check for direct slang match
            if word in self.slang_map:
                cleaned_words.append(self.slang_map[word])
                logger.debug(f"Direct slang match: '{word}' -> '{self.slang_map[word]}'")
            else:
                # Fuzzy matching for typos (e.g., 'securty' -> 'security')
                match = process.extractOne(word, self.slang_map.keys(), scorer=fuzz.ratio)
                if match and match[1] > 85:  # High confidence threshold
                    cleaned_words.append(self.slang_map[match[0]])
                    logger.debug(f"Fuzzy slang match: '{word}' -> '{self.slang_map[match[0]]}' (confidence: {match[1]:.1f})")
                else:
                    cleaned_words.append(word)
        
        result = " ".join(cleaned_words)
        
        # 5. Final cleanup
        result = re.sub(r'\s+', ' ', result).strip()
        
        if result != user_input.lower():
            logger.info(f"🔤 Slang normalized: '{user_input}' -> '{result}'")
        
        return result
    
    def process_input(self, user_input: str, is_hinglish: bool = None) -> Dict[str, str]:
        """
        Process input and return normalized result with metadata.
        
        Args:
            user_input: Raw user input
            is_hinglish: Optional hint if input is known to be Hinglish
            
        Returns:
            Dictionary with cleaned text and processing metadata
        """
        if not user_input or not user_input.strip():
            return {
                "original": user_input,
                "cleaned": user_input,
                "detected_hinglish": False,
                "slang_found": False
            }
        
        # Auto-detect Hinglish if not provided
        if is_hinglish is None:
            is_hinglish = self.is_hinglish_input(user_input)
        
        # Only process slang if Hinglish detected
        if is_hinglish:
            cleaned_text = self.clean_slang(user_input)
            slang_found = cleaned_text != user_input.lower()
        else:
            cleaned_text = user_input
            slang_found = False
        
        return {
            "original": user_input,
            "cleaned": cleaned_text,
            "detected_hinglish": is_hinglish,
            "slang_found": slang_found
        }

# Global instance
slang_normalizer = SlangNormalizer()

def clean_airport_slang(user_input: str, is_hinglish: bool = None) -> str:
    """
    Convenience function to clean airport slang from user input.
    
    Args:
        user_input: User input text
        is_hinglish: Optional hint if input is Hinglish
        
    Returns:
        Cleaned text
    """
    result = slang_normalizer.process_input(user_input, is_hinglish)
    return result["cleaned"]

# --- Test Cases ---
def _run_tests():
    """Run internal tests for slang normalization."""
    test_queries = [
        "Security line kahan hai?",
        "Mujhe bhook lagi hai, nasta kidhar milega?",
        "Duti fri shop kidhar hai?",
        "Samaan kahan checkin karein?",
        "Vashroom kahan hai?",
        "Gate 42 ka flight kab hai?",
        "Terminal 2 mein chai milega?",
        "Mujhe atm chahiye",
        "Boarding pass kahan milega?"
    ]
    
    print("=== Slang Normalization Tests ===")
    for query in test_queries:
        result = slang_normalizer.process_input(query)
        print(f"Original: {query}")
        print(f"Cleaned:  {result['cleaned']}")
        print(f"Hinglish: {result['detected_hinglish']}, Slang: {result['slang_found']}")
        print("---")

if __name__ == "__main__":
    _run_tests()
