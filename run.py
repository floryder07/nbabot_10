#!/usr/bin/env python3
"""
NBABot v10.0 - Entry Point

Run this file to start the bot:
    python run.py
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bot import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
