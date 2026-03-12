#!/usr/bin/env python3
"""
Check identify_risks return structure
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence

pi = PortfolioIntelligence()

risks = pi.identify_risks()
print(f"Type: {type(risks)}")
print(f"Keys: {risks.keys()}")
print(f"\nFull output:")
import json
print(json.dumps(risks, indent=2, default=str))