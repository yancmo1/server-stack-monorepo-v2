import sys
from pathlib import Path
# Add project root so that 'app' package is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
