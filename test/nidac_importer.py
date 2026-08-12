import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nidac import Nidac

__all__ = ["Nidac"]
