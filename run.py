#!/usr/bin/env python3
"""
NBABot v11.0 — Entry Point

Run this file to start the bot:
    python run.py
"""

import sys
import os
import asyncio

# Debug hook (safe, optional)
print("🚨 run.py ENTRY HIT")

# Add src directory to PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from bot import main  # noqa: E402


if __name__ == "__main__":
    asyncio.run(main())
