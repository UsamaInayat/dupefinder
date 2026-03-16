"""
Embeddings Package — DupeFinder ML Engine

Provides FashionCLIPExtractor for 512-dim fashion-aware embeddings.
The actual extractor lives in ml-engine/fashionclip/extractor.py;
this shim keeps existing imports working.
"""

import sys
from pathlib import Path

# Ensure fashionclip package is importable when using this shim
_FASHIONCLIP_PKG = Path(__file__).parent.parent / "fashionclip"
if str(_FASHIONCLIP_PKG.parent) not in sys.path:
    sys.path.insert(0, str(_FASHIONCLIP_PKG.parent))

from fashionclip.extractor import FashionCLIPExtractor

__all__ = ["FashionCLIPExtractor"]
