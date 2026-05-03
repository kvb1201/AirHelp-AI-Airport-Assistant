# Documentation Index

## 📚 Navigation System Documentation

### Getting Started
- **`README_NAVIGATION.md`** - Main overview and quick reference
- **`QUICK_START.md`** - Step-by-step setup and usage guide

### Detailed Documentation
- **`docs/turn_by_turn_navigation.md`** - Complete system documentation
- **`docs/api_examples.md`** - API endpoint examples and usage patterns
- **`docs/DISTANCE_CALIBRATION.md`** - Distance calibration guide and process

### Testing
- **`backend/test_turn_by_turn.py`** - Test suite for all navigation features

---

## 📖 Reading Order

### For Quick Setup
1. `README_NAVIGATION.md` - Overview
2. `QUICK_START.md` - Get it running
3. Test with API calls

### For Development
1. `docs/turn_by_turn_navigation.md` - Understand the system
2. `docs/api_examples.md` - Learn the API
3. Review code in `backend/app/services/`

### For Production Deployment
1. `docs/DISTANCE_CALIBRATION.md` - Calibrate distances
2. Run full test suite
3. Validate with real user walks

---

## 🗂️ File Structure

```
.
├── README_NAVIGATION.md          # Main navigation docs
├── QUICK_START.md                # Quick start guide
│
├── docs/
│   ├── turn_by_turn_navigation.md    # Complete system docs
│   ├── api_examples.md               # API usage examples
│   └── DISTANCE_CALIBRATION.md       # Calibration guide
│
└── backend/
    ├── test_turn_by_turn.py          # Test suite
    │
    └── app/services/
        ├── distance_calculator.py     # Distance/bearing math
        ├── turn_by_turn.py           # Direction generation
        └── navigation_knowledge.py    # Knowledge base integration
```

---

## 🎯 Quick Links

**Start Here:** `README_NAVIGATION.md`  
**API Reference:** `docs/api_examples.md`  
**Calibration:** `docs/DISTANCE_CALIBRATION.md`  
**Testing:** `backend/test_turn_by_turn.py`
