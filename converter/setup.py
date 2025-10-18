"""
Installation and Setup Script for Fallout 4 to Black Ops 3 Converter

This script helps automate the setup process.
Run this AFTER installing Python 3.10+
"""

import subprocess
import sys
import os


def main():
    print("="*60)
    print("  Fallout 4 → Black Ops 3 Converter - Setup")
    print("="*60)
    print()
    
    # Check Python version
    print("✓ Checking Python version...")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  ❌ Python 3.10 or higher is required!")
        print("  Download from: https://www.python.org/downloads/")
        return 1
    
    print("  ✓ Python version OK\n")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    print("  This may take a few minutes...\n")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("\n✓ Dependencies installed successfully!\n")
    except subprocess.CalledProcessError:
        print("\n❌ Failed to install dependencies")
        print("   Try manually: pip install -r requirements.txt")
        return 1
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    print("✓ Output directory created\n")
    
    # Final message
    print("="*60)
    print("  🎉 Setup Complete!")
    print("="*60)
    print()
    print("To start the converter, run:")
    print("  python main.py")
    print()
    print("For more information:")
    print("  Read QUICKSTART.md")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
