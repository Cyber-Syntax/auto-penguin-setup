#!/usr/bin/env python3
"""Entry point script for auto-penguin-setup development."""

import sys
from pathlib import Path

# Add the src directory to Python path for development
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and run the main function
from aps.main import main

if __name__ == "__main__":
    main()
