#!/usr/bin/env python3
from pathlib import Path
import os
import sys

runner = Path(__file__).resolve().parents[1] / ".agents/tools/paper-harness.py"
os.execv(sys.executable, [sys.executable, str(runner), "paper_populated"])
