#!/usr/bin/env python3
"""
NBABot v10.0 - Setup Verification Script

Run this to verify your environment is configured correctly:
    python verify_setup.py
"""

import sys
import os

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} - Need 3.10+")
        return False

def check_dependencies():
    """Check required packages."""
    required = ['discord', 'aiohttp', 'dotenv']
    missing = []
    
    for package in required:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            missing.append(package)
    
    return len(missing) == 0

def check_env_file():
    """Check .env file exists and has required vars."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_path):
        print("❌ .env file not found")
        print("   → Copy .env.example to .env and fill in your values")
        return False
    
    print("✅ .env file exists")
    
    # Check required variables
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    required_vars = ['DISCORD_TOKEN', 'API_BASKETBALL_KEY']
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is missing or not configured")
            missing.append(var)
    
    return len(missing) == 0

def check_src_files():
    """Check all source files exist."""
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    required_files = [
        'bot.py',
        'config.py',
        'eligibility.py',
        'api_client.py',
        'parlay_engine.py',
        'embeds.py',
        'buttons.py'
    ]
    
    missing = []
    for file in required_files:
        path = os.path.join(src_dir, file)
        if os.path.exists(path):
            print(f"✅ src/{file}")
        else:
            print(f"❌ src/{file} - Missing")
            missing.append(file)
    
    return len(missing) == 0

def main():
    print("=" * 50)
    print("🏀 NBABot v10.0 Setup Verification")
    print("=" * 50)
    
    print("\n📦 Checking Python version...")
    python_ok = check_python_version()
    
    print("\n📦 Checking dependencies...")
    deps_ok = check_dependencies()
    
    print("\n📄 Checking source files...")
    files_ok = check_src_files()
    
    print("\n🔐 Checking environment...")
    env_ok = check_env_file()
    
    print("\n" + "=" * 50)
    
    if python_ok and deps_ok and files_ok and env_ok:
        print("✅ All checks passed! Ready to run:")
        print("   python run.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        if not deps_ok:
            print("\n💡 Install dependencies:")
            print("   pip install -r requirements.txt")
        if not env_ok:
            print("\n💡 Configure environment:")
            print("   cp .env.example .env")
            print("   # Edit .env with your tokens")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
